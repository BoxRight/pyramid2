import { useState } from 'react'
import './ContractSummary.css'

/**
 * Summary Layer - Answer First, Details Second
 * Shows the most important information at a glance
 * Progressive disclosure: Click to expand details
 */
function ContractSummary({ contract, analysisResults, onViewDetails, onQuery }) {
  // Debug: Log what we're receiving from backend
  console.log('📊 ContractSummary received analysisResults:', {
    has_analysisResults: !!analysisResults,
    analysisResults_type: typeof analysisResults,
    analysisResults_keys: analysisResults ? Object.keys(analysisResults) : [],
    has_violation_results: !!analysisResults?.violation_results,
    violation_results_length: analysisResults?.violation_results?.length || 0,
    has_fulfillment_results: !!analysisResults?.fulfillment_results,
    fulfillment_results_length: analysisResults?.fulfillment_results?.length || 0,
    total_solutions: analysisResults?.total_solutions,
    num_predicates: analysisResults?.num_predicates,
    sample_violation: analysisResults?.violation_results?.[0] || null
  })
  
  // Log full violation results structure for debugging
  if (analysisResults?.violation_results?.length > 0) {
    console.log('📋 Full violation_results structure:', analysisResults.violation_results)
    console.log('📋 First violation details:', {
      predicate: analysisResults.violation_results[0].predicate,
      total_violation_scenarios: analysisResults.violation_results[0].total_violation_scenarios,
      total_fulfillment_scenarios: analysisResults.violation_results[0].total_fulfillment_scenarios,
      consequences_count: analysisResults.violation_results[0].consequences?.length || 0,
      consequences: analysisResults.violation_results[0].consequences
    })
  }

  // Calculate summary stats
  // Total scenarios in the solution space (all possible states)
  const totalScenarios = analysisResults?.total_solutions || 0
  
  // Count obligations that have automatic consequences when unfulfilled
  // These are obligations where if not fulfilled, other predicates are triggered
  const obligationsWithConsequences = analysisResults?.violation_results?.filter(
    v => v.total_violation_scenarios > 0 && (v.consequences?.length || 0) > 0
  ).length || 0
  
  // Count obligations that are always fulfilled (present in all scenarios)
  // These have no unfulfillment scenarios to analyze
  const obligationsAlwaysFulfilled = analysisResults?.violation_results?.filter(
    v => v.total_violation_scenarios === 0 && v.total_fulfillment_scenarios === totalScenarios
  ).length || 0
  
  // Total number of unfulfillment scenarios across all obligations
  // This shows how many scenarios we've analyzed for consequences
  const totalUnfulfillmentScenarios = analysisResults?.violation_results?.reduce(
    (sum, v) => sum + (v.total_violation_scenarios || 0), 0
  ) || 0
  
  // Total consequences identified (automatic triggers when obligations are unfulfilled)
  const totalConsequences = analysisResults?.violation_results?.reduce(
    (sum, v) => sum + (v.num_consequences || 0), 0
  ) || 0
  
  const hasConsequences = obligationsWithConsequences > 0
  const contractStatus = hasConsequences ? 'warning' : 'success'
  
  // Get top 3 obligations with most consequences when unfulfilled
  // Sort by number of consequences (most impactful first)
  const criticalObligations = analysisResults?.violation_results
    ?.filter(v => v.total_violation_scenarios > 0 && (v.consequences?.length || 0) > 0)
    .sort((a, b) => {
      // Sort by consequences count (descending), then by unfulfillment scenarios (descending)
      if ((b.consequences?.length || 0) !== (a.consequences?.length || 0)) {
        return (b.consequences?.length || 0) - (a.consequences?.length || 0)
      }
      return b.total_violation_scenarios - a.total_violation_scenarios
    })
    .slice(0, 3) || []

  if (!analysisResults) {
    return (
      <div className="contract-summary">
        <div className="summary-card empty-state">
          <h3>No Contract Analysis</h3>
          <p>Analyze a contract to see summary information</p>
        </div>
      </div>
    )
  }

  return (
    <div className="contract-summary">
      {/* PRIMARY ANSWER - Contract Status */}
      <div className={`summary-card status-card ${contractStatus}`}>
        <div className="status-content">
          <h2 className="status-title">
            {hasConsequences 
              ? `${obligationsWithConsequences} Obligation${obligationsWithConsequences !== 1 ? 's' : ''} with Automatic Consequences`
              : 'No Automatic Consequences'
            }
          </h2>
          <p className="status-description">
            {hasConsequences
              ? `When these obligations are unfulfilled, ${totalConsequences} automatic consequence${totalConsequences !== 1 ? 's' : ''} are triggered`
              : `All obligations are fulfilled in all ${totalScenarios} scenarios - no unfulfillment consequences analyzed`
            }
          </p>
        </div>
      </div>

      {/* KEY METRICS - Grouped in cards */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-content">
            <div className="metric-label">Total Scenarios</div>
            <div className="metric-value">{analysisResults.total_solutions || 0}</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-content">
            <div className="metric-label">Obligations</div>
            <div className="metric-value">{analysisResults.num_predicates || 0}</div>
          </div>
        </div>

        <div className="metric-card warning">
          <div className="metric-content">
            <div className="metric-label">Obligations with Consequences</div>
            <div className="metric-value">{obligationsWithConsequences}</div>
            <div className="metric-subtext">when unfulfilled</div>
          </div>
        </div>

        <div className="metric-card info">
          <div className="metric-content">
            <div className="metric-label">Total Consequences</div>
            <div className="metric-value">{totalConsequences}</div>
            <div className="metric-subtext">automatic triggers</div>
          </div>
        </div>
      </div>

      {/* OBLIGATIONS WITH CONSEQUENCES - Always visible */}
      {hasConsequences && (
        <div className="summary-card issues-card">
          <div className="card-header">
            <div>
              <h3>Obligations with Automatic Consequences</h3>
              <p className="card-subtitle">When unfulfilled, these obligations trigger automatic consequences</p>
            </div>
          </div>

          <div className="card-content">
            {criticalObligations.map((obligation, idx) => (
              <div key={idx} className="issue-item">
                <div className="issue-header">
                  <span className="issue-name">{obligation.predicate}</span>
                  <span className="issue-count">{obligation.total_violation_scenarios} unfulfillment scenario{obligation.total_violation_scenarios !== 1 ? 's' : ''}</span>
                </div>
                {obligation.consequences?.length > 0 && (
                  <div className="issue-consequences">
                    <strong>Automatic Consequences:</strong> {obligation.consequences.length} predicate{obligation.consequences.length !== 1 ? 's' : ''} triggered when unfulfilled
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PRIMARY ACTION - Ask a Question */}
      <div className="summary-actions">
        <button 
          className="action-button primary"
          onClick={() => onQuery && onQuery()}
        >
          Ask a Question
        </button>
      </div>
    </div>
  )
}

export default ContractSummary

