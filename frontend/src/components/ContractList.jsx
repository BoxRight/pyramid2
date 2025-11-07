import './ContractList.css'

function ContractList({ contracts, onContractSelect }) {
  if (contracts.length === 0) {
    return (
      <div className="contract-list">
        <div className="view-header">
          <h2>Contracts</h2>
        </div>
        <div className="view-content">
          <div className="empty-state">
            <div className="empty-state-title">No Contracts</div>
            <div className="empty-state-description">
              Generate a contract from natural language or upload a LAML file to get started.
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="contract-list">
      <div className="view-header">
        <h2>Contracts ({contracts.length})</h2>
        <div className="view-header-actions">
          <button className="secondary">Import</button>
          <button className="secondary">Refresh</button>
        </div>
      </div>

      <div className="view-content">
        <div className="contracts-grid">
          {contracts.map((contract, index) => (
            <div 
              key={index} 
              className="contract-card"
              onClick={() => onContractSelect(contract)}
            >
              <div className="contract-card-header">
                <span className="contract-title">
                  {contract.contract_id || `Contract ${index + 1}`}
                </span>
              </div>
              <div className="contract-card-body">
                <div className="contract-meta">
                  <span className="meta-item">
                    <span className="meta-label">Type:</span>
                    <span className="meta-value">{contract.contract_type || 'N/A'}</span>
                  </span>
                  <span className="meta-item">
                    <span className="meta-label">Status:</span>
                    <span className="meta-value">{contract.status || 'draft'}</span>
                  </span>
                </div>
                {contract.created_at && (
                  <div className="contract-date">
                    Created: {new Date(contract.created_at).toLocaleDateString()}
                  </div>
                )}
              </div>
              <div className="contract-card-footer">
                <button className="view-button">View Contract</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default ContractList

