# FT-Echo TCP File Transfer Project

A complete implementation of the FT-Echo protocol for TCP-based file transfer with support for LIST, GET, PUT, and RESUME operations. Includes a TCP server, client library, CLI client, FastAPI HTTP wrapper, and React frontend.

## Project Structure

```
ft-echo-project/
├── README.md
├── transcript.txt          # Test run transcript
├── server/
│   ├── tcp_server.py      # Async TCP FT-Echo server
│   ├── tcp_client_lib.py  # Synchronous client library
│   ├── cli_client.py      # CLI for manual testing
│   ├── fastapi_app.py     # FastAPI HTTP wrapper
│   ├── requirements.txt   # Python dependencies
│   └── logs/              # Server logs
├── frontend/
│   ├── package.json
│   └── src/               # React application
├── demo_scripts/
│   ├── run_tests.sh       # Automated test script
│   └── demo_commands.txt  # Manual test commands
└── storage/                # Server file storage
```

## FT-Echo Protocol Specification

### Message Format
Every message follows this structure:
- **4 bytes**: Big-endian uint32 length (N)
- **1 byte**: ASCII message type
- **(N-1) bytes**: Payload

### Message Types
- **L** (LIST): Request file listing
- **G** (GET): Download a file
- **P** (PUT): Upload a file
- **R** (RESUME): Resume interrupted transfer
- **Q** (QUIT): Disconnect
- **O** (OK): Success response
- **E** (ERROR): Error response
- **F** (FILE): File data chunk
- **S** (SHA256): Checksum (hex digest)

### Protocol Flow

#### LIST (L)
1. Client sends: `L` (no payload)
2. Server responds: `O` + newline-separated list (`filename|size\n`)

#### GET (G)
1. Client sends: `G` + filename (UTF-8)
2. Server responds: `O` + metadata (JSON: `{"size": N}`)
3. Server sends: Multiple `F` chunks (file data)
4. Server sends: `S` + SHA256 hex digest

#### PUT (P)
1. Client sends: `P` + metadata (JSON: `{"filename": "...", "size": N}`)
2. Server responds: `O` + "Ready to receive"
3. Client sends: Multiple `F` chunks (file data)
4. Server responds: `O` + SHA256 hex digest

#### RESUME (R)
1. Client sends: `R` + `filename|offset|direction`
2. Server verifies partial file exists
3. Transfer continues from offset
4. Same flow as GET/PUT but starting from offset

## Installation

### Prerequisites
- Python 3.10+
- Node.js 16+ and npm
- Bash (for test scripts on Unix-like systems)

### Python Dependencies
```bash
cd server
pip install -r requirements.txt
```

### React Frontend
```bash
cd frontend
npm install
```

## Usage

### 1. Start the TCP Server

**Linux/macOS:**
```bash
cd server
python3 tcp_server.py [port]
```

**Windows:**
```cmd
cd server
python tcp_server.py [port]
```

Default port: 9000

The server will:
- Listen on all interfaces (0.0.0.0)
- Store files in `../storage/` directory
- Log to `logs/server.log`

### 2. Use the CLI Client

**Linux/macOS:**
```bash
cd server
python3 cli_client.py
```

**Windows:**
```cmd
cd server
python cli_client.py
```

Interactive commands:
- `connect <host> <port>` - Connect to server
- `list` - List files on server
- `get <filename> [dest_path]` - Download a file
- `put <filepath>` - Upload a file
- `resume <file> <offset> <direction>` - Resume transfer (direction: get|put)
- `quit` - Disconnect and exit

Example:
```bash
ft-echo> connect localhost 9000
ft-echo> list
ft-echo> put ../demo_data/test.txt
ft-echo> get test.txt downloaded_test.txt
ft-echo> quit
```

### 3. Use the FastAPI HTTP Wrapper

Start the HTTP server:

**Linux/macOS:**
```bash
cd server
python3 fastapi_app.py
```

**Windows:**
```cmd
cd server
python fastapi_app.py
```

Or with uvicorn (all platforms):
```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```

API Endpoints:
- `GET /api/list` - List files
- `GET /api/get?file=<filename>` - Download file
- `POST /api/put` - Upload file (multipart/form-data)
- `POST /api/resume` - Resume transfer (JSON body: `{file, offset, direction}`)

### 4. Use the React Frontend

Start the React app:
```bash
cd frontend
npm start
```

Open http://localhost:3000 in your browser.

Features:
- View server file list
- Upload files with progress bar
- Download files with checksum verification
- Automatic refresh after operations

### 5. Run Automated Tests

**Linux/macOS:**
```bash
cd demo_scripts
chmod +x run_tests.sh
./run_tests.sh
```

**Windows:**
```cmd
cd demo_scripts
run_tests.bat
```

**Simple Python Test:**

**Linux/macOS:**
```bash
cd server
python3 test_simple.py
```

**Windows:**
```cmd
cd server
python test_simple.py
```

The test scripts will:
1. Create test files
2. Start the TCP server
3. Test PUT, LIST, GET operations
4. Test RESUME functionality
5. Generate `transcript.txt` with results

## Testing Instructions

### Required Test Scenarios

1. **PUT Operation**
   - Upload a file using CLI or frontend
   - Verify SHA256 checksum matches
   - Check file appears in server storage

2. **GET Operation**
   - Download a file from server
   - Verify SHA256 checksum matches original
   - Compare file contents byte-by-byte

3. **RESUME Operation**
   - Start uploading a large file
   - Interrupt the transfer (Ctrl+C or kill process)
   - Resume from the last offset
   - Verify final file matches original checksum

### Manual Test Commands

See `demo_scripts/demo_commands.txt` for detailed manual testing instructions.

### Expected Output

After running tests, you should see:
- Files successfully uploaded with SHA256 checksums
- Files successfully downloaded with matching checksums
- Resume operations completing partial transfers
- All operations logged in `server/logs/server.log`

## Implementation Details

### Server Features
- **Async I/O**: Uses `asyncio` for concurrent client handling
- **Safe Writes**: Writes to `.part` temporary files, renames on success
- **Checksum Verification**: SHA256 computed during streaming
- **Error Handling**: Graceful error messages via `E` message type
- **Logging**: All operations logged with timestamps

### Client Library Features
- **Synchronous API**: Easy to use in scripts and HTTP wrappers
- **Automatic Reconnection**: Each function manages its own connection
- **Progress Tracking**: Can be extended for progress callbacks
- **Checksum Validation**: Verifies server checksums match client

### Protocol Compliance
- ✅ 4-byte big-endian length prefix
- ✅ 1-byte message type
- ✅ All message types implemented (L, G, P, R, Q, O, E, F, S)
- ✅ SHA256 checksums for integrity
- ✅ Safe file writes (temp + rename)
- ✅ Resume support with byte offsets
- ✅ Configurable chunk size (default 4096)

## Configuration

### Environment Variables
- `FT_ECHO_HOST`: TCP server host (default: localhost)
- `FT_ECHO_PORT`: TCP server port (default: 9000)

### Server Configuration
Edit `server/tcp_server.py`:
- `DEFAULT_PORT`: Server listening port
- `CHUNK_SIZE`: Transfer chunk size (bytes)
- `STORAGE_DIR`: Directory for stored files

## Troubleshooting

### Server won't start
- Check if port is already in use: `lsof -i :9000` (Unix) or `netstat -an | findstr 9000` (Windows)
- Check Python version: `python3 --version` (needs 3.10+)

### Connection refused
- Ensure TCP server is running
- Check firewall settings
- Verify host and port are correct

### Checksum mismatch
- Verify file wasn't corrupted during transfer
- Check network stability
- Ensure both client and server use same chunk size

### Resume not working
- Verify partial file (`.part`) exists in storage directory
- Check offset matches actual file size
- Ensure same filename is used for resume

## Authors

The following students contributed to this project:
- Penubothu Vaishnavi
- Velagapudi Jeshnav
- Ugrapalli Mukesh
- Mullapudi Mounika Sri Vijaya Lakshmi
- Bhanu Kiran Annavarapu
- Ravooru Sumanaswi
- Guntumadugu Manjeesh
- Sesank Chaluvadi
- Kavitha Sai Prasanth
- Kodavati Lakshmi Manikanta
- Paturi Bhavana
