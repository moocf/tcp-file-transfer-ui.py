"""
FT-Echo TCP Client Library
Synchronous client library for FT-Echo protocol operations.
"""
import hashlib
import json
import socket
import struct
from pathlib import Path
from typing import Optional

CHUNK_SIZE = 4096


class FTEchoClient:
    """FT-Echo Protocol Client"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
    
    def connect(self):
        """Connect to the server"""
        if self.sock:
            self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
    
    def close(self):
        """Close the connection"""
        if self.sock:
            self.sock.close()
            self.sock = None
    
    def recv_exact(self, n: int) -> bytes:
        """Read exactly n bytes from the socket"""
        data = b''
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data
    
    def send_message(self, msg_type: str, payload: bytes = b''):
        """Send a message: 4-byte length + 1-byte type + payload"""
        length = len(payload) + 1
        msg = struct.pack('>I', length) + msg_type.encode('ascii') + payload
        self.sock.sendall(msg)
    
    def recv_message(self) -> tuple[str, bytes]:
        """Receive a message: returns (msg_type, payload)"""
        # Read length (4 bytes)
        length_bytes = self.recv_exact(4)
        length = struct.unpack('>I', length_bytes)[0]
        
        if length < 1:
            raise ValueError(f"Invalid message length: {length}")
        
        # Read message type (1 byte)
        msg_type_bytes = self.recv_exact(1)
        msg_type = msg_type_bytes.decode('ascii')
        
        # Read payload (length - 1 bytes)
        payload = b''
        if length > 1:
            payload = self.recv_exact(length - 1)
        
        return msg_type, payload
    
    def list_files(self) -> list[dict]:
        """List files on the server. Returns list of {name, size} dicts."""
        if not self.sock:
            self.connect()
        
        self.send_message('L', b'')
        msg_type, payload = self.recv_message()
        
        if msg_type == 'E':
            error_msg = payload.decode('utf-8')
            raise Exception(f"Server error: {error_msg}")
        elif msg_type != 'O':
            raise Exception(f"Unexpected response: {msg_type}")
        
        listing = payload.decode('utf-8').strip()
        files = []
        for line in listing.split('\n'):
            if line and '|' in line:
                name, size_str = line.split('|', 1)
                files.append({'name': name, 'size': int(size_str)})
        
        return files
    
    def get_file(self, filename: str, dest_path: str, resume: bool = False, offset: int = 0) -> dict:
        """
        Get a file from the server.
        Returns: {'ok': True, 'sha': hex_digest}
        """
        if not self.sock:
            self.connect()
        
        if resume:
            # Send RESUME command
            resume_data = f"{filename}|{offset}|get"
            self.send_message('R', resume_data.encode('utf-8'))
        else:
            # Send GET command
            self.send_message('G', filename.encode('utf-8'))
        
        # Receive response
        msg_type, payload = self.recv_message()
        
        if msg_type == 'E':
            error_msg = payload.decode('utf-8')
            raise Exception(f"Server error: {error_msg}")
        elif msg_type != 'O':
            raise Exception(f"Unexpected response: {msg_type}")
        
        # Parse metadata
        try:
            metadata = json.loads(payload.decode('utf-8'))
            file_size = metadata.get('size', 0)
            resume_offset = metadata.get('offset', 0)
        except json.JSONDecodeError:
            # Fallback: assume payload is just size info
            file_size = 0
            resume_offset = 0
        
        # Open file for writing
        mode = 'ab' if resume else 'wb'
        sha256 = hashlib.sha256()
        total_received = resume_offset if resume else 0
        
        # If resuming, read existing file to update SHA256
        if resume and Path(dest_path).exists():
            with open(dest_path, 'rb') as existing:
                existing_data = existing.read()
                sha256.update(existing_data)
        
        with open(dest_path, mode) as f:
            # Receive file chunks
            while True:
                msg_type, chunk = self.recv_message()
                
                if msg_type == 'S':
                    # Received checksum
                    server_sha = chunk.decode('utf-8')
                    break
                elif msg_type == 'F':
                    f.write(chunk)
                    sha256.update(chunk)
                    total_received += len(chunk)
                elif msg_type == 'E':
                    error_msg = chunk.decode('utf-8')
                    raise Exception(f"Server error during transfer: {error_msg}")
                else:
                    raise Exception(f"Unexpected message type: {msg_type}")
        
        client_sha = sha256.hexdigest()
        if client_sha != server_sha:
            raise Exception(f"Checksum mismatch: client={client_sha}, server={server_sha}")
        
        return {'ok': True, 'sha': client_sha, 'size': total_received}
    
    def put_file(self, src_path: str, resume: bool = False, offset: int = 0) -> dict:
        """
        Put a file to the server.
        Returns: {'ok': True, 'sha': hex_digest}
        """
        if not self.sock:
            self.connect()
        
        src_path_obj = Path(src_path)
        if not src_path_obj.exists():
            raise FileNotFoundError(f"Source file not found: {src_path}")
        
        filename = src_path_obj.name
        file_size = src_path_obj.stat().st_size
        
        if resume:
            # Send RESUME command
            resume_data = f"{filename}|{offset}|put"
            self.send_message('R', resume_data.encode('utf-8'))
        else:
            # Send PUT command with metadata
            metadata = json.dumps({'filename': filename, 'size': file_size}).encode('utf-8')
            self.send_message('P', metadata)
        
        # Receive server response
        msg_type, payload = self.recv_message()
        
        if msg_type == 'E':
            error_msg = payload.decode('utf-8')
            raise Exception(f"Server error: {error_msg}")
        elif msg_type != 'O':
            raise Exception(f"Unexpected response: {msg_type}")
        
        # Compute SHA256 and send file
        sha256 = hashlib.sha256()
        bytes_sent = 0
        
        with open(src_path, 'rb') as f:
            if resume:
                # Skip to offset
                f.seek(offset)
                # Read existing data to update SHA256
                with open(src_path, 'rb') as full:
                    existing_data = full.read(offset)
                    sha256.update(existing_data)
            
            # Send file in chunks
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                sha256.update(chunk)
                self.send_message('F', chunk)
                bytes_sent += len(chunk)
        
        # Send checksum
        checksum = sha256.hexdigest()
        self.send_message('S', checksum.encode('utf-8'))
        
        # Receive final confirmation
        msg_type, payload = self.recv_message()
        
        if msg_type == 'E':
            error_msg = payload.decode('utf-8')
            raise Exception(f"Server error: {error_msg}")
        elif msg_type == 'O':
            server_sha = payload.decode('utf-8')
            if server_sha != checksum:
                raise Exception(f"Checksum mismatch: client={checksum}, server={server_sha}")
            return {'ok': True, 'sha': checksum, 'size': bytes_sent}
        else:
            raise Exception(f"Unexpected response: {msg_type}")
    
    def quit(self):
        """Send QUIT command and close connection"""
        if self.sock:
            try:
                self.send_message('Q', b'')
                msg_type, payload = self.recv_message()
            except:
                pass
            finally:
                self.close()


# Convenience functions
def list_files(host: str, port: int) -> list[dict]:
    """List files on the server"""
    client = FTEchoClient(host, port)
    try:
        client.connect()
        return client.list_files()
    finally:
        client.close()


def get_file(host: str, port: int, filename: str, dest_path: str, resume: bool = False) -> dict:
    """Get a file from the server"""
    client = FTEchoClient(host, port)
    try:
        client.connect()
        offset = 0
        if resume:
            # Determine offset from existing file
            dest_path_obj = Path(dest_path)
            if dest_path_obj.exists():
                offset = dest_path_obj.stat().st_size
        return client.get_file(filename, dest_path, resume=resume, offset=offset)
    finally:
        client.close()


def put_file(host: str, port: int, src_path: str, resume: bool = False) -> dict:
    """Put a file to the server"""
    client = FTEchoClient(host, port)
    try:
        client.connect()
        offset = 0
        if resume:
            # Check for partial file on server (we can't directly check, so assume 0)
            # In practice, the server should tell us the offset
            offset = 0
        return client.put_file(src_path, resume=resume, offset=offset)
    finally:
        client.close()


def resume_file(host: str, port: int, filename: str, offset: int, direction: str, 
                filepath: str = None) -> dict:
    """
    Resume a file transfer (get or put)
    For 'get': filename is server filename, filepath is local destination
    For 'put': filepath is local source file path
    """
    client = FTEchoClient(host, port)
    try:
        client.connect()
        if direction == 'get':
            if not filepath:
                filepath = filename  # Use filename as default dest
            return client.get_file(filename, filepath, resume=True, offset=offset)
        elif direction == 'put':
            if not filepath:
                raise ValueError("filepath required for PUT resume")
            return client.put_file(filepath, resume=True, offset=offset)
        else:
            raise ValueError(f"Invalid direction: {direction}")
    finally:
        client.close()

