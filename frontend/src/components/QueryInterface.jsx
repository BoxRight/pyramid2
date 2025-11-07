import { useState, useMemo } from 'react'
import './QueryInterface.css'
import { queryContract } from '../services/api'
import MockDataIndicator from './MockDataIndicator'

function QueryInterface({ contract, analysisResults, onBackToAnalysis }) {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [selectedQueryType, setSelectedQueryType] = useState(null)

  // Helper function to generate human-readable labels from predicate names
  const generateQueryLabel = (predicate, type) => {
    const readable = predicate.replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
    
    if (type === 'violation') {
      return `What happens if ${readable} is NOT fulfilled?`
    } else {
      return `What happens when ${readable} IS fulfilled?`
    }
  }

  // Helper function to generate description
  const generateDescription = (predicate, type) => {
    const readable = predicate.replace(/_/g, ' ')
      .toLowerCase()
    
    if (type === 'violation') {
      return `See the automatic consequences when ${readable} is not fulfilled`
    } else {
      return `See what obligations are triggered when ${readable} is fulfilled`
    }
  }

  // Generate example queries dynamically from actual contract predicates
  const exampleQueries = useMemo(() => {
    // Get predicates from analysis results or contract
    const predicates = analysisResults?.predicates || 
                       analysisResults?.violation_results?.map(v => v.predicate) || 
                       []
    
    if (predicates.length === 0) {
      return []
    }

    // Prioritize predicates that have consequences when unfulfilled
    const predicatesWithConsequences = predicates.filter(p => {
      const result = analysisResults?.violation_results?.find(v => v.predicate === p)
      return result && (
        (result.consequences?.length > 0) || 
        (result.total_violation_scenarios > 0)
      )
    })

    // Use predicates with consequences first, then fall back to all predicates
    const candidates = predicatesWithConsequences.length > 0 
      ? predicatesWithConsequences 
      : predicates

    // Select up to 4 predicates (try to balance violation and fulfillment queries)
    const selected = candidates.slice(0, Math.min(candidates.length, 4))
    
    // Generate queries: try to balance violation and fulfillment
    // Priority: predicates with most consequences first
    const queries = []
    
    // First pass: Add violation queries (most important - consequences of unfulfillment)
    for (let i = 0; i < selected.length && queries.length < 4; i++) {
      const predicate = selected[i]
      queries.push({
        type: 'violation',
        predicate,
        label: generateQueryLabel(predicate, 'violation'),
        description: generateDescription(predicate, 'violation')
      })
    }
    
    // If we have space, add a fulfillment query for the first predicate
    // (This gives users a balanced view)
    if (queries.length < 4 && selected.length > 0) {
      queries.push({
        type: 'fulfillment',
        predicate: selected[0],
        label: generateQueryLabel(selected[0], 'fulfillment'),
        description: generateDescription(selected[0], 'fulfillment')
      })
    }

    return queries.slice(0, 4) // Ensure max 4 examples
  }, [analysisResults])

  // Auto-execute query when example is clicked
  const handleExampleClick = async (example) => {
    if (!contract?.contract_id) {
      setError('No contract selected')
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)
    setSelectedQueryType(example.type)

    try {
      const result = await queryContract({
        contract_id: contract.contract_id,
        query_type: example.type,
        predicate_name: example.predicate
      })

      setResults(result)
    } catch (err) {
      setError(err.message || 'Query failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="query-interface">
      <div className="view-header">
        <h2>Ask a Question</h2>
      </div>

      <div className="view-content">
        {import.meta.env.VITE_USE_MOCK_DATA !== 'false' && <MockDataIndicator />}
        <div className="query-container">
          <div className="query-form-section">
            {/* Recognition over Recall: Example queries only */}
            <div className="examples-section">
              <h3>Common Questions</h3>
              <p className="examples-subtitle">Click any question to get an instant answer</p>
              {exampleQueries.length > 0 ? (
                <div className="examples-list">
                  {exampleQueries.map((example, index) => (
                    <button
                      key={`${example.predicate}-${example.type}-${index}`}
                      className="example-query-button"
                      onClick={() => handleExampleClick(example)}
                      type="button"
                      disabled={loading}
                    >
                      <div className="example-header">
                        <span className="example-label">{example.label}</span>
                      </div>
                      <div className="example-description">{example.description}</div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="empty-examples">
                  <p className="empty-state-description">
                    {analysisResults 
                      ? 'No obligations available for querying'
                      : 'Analyze the contract first to see available questions'}
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="query-results-section">
            <h3>Answer</h3>
            {results ? (
              <div className="query-results">
                <div className="result-header">
                  <span className="result-predicate">
                    {results.predicate?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Obligation'}
                  </span>
                  <span className="result-type">
                    {selectedQueryType === 'violation' ? 'Not Met' : 'Met'}
                  </span>
                </div>
                
                {selectedQueryType === 'violation' && (
                  <div className="result-stats">
                    <div className="stat-item warning">
                      <span className="stat-label">Violation Scenarios</span>
                      <span className="stat-value">{results.total_violation_scenarios || 0}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Valid Scenarios</span>
                      <span className="stat-value">{results.total_fulfillment_scenarios || 0}</span>
                    </div>
                  </div>
                )}

                {selectedQueryType === 'fulfillment' && (
                  <div className="result-stats">
                    <div className="stat-item success">
                      <span className="stat-label">Valid Scenarios</span>
                      <span className="stat-value">{results.total_fulfillment_scenarios || 0}</span>
                    </div>
                  </div>
                )}

                {results.consequences && results.consequences.length > 0 && (
                  <div className="consequences-section">
                    <h4>Automatic Consequences ({results.consequences.length})</h4>
                    <p className="consequences-intro">
                      When this obligation is {selectedQueryType === 'violation' ? 'NOT met' : 'met'}, the following actions are automatically triggered:
                    </p>
                    <ul className="consequences-list">
                      {results.consequences.map((cons, idx) => (
                        <li key={idx} className={`consequence ${cons.consequence_type}`}>
                          <span className="consequence-predicate">
                            {cons.predicate_name?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </span>
                          <span className="consequence-type">
                            {cons.consequence_type === 'always_present' 
                              ? 'Obligatory Action Triggered' 
                              : 'Prohibited Action Triggered'}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {results.consequences && results.consequences.length === 0 && (
                  <div className="result-message">
                    <p>No automatic consequences found for this scenario.</p>
                  </div>
                )}

                {results.message && (
                  <div className="result-message">
                    {results.message}
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-results">
                <div className="empty-state-title">No Answer Yet</div>
                <div className="empty-state-description">
                  Ask a question to see the answer here
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default QueryInterface

