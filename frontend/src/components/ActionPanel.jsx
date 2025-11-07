import { useState } from 'react'
import './ActionPanel.css'
import ContractSummary from './ContractSummary'
import QueryInterface from './QueryInterface'

/**
 * Right Action Panel - Contextual actions and metadata
 * Shows Analyze and Query tabs after contract is compiled
 */
function ActionPanel({ contract, analysisResults, onQueryClick }) {
  const [activeTab, setActiveTab] = useState('analyze')

  // Panel is only rendered when contractCompiled is true (from parent)
  // This check is just for safety
  if (!contract) {
    return null
  }

  return (
    <div className="action-panel">
      <div className="action-panel-header">
        <div className="action-panel-tabs">
          <button
            className={`action-tab ${activeTab === 'analyze' ? 'active' : ''}`}
            onClick={() => setActiveTab('analyze')}
          >
            Analyze
          </button>
          <button
            className={`action-tab ${activeTab === 'query' ? 'active' : ''}`}
            onClick={() => setActiveTab('query')}
          >
            Query
          </button>
        </div>
      </div>

      <div className="action-panel-content">
        {activeTab === 'analyze' && (
          <div className="analyze-tab">
            {analysisResults ? (
              <ContractSummary
                contract={contract}
                analysisResults={analysisResults}
                onViewDetails={() => {}}
                onQuery={() => {
                  setActiveTab('query')
                  onQueryClick?.()
                }}
              />
            ) : (
              <div className="empty-state">
                <div className="empty-state-title">Analysis Pending</div>
                <div className="empty-state-description">
                  Contract will be analyzed automatically after validation
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'query' && (
          <div className="query-tab">
            <QueryInterface
              contract={contract}
              analysisResults={analysisResults}
              onBackToAnalysis={() => setActiveTab('analyze')}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default ActionPanel

