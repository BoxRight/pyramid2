import { useState } from 'react'
import './App.css'
import WorkflowView from './components/WorkflowView'
import Sidebar from './components/Sidebar'

function App() {
  // Progressive Disclosure: Track workflow step
  const [workflowStep, setWorkflowStep] = useState('generate') // generate -> review -> analyze -> query
  const [contracts, setContracts] = useState([])
  const [selectedContract, setSelectedContract] = useState(null)
  const [lamlCode, setLamlCode] = useState('')
  const [analysisResults, setAnalysisResults] = useState(null)
  const [contractCompiled, setContractCompiled] = useState(false)

  const handleContractGenerated = (contract) => {
    const newContract = { 
      ...contract, 
      id: Date.now(),
      parsed_contract: contract.parsed_contract // Include parsed contract document
    }
    setContracts([...contracts, newContract])
    setSelectedContract(newContract)
    setLamlCode(contract.laml_content || '')
    setContractCompiled(false)
    setAnalysisResults(null)
    // Progressive disclosure: Move to next step
    setWorkflowStep('review')
  }

  const handleContractCompiled = (result) => {
    console.log('🔄 handleContractCompiled called with:', {
      has_parsed_contract: !!result?.parsed_contract,
      parsed_contract_type: typeof result?.parsed_contract,
      selectedContract_id: selectedContract?.id
    })
    
    setContractCompiled(true)
    // Update contract with parsed document if available
    if (result?.parsed_contract && selectedContract) {
      const updatedContract = {
        ...selectedContract,
        parsed_contract: result.parsed_contract,
        compiled: true
      }
      console.log('✅ Updated contract with parsed_contract:', {
        contract_id: updatedContract.contract_id,
        has_parsed_contract: !!updatedContract.parsed_contract
      })
      setSelectedContract(updatedContract)
      // Also update in contracts list so it persists
      setContracts(prevContracts => 
        prevContracts.map(c => 
          c.id === selectedContract.id ? updatedContract : c
        )
      )
    } else {
      console.warn('⚠️ No parsed_contract in result or no selectedContract:', {
        has_parsed_contract: !!result?.parsed_contract,
        has_selectedContract: !!selectedContract
      })
    }
    // Analysis becomes available after compilation
  }

  const handleAnalysisComplete = (results) => {
    console.log('📊 handleAnalysisComplete called with:', {
      contract_id: results?.contract_id,
      num_predicates: results?.num_predicates,
      current_selectedContract_id: selectedContract?.id,
      current_selectedContract_has_parsed_contract: !!selectedContract?.parsed_contract
    })
    
    setAnalysisResults(results)
    
    // CRITICAL: Use functional update to ensure we have latest state
    setSelectedContract(prevContract => {
      if (!prevContract) return prevContract
      
      const updatedContract = {
        ...prevContract,
        parsed_contract: prevContract.parsed_contract, // PRESERVE parsed_contract from latest state
        analysisResults: results,
        compiled: prevContract.compiled || true // Preserve compiled status
      }
      
      console.log('✅ Updated contract with analysis (preserving parsed_contract):', {
        contract_id: updatedContract.contract_id,
        has_parsed_contract: !!updatedContract.parsed_contract,
        has_analysisResults: !!updatedContract.analysisResults
      })
      
      // Also update in contracts list
      setContracts(prevContracts => 
        prevContracts.map(c => 
          c.id === prevContract.id ? updatedContract : c
        )
      )
      
      return updatedContract
    })
    
    // Progressive disclosure: Move to analysis view
    setWorkflowStep('analyze')
  }

  const handleContractSelected = (contract) => {
    setSelectedContract(contract)
    setLamlCode(contract.laml_content || '')
    setContractCompiled(contract.compiled || false)
    setAnalysisResults(contract.analysisResults || null)
    // Determine which step to show based on contract state
    if (contract.analysisResults) {
      setWorkflowStep('analyze')
    } else if (contract.compiled) {
      setWorkflowStep('review')
    } else {
      setWorkflowStep('review')
    }
  }

  const handleStartOver = () => {
    setWorkflowStep('generate')
    setSelectedContract(null)
    setLamlCode('')
    setContractCompiled(false)
    setAnalysisResults(null)
  }

  return (
    <div className="app-container">
      <Sidebar 
        workflowStep={workflowStep}
        onStepChange={setWorkflowStep}
        contracts={contracts}
        onContractSelect={handleContractSelected}
        onStartOver={handleStartOver}
      />
      <div className="main-content">
        <WorkflowView
          step={workflowStep}
          contract={selectedContract}
          lamlCode={lamlCode}
          contractCompiled={contractCompiled}
          analysisResults={analysisResults}
          onContractGenerated={handleContractGenerated}
          onContractCompiled={handleContractCompiled}
          onAnalysisComplete={handleAnalysisComplete}
          onStepChange={setWorkflowStep}
        />
      </div>
    </div>
  )
}

export default App

