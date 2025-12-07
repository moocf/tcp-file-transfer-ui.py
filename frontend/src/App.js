import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// API base URL - change if FastAPI is running on different port
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [downloadProgress, setDownloadProgress] = useState({});

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      setLoading(true);
      setMessage(''); // Clear previous messages
      const response = await axios.get(`${API_BASE}/api/list`);
      if (response.data.ok) {
        setFiles(response.data.files || []);
        setMessage(''); // Clear any error messages on success
      }
    } catch (error) {
      const errorMsg = error.response 
        ? `Error loading files: ${error.response.status} - ${error.response.statusText}`
        : `Error loading files: ${error.message}. Make sure FastAPI server is running on ${API_BASE}`;
      setMessage(errorMsg);
      console.error('Load files error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      setLoading(true);
      setMessage('');
      setUploadProgress(0);

      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_BASE}/api/put`, formData, {
        // Let axios/browser set the Content-Type (with boundary) automatically
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(percentCompleted);
        },
      });

      if (response.data.ok) {
        setMessage(`✓ Upload successful! SHA256: ${response.data.sha}`);
        setUploadProgress(100);
        loadFiles(); // Refresh file list
      }
    } catch (error) {
      setMessage(`Upload error: ${error.message}`);
      setUploadProgress(0);
    } finally {
      setLoading(false);
      // Reset file input
      event.target.value = '';
    }
  };

  const handleDownload = async (filename) => {
    try {
      setLoading(true);
      setMessage('');
      setDownloadProgress({ ...downloadProgress, [filename]: 0 });

      const response = await axios.get(`${API_BASE}/api/get?file=${encodeURIComponent(filename)}`, {
        responseType: 'blob',
        onDownloadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setDownloadProgress({ ...downloadProgress, [filename]: percentCompleted });
          }
        },
      });

      // Get SHA256 from headers
      const sha256 = response.headers['x-sha256'];

      // Create blob and download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setMessage(`✓ Download successful! SHA256: ${sha256}`);
      setDownloadProgress({ ...downloadProgress, [filename]: 100 });
    } catch (error) {
      setMessage(`Download error: ${error.message}`);
      setDownloadProgress({ ...downloadProgress, [filename]: 0 });
    } finally {
      setLoading(false);
    }
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>FT-Echo File Transfer</h1>
        <p>TCP File Transfer Protocol Client</p>
      </header>

      <main className="App-main">
        <div className="upload-section">
          <h2>Upload File</h2>
          <input
            type="file"
            id="file-upload"
            onChange={handleUpload}
            disabled={loading}
          />
          {uploadProgress > 0 && uploadProgress < 100 && (
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${uploadProgress}%` }}
              >
                {uploadProgress}%
              </div>
            </div>
          )}
        </div>

        <div className="files-section">
          <div className="section-header">
            <h2>Server Files</h2>
            <button onClick={loadFiles} disabled={loading}>
              Refresh
            </button>
          </div>

          {message && (
            <div className={`message ${message.startsWith('✓') ? 'success' : 'error'}`}>
              {message}
            </div>
          )}

          {loading && files.length === 0 ? (
            <div className="loading">Loading files...</div>
          ) : files.length === 0 ? (
            <div className="empty">No files on server</div>
          ) : (
            <table className="files-table">
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Size</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {files.map((file) => (
                  <tr key={file.name}>
                    <td>{file.name}</td>
                    <td>{formatSize(file.size)}</td>
                    <td>
                      <button
                        onClick={() => handleDownload(file.name)}
                        disabled={loading}
                      >
                        Download
                      </button>
                      {downloadProgress[file.name] > 0 &&
                        downloadProgress[file.name] < 100 && (
                          <span className="progress-text">
                            {' '}
                            {downloadProgress[file.name]}%
                          </span>
                        )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;

