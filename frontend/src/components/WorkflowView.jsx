import React, { useState, useEffect } from 'react'
import NaturalLanguageInput from './NaturalLanguageInput'
import ContractReview from './ContractReview'
import ActionPanel from './ActionPanel'
import ContractDocument from './ContractDocument'
import './WorkflowView.css'

/**
 * Two-Panel Layout:
 * - Main Panel: Contract document (always visible after generation)
 * - Right Panel: Action tabs (Analyze, Query) - appears after compilation
 */
function WorkflowView({ 
  step, 
  contract, 
  lamlCode, 
  contractCompiled,
  analysisResults,
  onContractGenerated, 
  onContractCompiled,
  onAnalysisComplete,
  onStepChange 
}) {
  const [panelWidth, setPanelWidth] = useState(400)
  const [isResizing, setIsResizing] = useState(false)

  // Handle resizing
  const handleMouseDown = (e) => {
    setIsResizing(true)
    e.preventDefault()
  }


  // Add global event listeners for resizing
  useEffect(() => {
    if (isResizing) {
      const handleMove = (e) => {
        // Account for sidebar width (280px)
        const sidebarWidth = 280
        const newWidth = window.innerWidth - e.clientX - sidebarWidth
        // Constrain width between 300px and 800px
        const constrainedWidth = Math.max(300, Math.min(800, newWidth))
        setPanelWidth(constrainedWidth)
      }
      
      const handleUp = () => setIsResizing(false)
      
      window.addEventListener('mousemove', handleMove)
      window.addEventListener('mouseup', handleUp)
      
      return () => {
        window.removeEventListener('mousemove', handleMove)
        window.removeEventListener('mouseup', handleUp)
      }
    }
  }, [isResizing])

  // Step 1: Generate - Only show input, no panels
  if (step === 'generate') {
    return (
      <div className="workflow-view workflow-view-single">
        <NaturalLanguageInput 
          onContractGenerated={onContractGenerated}
        />
      </div>
    )
  }

  // Step 2+: Show contract in main panel, action panel on right (if compiled)
  return (
    <div className="workflow-view workflow-view-two-panel">
      {/* Main Panel - Contract Document */}
      <div className="main-panel">
        <ContractReview
          contract={contract}
          lamlCode={lamlCode}
          contractCompiled={contractCompiled}
          onContractCompiled={onContractCompiled}
          onAnalysisComplete={onAnalysisComplete}
          onStepChange={onStepChange}
        />
      </div>

      {/* Right Action Panel - Analyze & Query Tabs */}
      {contractCompiled && (
        <>
          {/* Resize Handle */}
          <div 
            className={`resize-handle ${isResizing ? 'resizing' : ''}`}
            onMouseDown={handleMouseDown}
          />
          <div className="action-panel-wrapper" style={{ width: `${panelWidth}px` }}>
            <ActionPanel
              contract={contract}
              analysisResults={analysisResults}
              onQueryClick={() => onStepChange('query')}
            />
          </div>
        </>
      )}
    </div>
  )
}

export default WorkflowView

