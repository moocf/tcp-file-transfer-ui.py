# Complete Step-by-Step Guide to Run FT-Echo Project

## Prerequisites Check

First, verify you have everything installed:

```powershell
# Check Python (should show version 3.10 or higher)
python --version

# Check Node.js (should show version 16 or higher)
node --version

# Check npm
npm --version
```

If any are missing, install them first.

---

## Step 1: Install Python Dependencies

Open PowerShell and run:

```powershell
cd "C:\Users\Mukesh\Desktop\CN Project\server"
pip install -r requirements.txt
```

**Expected output:** Packages install successfully (fastapi, uvicorn, etc.)

---

## Step 2: Install Node.js Dependencies

In a NEW PowerShell window:

```powershell
cd "C:\Users\Mukesh\Desktop\CN Project\frontend"
npm install
```

**Expected output:** node_modules folder is created, packages install

**Wait for this to complete** (may take 1-2 minutes)

---

## Step 3: Start the TCP Server

In a NEW PowerShell window (Terminal 1):

```powershell
cd "C:\Users\Mukesh\Desktop\CN Project\server"
python tcp_server.py 9000
```

**Expected output:**
```
INFO - FT-Echo server listening on ('0.0.0.0', 9000)
```

**IMPORTANT:** Keep this window open! The server must stay running.

---

## Step 4: Start the FastAPI HTTP Server

In a NEW PowerShell window (Terminal 2):

```powershell
cd "C:\Users\Mukesh\Desktop\CN Project\server"
python fastapi_app.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**IMPORTANT:** Keep this window open too!

---

## Step 5: Start the React Frontend

In a NEW PowerShell window (Terminal 3):

```powershell
cd "C:\Users\Mukesh\Desktop\CN Project\frontend"
npm start
```

**Expected output:**
- Browser should automatically open to http://localhost:3000
- If not, manually open: http://localhost:3000

**IMPORTANT:** Keep this window open!

---

## Step 6: Verify Everything is Running

You should now have **3 PowerShell windows open**:

1. **Terminal 1:** TCP Server (port 9000) - showing server logs
2. **Terminal 2:** FastAPI Server (port 8000) - showing uvicorn logs
3. **Terminal 3:** React App (port 3000) - showing npm/react logs

### Quick Test:

Open a browser and go to: **http://localhost:8000/api/list**

You should see JSON like:
```json
{"ok":true,"files":[]}
```

If you see this, the backend is working!

---

## Step 7: Test the Frontend

1. Go to http://localhost:3000 (should already be open)
2. Click the **"Refresh"** button in the "Server Files" section
3. The error should disappear and show "No files on server" (which is correct - no files uploaded yet)

---

## Step 8: Upload a Test File

1. In the React interface, click **"Choose File"** in the "Upload File" section
2. Select any file from your computer (e.g., a text file, image, etc.)
3. The file will upload automatically
4. You should see:
   - Progress bar during upload
   - Success message with SHA256 checksum
   - File appears in the "Server Files" list

---

## Step 9: Download a File

1. In the "Server Files" section, click **"Download"** next to any file
2. The file should download to your browser's download folder
3. You'll see a success message with SHA256 checksum

---

## Troubleshooting

### Problem: "Network Error" in React

**Solution:**
1. Check if FastAPI is running (Terminal 2) - should show uvicorn logs
2. Check if TCP server is running (Terminal 1) - should show server logs
3. Try accessing http://localhost:8000/api/list directly in browser
4. If that doesn't work, restart both servers

### Problem: "Connection refused" or "Port already in use"

**Solution:**
1. Close all PowerShell windows
2. Check if ports are in use:
   ```powershell
   netstat -an | findstr "9000"
   netstat -an | findstr "8000"
   netstat -an | findstr "3000"
   ```
3. If ports are in use, kill the processes or use different ports

### Problem: Python not found

**Solution:**
1. Make sure Python is installed: `python --version`
2. If not installed, download from python.org
3. Make sure Python is in your PATH

### Problem: npm install fails

**Solution:**
1. Make sure Node.js is installed: `node --version`
2. Try clearing cache: `npm cache clean --force`
3. Delete `node_modules` folder and `package-lock.json`, then run `npm install` again

### Problem: FastAPI can't connect to TCP server

**Solution:**
1. Make sure TCP server (Terminal 1) is running first
2. Check the TCP server logs for errors
3. Restart TCP server, then restart FastAPI

---

## Complete Startup Sequence (Quick Reference)

```powershell
# Terminal 1: TCP Server
cd "C:\Users\Mukesh\Desktop\CN Project\server"
python tcp_server.py 9000

# Terminal 2: FastAPI (wait 2 seconds after starting TCP server)
cd "C:\Users\Mukesh\Desktop\CN Project\server"
python fastapi_app.py

# Terminal 3: React (wait 2 seconds after starting FastAPI)
cd "C:\Users\Mukesh\Desktop\CN Project\frontend"
npm start
```

---

## Verification Checklist

- [ ] Python dependencies installed (`pip install -r requirements.txt` succeeded)
- [ ] Node.js dependencies installed (`npm install` succeeded)
- [ ] TCP server running (Terminal 1 shows "listening on port 9000")
- [ ] FastAPI server running (Terminal 2 shows "Uvicorn running on port 8000")
- [ ] React app running (Terminal 3 shows "Compiled successfully")
- [ ] Browser shows http://localhost:3000 without errors
- [ ] http://localhost:8000/api/list returns JSON
- [ ] React interface shows "No files on server" (not "Network Error")
- [ ] Can upload a file successfully
- [ ] Can download a file successfully

---

## If Everything Works

You should see:
- ✅ No "Network Error" message
- ✅ "No files on server" or list of files
- ✅ Can upload files with progress bar
- ✅ Can download files
- ✅ SHA256 checksums displayed after transfers

---

## Need Help?

Check the logs:
- TCP Server logs: `server/logs/server.log`
- FastAPI logs: Terminal 2 output
- React logs: Terminal 3 output
- Browser console: Press F12 in browser, check Console tab

