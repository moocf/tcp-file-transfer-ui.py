"""
FT-Echo TCP Server
Implements the FT-Echo protocol for file transfer operations.
Protocol: 4-byte big-endian length (N) + 1-byte message type + (N-1) bytes payload
"""
import asyncio
import hashlib
import json
import logging
import os
import struct
from datetime import datetime
from pathlib import Path

# Configure logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_PORT = 9000
CHUNK_SIZE = 4096
STORAGE_DIR = Path(__file__).parent.parent / "storage"
STORAGE_DIR.mkdir(exist_ok=True)


class FTEchoServer:
    """FT-Echo Protocol Server"""
    
    def __init__(self, port=DEFAULT_PORT, storage_dir=STORAGE_DIR):
        self.port = port
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True)
    
    async def recv_exact(self, reader: asyncio.StreamReader, n: int) -> bytes:
        """Read exactly n bytes from the stream"""
        data = b''
        while len(data) < n:
            chunk = await reader.read(n - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data
    
    async def send_message(self, writer: asyncio.StreamWriter, msg_type: str, payload: bytes = b''):
        """Send a message: 4-byte length + 1-byte type + payload"""
        length = len(payload) + 1
        msg = struct.pack('>I', length) + msg_type.encode('ascii') + payload
        writer.write(msg)
        await writer.drain()
        logger.debug(f"Sent: type={msg_type}, length={length}")
    
    async def recv_message(self, reader: asyncio.StreamReader) -> tuple[str, bytes]:
        """Receive a message: returns (msg_type, payload)"""
        # Read length (4 bytes)
        length_bytes = await self.recv_exact(reader, 4)
        length = struct.unpack('>I', length_bytes)[0]
        
        if length < 1:
            raise ValueError(f"Invalid message length: {length}")
        
        # Read message type (1 byte)
        msg_type_bytes = await self.recv_exact(reader, 1)
        msg_type = msg_type_bytes.decode('ascii')
        
        # Read payload (length - 1 bytes)
        payload = b''
        if length > 1:
            payload = await self.recv_exact(reader, length - 1)
        
        logger.debug(f"Received: type={msg_type}, length={length}")
        return msg_type, payload
    
    async def handle_list(self, writer: asyncio.StreamWriter):
        """Handle LIST (L) command"""
        logger.info("Handling LIST command")
        files = []
        for file_path in self.storage_dir.iterdir():
            if file_path.is_file() and not file_path.name.endswith('.part'):
                size = file_path.stat().st_size
                files.append(f"{file_path.name}|{size}")
        
        listing = '\n'.join(files) + '\n'
        await self.send_message(writer, 'O', listing.encode('utf-8'))
        logger.info(f"Listed {len(files)} files")
    
    async def handle_get(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, filename: str):
        """Handle GET (G) command"""
        logger.info(f"Handling GET command for file: {filename}")
        file_path = self.storage_dir / filename
        
        if not file_path.exists() or not file_path.is_file():
            error_msg = f"File not found: {filename}"
            await self.send_message(writer, 'E', error_msg.encode('utf-8'))
            logger.warning(error_msg)
            return
        
        file_size = file_path.stat().st_size
        metadata = json.dumps({"size": file_size}).encode('utf-8')
        await self.send_message(writer, 'O', metadata)
        
        # Stream file in chunks
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                sha256.update(chunk)
                await self.send_message(writer, 'F', chunk)
        
        # Send SHA256 checksum
        checksum = sha256.hexdigest()
        await self.send_message(writer, 'S', checksum.encode('utf-8'))
        logger.info(f"GET completed: {filename}, size={file_size}, sha={checksum}")
    
    async def handle_get_resume(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, 
                                filename: str, offset: int):
        """Handle GET RESUME (R) command for downloading"""
        logger.info(f"Handling GET RESUME for file: {filename}, offset: {offset}")
        file_path = self.storage_dir / filename
        
        if not file_path.exists() or not file_path.is_file():
            error_msg = f"File not found: {filename}"
            await self.send_message(writer, 'E', error_msg.encode('utf-8'))
            return
        
        file_size = file_path.stat().st_size
        if offset >= file_size:
            error_msg = f"Offset {offset} exceeds file size {file_size}"
            await self.send_message(writer, 'E', error_msg.encode('utf-8'))
            return
        
        metadata = json.dumps({"size": file_size, "offset": offset}).encode('utf-8')
        await self.send_message(writer, 'O', metadata)
        
        # Stream file from offset
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            f.seek(offset)
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                sha256.update(chunk)
                await self.send_message(writer, 'F', chunk)
        
        checksum = sha256.hexdigest()
        await self.send_message(writer, 'S', checksum.encode('utf-8'))
        logger.info(f"GET RESUME completed: {filename}, offset={offset}, sha={checksum}")
    
    async def handle_put(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, 
                        metadata_payload: bytes):
        """Handle PUT (P) command"""
        # Parse metadata (format: "filename|size" or JSON)
        try:
            metadata_str = metadata_payload.decode('utf-8')
            if '|' in metadata_str:
                filename, size_str = metadata_str.split('|', 1)
                file_size = int(size_str)
            else:
                metadata = json.loads(metadata_str)
                filename = metadata['filename']
                file_size = metadata['size']
        except (ValueError, json.JSONDecodeError) as e:
            error_msg = f"Invalid metadata: {e}"
            await self.send_message(writer, 'E', error_msg.encode('utf-8'))
            return
        
        logger.info(f"Handling PUT command for file: {filename}, size: {file_size}")
        
        # Send OK to accept
        await self.send_message(writer, 'O', b'Ready to receive')
        
        # Write to temporary file first
        temp_path = self.storage_dir / f"{filename}.part"
        final_path = self.storage_dir / filename
        
        sha256 = hashlib.sha256()
        total_received = 0
        
        try:
            with open(temp_path, 'wb') as f:
                while total_received < file_size:
                    msg_type, chunk = await self.recv_message(reader)
                    if msg_type != 'F':
                        raise ValueError(f"Expected 'F' chunk, got '{msg_type}'")
                    f.write(chunk)
                    sha256.update(chunk)
                    total_received += len(chunk)
            
            if total_received != file_size:
                raise ValueError(f"Size mismatch: expected {file_size}, received {total_received}")
            
            # Rename temp file to final file (atomic operation)
            temp_path.rename(final_path)
            
            checksum = sha256.hexdigest()
            await self.send_message(writer, 'O', checksum.encode('utf-8'))
            logger.info(f"PUT completed: {filename}, size={file_size}, sha={checksum}")
            
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            error_msg = f"PUT failed: {str(e)}"
            await self.send_message(writer, 'E', error_msg.encode('utf-8'))
            logger.error(error_msg)
    
    async def handle_put_resume(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                                metadata_payload: bytes):
        """Handle PUT RESUME (R) command for uploading"""
        # Parse metadata: "filename|offset|put" or JSON
        try:
            metadata_str = metadata_payload.decode('utf-8')
            if '|' in metadata_str:
                parts = metadata_str.split('|')
                filename = parts[0]
                offset = int(parts[1])
            else:
                metadata = json.loads(metadata_str)
                filename = metadata['filename']
                offset = metadata['offset']
        except (ValueError, json.JSONDecodeError) as e:
            error_msg = f"Invalid metadata: {e}"
            await self.send_message(writer, 'E', error_msg.encode('utf-8'))
            return
        
        logger.info(f"Handling PUT RESUME for file: {filename}, offset: {offset}")
        
        temp_path = self.storage_dir / f"{filename}.part"
        final_path = self.storage_dir / filename
        
        # Check if temp file exists
        if not temp_path.exists():
            error_msg = f"No partial file found for resume: {filename}"
            await self.send_message(writer, 'E', error_msg.encode('utf-8'))
            return
        
        current_size = temp_path.stat().st_size
        if offset != current_size:
            error_msg = f"Offset mismatch: expected {current_size}, got {offset}"
            await self.send_message(writer, 'E', error_msg.encode('utf-8'))
            return
        
        # Get total file size from original PUT metadata if available, or estimate
        # For now, we'll continue until we receive the S message
        await self.send_message(writer, 'O', json.dumps({"offset": offset, "ready": True}).encode('utf-8'))
        
        # Read existing file to compute SHA256 so far
        sha256 = hashlib.sha256()
        with open(temp_path, 'rb') as f:
            existing_data = f.read()
            sha256.update(existing_data)
        
        total_received = current_size
        
        try:
            with open(temp_path, 'ab') as f:
                while True:
                    msg_type, chunk = await self.recv_message(reader)
                    if msg_type == 'S':
                        # Received final checksum from client
                        client_checksum = chunk.decode('utf-8')
                        break
                    elif msg_type == 'F':
                        f.write(chunk)
                        sha256.update(chunk)
                        total_received += len(chunk)
                    else:
                        raise ValueError(f"Unexpected message type: {msg_type}")
            
            # Verify checksum
            server_checksum = sha256.hexdigest()
            if server_checksum == client_checksum:
                temp_path.rename(final_path)
                await self.send_message(writer, 'O', server_checksum.encode('utf-8'))
                logger.info(f"PUT RESUME completed: {filename}, total_size={total_received}, sha={server_checksum}")
            else:
                raise ValueError(f"Checksum mismatch: server={server_checksum}, client={client_checksum}")
                
        except Exception as e:
            error_msg = f"PUT RESUME failed: {str(e)}"
            await self.send_message(writer, 'E', error_msg.encode('utf-8'))
            logger.error(error_msg)
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a client connection"""
        client_addr = writer.get_extra_info('peername')
        logger.info(f"Client connected: {client_addr}")
        
        try:
            while True:
                msg_type, payload = await self.recv_message(reader)
                
                if msg_type == 'Q':
                    logger.info(f"Client {client_addr} requested QUIT")
                    await self.send_message(writer, 'O', b'Goodbye')
                    break
                
                elif msg_type == 'L':
                    await self.handle_list(writer)
                
                elif msg_type == 'G':
                    filename = payload.decode('utf-8').strip()
                    await self.handle_get(reader, writer, filename)
                
                elif msg_type == 'P':
                    await self.handle_put(reader, writer, payload)
                
                elif msg_type == 'R':
                    # RESUME command: payload format "filename|offset|direction" or JSON
                    try:
                        resume_str = payload.decode('utf-8')
                        if '|' in resume_str:
                            parts = resume_str.split('|')
                            filename = parts[0]
                            offset = int(parts[1])
                            direction = parts[2] if len(parts) > 2 else 'get'
                        else:
                            resume_data = json.loads(resume_str)
                            filename = resume_data['filename']
                            offset = resume_data['offset']
                            direction = resume_data.get('direction', 'get')
                        
                        if direction == 'get':
                            await self.handle_get_resume(reader, writer, filename, offset)
                        elif direction == 'put':
                            await self.handle_put_resume(reader, writer, payload)
                        else:
                            await self.send_message(writer, 'E', f"Invalid direction: {direction}".encode('utf-8'))
                    except (ValueError, json.JSONDecodeError) as e:
                        await self.send_message(writer, 'E', f"Invalid RESUME format: {e}".encode('utf-8'))
                
                elif msg_type == 'S':
                    # Checksum message - this should only come from client during PUT operations
                    # If we receive it here, it's likely a protocol error
                    logger.warning(f"Received unexpected checksum message from {client_addr}")
                    await self.send_message(writer, 'E', b'Unexpected checksum message')
                
                else:
                    error_msg = f"Unknown message type: {msg_type}"
                    await self.send_message(writer, 'E', error_msg.encode('utf-8'))
                    logger.warning(f"Unknown message type from {client_addr}: {msg_type}")
        
        except ConnectionError as e:
            logger.info(f"Client {client_addr} disconnected: {e}")
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}", exc_info=True)
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info(f"Client {client_addr} connection closed")
    
    async def run(self):
        """Start the server"""
        server = await asyncio.start_server(
            self.handle_client,
            '0.0.0.0',
            self.port
        )
        addr = server.sockets[0].getsockname()
        logger.info(f"FT-Echo server listening on {addr}")
        
        async with server:
            await server.serve_forever()


def main():
    """Main entry point"""
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    server = FTEchoServer(port=port)
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")


if __name__ == '__main__':
    main()

