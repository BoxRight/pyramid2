import './Sidebar.css'

function Sidebar({ workflowStep, onStepChange, contracts, onContractSelect, onStartOver }) {
  const workflowSteps = [
    { id: 'generate', label: 'Generate', description: 'Create contract from natural language' },
    { id: 'review', label: 'Review', description: 'Review and compile contract' },
    { id: 'analyze', label: 'Analyze', description: 'View analysis results' },
    { id: 'query', label: 'Query', description: 'Query specific predicates' }
  ]

  const currentStepIndex = workflowSteps.findIndex(s => s.id === workflowStep)

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>LAML Contracts</h1>
        <p className="sidebar-subtitle">Legal Contract Analysis</p>
      </div>
      
      {/* Progressive Disclosure: Show workflow steps */}
      <div className="workflow-steps">
        <div className="sidebar-section-header">Workflow</div>
        {workflowSteps.map((step, index) => {
          const isActive = step.id === workflowStep
          const isCompleted = index < currentStepIndex
          const isAccessible = index <= currentStepIndex

          return (
            <button
              key={step.id}
              className={`workflow-step-item ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''} ${!isAccessible ? 'disabled' : ''}`}
              onClick={() => isAccessible && onStepChange(step.id)}
              disabled={!isAccessible}
              title={step.description}
            >
              <span className="workflow-step-number">{index + 1}</span>
              <div className="workflow-step-content">
                <span className="workflow-step-label">{step.label}</span>
              </div>
            </button>
          )
        })}
      </div>

    </div>
  )
}

export default Sidebar

