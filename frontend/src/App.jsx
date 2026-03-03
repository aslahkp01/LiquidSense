import { useState, useRef } from 'react'
import './App.css'

function App() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
      setResult(null)
      setError(null)
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setResult(null)
      setError(null)
    }
  }

  const handleSubmit = async () => {
    if (!file) return

    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const API_URL = import.meta.env.VITE_API_URL || ''
      const response = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message || 'Something went wrong. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setResult(null)
    setError(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const getMilkQuality = (milkPct) => {
    if (milkPct >= 90) return { label: 'Pure', color: '#4caf50' }
    if (milkPct >= 70) return { label: 'Slightly Adulterated', color: '#ff9800' }
    if (milkPct >= 50) return { label: 'Moderately Adulterated', color: '#f44336' }
    return { label: 'Highly Adulterated', color: '#b71c1c' }
  }

  return (
    <div className="app">
      <div className="card">
        <div className="header">
          <div className="logo">
            <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M8 2h8l2 6H6l2-6z" />
              <path d="M6 8v10a4 4 0 004 4h4a4 4 0 004-4V8" />
              <path d="M6 14h12" />
            </svg>
          </div>
          <h1>LiquidSense</h1>
          <p className="subtitle">Milk Adulteration Detection System</p>
        </div>

        <div
          className={`dropzone ${dragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".s2p"
            onChange={handleFileChange}
            hidden
          />
          {file ? (
            <div className="file-info">
              <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="#4caf50" strokeWidth="2">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                <polyline points="14,2 14,8 20,8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
              </svg>
              <span className="file-name">{file.name}</span>
              <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
          ) : (
            <div className="dropzone-content">
              <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                <polyline points="17,8 12,3 7,8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              <p>Drag & drop your <strong>.s2p</strong> file here</p>
              <span className="or-text">or click to browse</span>
            </div>
          )}
        </div>

        <div className="actions">
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={!file || loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Analyzing...
              </>
            ) : (
              'Analyze Sample'
            )}
          </button>
          {(file || result) && (
            <button className="btn btn-secondary" onClick={handleReset}>
              Reset
            </button>
          )}
        </div>

        {error && (
          <div className="error-box">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
            {error}
          </div>
        )}

        {result && (
          <div className="results">
            <h2>Analysis Results</h2>
            <div className="result-cards">
              <div className="result-card milk">
                <div className="result-value">{result.Milk_Percentage}%</div>
                <div className="result-label">Milk Content</div>
                <div className="progress-bar">
                  <div
                    className="progress-fill milk-fill"
                    style={{ width: `${result.Milk_Percentage}%` }}
                  ></div>
                </div>
              </div>
              <div className="result-card adulterant">
                <div className="result-value">{result.Adulteration}%</div>
                <div className="result-label">Adulteration</div>
                <div className="progress-bar">
                  <div
                    className="progress-fill adulterant-fill"
                    style={{ width: `${result.Adulteration}%` }}
                  ></div>
                </div>
              </div>
            </div>
            <div
              className="quality-badge"
              style={{ backgroundColor: getMilkQuality(result.Milk_Percentage).color }}
            >
              {getMilkQuality(result.Milk_Percentage).label}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
