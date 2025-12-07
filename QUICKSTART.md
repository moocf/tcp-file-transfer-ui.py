# FT-Echo Quick Start Guide

## Prerequisites
- Python 3.10+
- Node.js 16+ and npm
- TCP port 9000 available
- HTTP port 8000 available (for FastAPI)
- HTTP port 3000 available (for React)

## Quick Start (5 minutes)

### Step 1: Install Dependencies

**Python:**
```bash
cd server
pip install -r requirements.txt
```
(On Windows, use `python` instead of `python3` in all commands)

**Node.js:**
```bash
cd frontend
npm install
```

### Step 2: Start the TCP Server

**Linux/macOS:**
```bash
cd server
python3 tcp_server.py 9000
```

**Windows:**
```cmd
cd server
python tcp_server.py 9000
```

Keep this terminal open. The server is now listening on port 9000.

### Step 3: Test with CLI Client (Terminal 2)

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

Then in the CLI:
```
connect localhost 9000
list
put ../demo_data/small.txt
get small.txt
quit
```

### Step 4: Start FastAPI HTTP Server (Terminal 3)

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

Or (all platforms):
```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```

### Step 5: Start React Frontend (Terminal 4)

```bash
cd frontend
npm start
```

Open http://localhost:3000 in your browser.

## Testing Checklist

- [ ] TCP server starts without errors
- [ ] CLI client can connect and list files
- [ ] CLI client can upload a file (PUT)
- [ ] CLI client can download a file (GET)
- [ ] SHA256 checksums match after transfer
- [ ] FastAPI endpoints respond (check http://localhost:8000/api/list)
- [ ] React frontend loads and shows file list
- [ ] React frontend can upload files
- [ ] React frontend can download files

## Common Issues

**Port already in use:**
- Change port: `python3 tcp_server.py 9001`
- Update `TCP_PORT` in `fastapi_app.py` if needed

**Module not found:**
- Ensure you're in the correct directory
- Install dependencies: `pip install -r requirements.txt`

**Connection refused:**
- Ensure TCP server is running
- Check firewall settings
- Verify host/port are correct

## Next Steps

- Read `README.md` for detailed documentation
- Check `demo_scripts/demo_commands.txt` for advanced usage
- Run `server/test_simple.py` for automated basic tests
- Review `server/logs/server.log` for server activity

