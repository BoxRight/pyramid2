import { useState, useEffect } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism'
import './LAMLViewer.css'
import { compileContract, analyzeContract } from '../services/api'

function LAMLViewer({ contract, lamlCode, onAnalysisComplete }) {
  const [code, setCode] = useState(lamlCode || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [compiled, setCompiled] = useState(false)
  const [analysisLoading, setAnalysisLoading] = useState(false)

  useEffect(() => {
    if (lamlCode) {
      setCode(lamlCode)
    }
  }, [lamlCode])

  const handleCompile = async () => {
    if (!code.trim()) {
      setError('LAML code is empty')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const result = await compileContract({
        contract_id: contract?.contract_id || 'new-contract',
        laml_content: code
      })

      setCompiled(true)
      setError(null)
      
      // Auto-trigger analysis after compilation
      if (result.status === 'compiled') {
        handleAnalyze(result.contract_id)
      }
    } catch (err) {
      setError(err.message || 'Compilation failed')
      setCompiled(false)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async (contractId) => {
    if (!contractId && !contract?.contract_id) {
      setError('No contract ID available')
      return
    }

    setAnalysisLoading(true)
    setError(null)

    try {
      const result = await analyzeContract({
        contract_id: contractId || contract.contract_id
      })

      onAnalysisComplete(result)
    } catch (err) {
      setError(err.message || 'Analysis failed')
    } finally {
      setAnalysisLoading(false)
    }
  }

  const handleSave = () => {
    // TODO: Implement save functionality
    alert('Save functionality will be implemented')
  }

  return (
    <div className="laml-viewer">
      <div className="view-header">
        <h2>LAML Code Editor</h2>
        <div className="view-header-actions">
          <button 
            className="secondary" 
            onClick={handleSave}
            disabled={!code.trim()}
          >
            Save
          </button>
          <button 
            className="secondary" 
            onClick={() => handleAnalyze()}
            disabled={!compiled || analysisLoading}
          >
            {analysisLoading ? 'Analyzing...' : 'Analyze'}
          </button>
          <button 
            onClick={handleCompile}
            disabled={loading || !code.trim()}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                Compiling...
              </>
            ) : (
              'Compile'
            )}
          </button>
        </div>
      </div>

      <div className="view-content">
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {compiled && !error && (
          <div className="success-message">
            Contract compiled successfully! Ready for analysis.
          </div>
        )}

        <div className="code-editor-container">
          <div className="code-editor-header">
            <span className="file-name">
              {contract?.contract_id ? `${contract.contract_id}.laml` : 'contract.laml'}
            </span>
            <span className="code-info">
              {code.split('\n').length} lines • {code.length} characters
            </span>
          </div>
          <div className="code-editor">
            <textarea
              className="code-textarea"
              value={code}
              onChange={(e) => {
                setCode(e.target.value)
                setCompiled(false) // Reset compiled status when code changes
              }}
              placeholder="Enter or paste your LAML code here..."
              spellCheck={false}
            />
          </div>
        </div>

        <div className="laml-preview">
          <div className="preview-header">
            <h3>Syntax Highlighted Preview</h3>
          </div>
          <div className="preview-content">
            {code ? (
              <SyntaxHighlighter
                language="laml"
                style={vscDarkPlus}
                customStyle={{
                  margin: 0,
                  padding: '20px',
                  background: '#1e1e1e',
                  borderRadius: '4px'
                }}
              >
                {code}
              </SyntaxHighlighter>
            ) : (
              <div className="empty-code">
                <p>Enter LAML code to see syntax highlighting</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default LAMLViewer

