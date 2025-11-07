import { useState, useEffect, useCallback } from 'react'
import ContractDocument from './ContractDocument'
import './ContractReview.css'
import { compileContract, analyzeContract } from '../services/api'

function ContractReview({ contract, lamlCode, contractCompiled, onContractCompiled, onAnalysisComplete, onStepChange }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Auto-validate and analyze when contract is available
  const handleAutoProcess = useCallback(async () => {
    if (!lamlCode?.trim() || !contract) return

    setLoading(true)
    setError(null)

    try {
      // Auto-validate (compile)
      const compileResult = await compileContract({
        contract_id: contract?.contract_id || contract?.id || 'new-contract',
        laml_content: lamlCode
      })

      console.log('📝 Compile result:', {
        contract_id: compileResult.contract_id,
        has_parsed_contract: !!compileResult.parsed_contract,
        parsed_contract_type: typeof compileResult.parsed_contract,
        parsed_contract_keys: compileResult.parsed_contract ? Object.keys(compileResult.parsed_contract) : []
      })
      
      onContractCompiled(compileResult)

      // Auto-analyze after compilation (don't change step, just run analysis)
      setTimeout(async () => {
        try {
          const analysisResult = await analyzeContract({
            contract_id: contract?.contract_id || contract?.id
          })
          console.log('📊 Analysis result:', {
            contract_id: analysisResult.contract_id,
            num_predicates: analysisResult.num_predicates,
            violation_results_count: analysisResult.violation_results?.length
          })
          onAnalysisComplete(analysisResult)
          // Don't change step - keep user on Review so they can read the contract
        } catch (err) {
          console.error('Auto-analysis failed:', err)
        }
      }, 500)
    } catch (err) {
      setError(err.message || 'Validation failed')
    } finally {
      setLoading(false)
    }
  }, [contract, lamlCode, contractCompiled, onContractCompiled, onAnalysisComplete, onStepChange])

  useEffect(() => {
    if (contract && !contractCompiled && lamlCode) {
      handleAutoProcess()
    }
  }, [contract, contractCompiled, lamlCode, handleAutoProcess])

  return (
    <div className="contract-review">
      <div className="view-header">
        <h2>Contract Document</h2>
        {loading && (
          <div className="processing-indicator">
            <span className="loading-spinner"></span>
            <span>Validating and analyzing contract...</span>
          </div>
        )}
      </div>

      <div className="view-content">
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="review-container">
          {/* Legal Document View - Main content panel */}
          <div className="document-section full-view">
            {(() => {
              console.log('🔍 ContractReview render check:', {
                has_contract: !!contract,
                has_parsed_contract: !!contract?.parsed_contract,
                contract_id: contract?.contract_id || contract?.id,
                parsed_contract_type: typeof contract?.parsed_contract
              })
              
              if (contract?.parsed_contract) {
                return <ContractDocument contractData={contract.parsed_contract} />
              } else {
                return (
                  <div className="empty-state">
                    <div className="empty-state-title">No Contract Document</div>
                    <div className="empty-state-description">
                      {contractCompiled 
                        ? 'Contract compiled but parsed document not available. Check console for details.'
                        : 'Contract will be displayed here after compilation'}
                    </div>
                  </div>
                )
              }
            })()}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ContractReview

