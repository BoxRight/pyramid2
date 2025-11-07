import { useMemo } from 'react'
import './ContractVisualization.css'

function ContractVisualization({ lamlCode, highlightedElement, onElementClick, onElementHover }) {
  // Parse LAML to extract structure for visualization
  const contractStructure = useMemo(() => {
    if (!lamlCode) return null

    // Simple parser to extract key elements
    const structure = {
      institution: null,
      parties: [],
      objects: [],
      predicates: [],
      rules: []
    }

    // Extract institution
    const institutionMatch = lamlCode.match(/institution\(([^)]+)\)/)
    if (institutionMatch) {
      structure.institution = institutionMatch[1].split(',').map(s => s.trim())
    }

    // Extract parties (Person bindings)
    const partyMatches = lamlCode.matchAll(/(\w+)\((\w+)\)\s*=\s*Person\([^)]+\)/g)
    for (const match of partyMatches) {
      structure.parties.push({ name: match[1], variable: match[2] })
    }

    // Extract objects (Thing bindings)
    const objectMatches = lamlCode.matchAll(/(\w+)\((\w+)\)\s*=\s*Thing\([^)]+\)/g)
    for (const match of objectMatches) {
      structure.objects.push({ name: match[1], variable: match[2] })
    }

    // Extract predicates (acts)
    const predicateMatches = lamlCode.matchAll(/(\w+)\(([^)]+)\)\s*=\s*[^;]+/g)
    for (const match of predicateMatches) {
      if (!match[1].startsWith('rule_')) {
        structure.predicates.push({
          name: match[1],
          params: match[2].split(',').map(s => s.trim())
        })
      }
    }

    // Extract rules
    const ruleMatches = lamlCode.matchAll(/rule_(\w+)\s*=\s*([^;]+)/g)
    for (const match of ruleMatches) {
      structure.rules.push({
        name: match[1],
        definition: match[2].trim()
      })
    }

    return structure
  }, [lamlCode])

  if (!contractStructure || !lamlCode) {
    return (
      <div className="contract-visualization empty">
        <div className="empty-state">
          <div className="empty-state-title">No Contract Loaded</div>
          <div className="empty-state-description">
            Compile a contract to see its visual structure
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="contract-visualization">
      <div className="visual-content">
        {/* Institution Node */}
        {contractStructure.institution && (
          <div className="visual-node institution-node">
            <div className="node-header">Institution</div>
            <div className="node-content">
              {contractStructure.institution.map((param, idx) => (
                <span key={idx} className="node-param">{param}</span>
              ))}
            </div>
          </div>
        )}

        {/* Parties */}
        {contractStructure.parties.length > 0 && (
          <div className="visual-group">
            <div className="group-title">Parties</div>
            <div className="group-content">
              {contractStructure.parties.map((party, idx) => (
                <div
                  key={idx}
                  className={`visual-node party-node ${highlightedElement === `party-${party.name}` ? 'highlighted' : ''}`}
                  onMouseEnter={() => onElementHover?.(`party-${party.name}`)}
                  onMouseLeave={() => onElementHover?.(null)}
                  onClick={() => onElementClick?.(`party-${party.name}`)}
                >
                  <div className="node-name">{party.name}</div>
                  <div className="node-variable">{party.variable}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Objects */}
        {contractStructure.objects.length > 0 && (
          <div className="visual-group">
            <div className="group-title">Objects</div>
            <div className="group-content">
              {contractStructure.objects.map((obj, idx) => (
                <div
                  key={idx}
                  className={`visual-node object-node ${highlightedElement === `object-${obj.name}` ? 'highlighted' : ''}`}
                  onMouseEnter={() => onElementHover?.(`object-${obj.name}`)}
                  onMouseLeave={() => onElementHover?.(null)}
                  onClick={() => onElementClick?.(`object-${obj.name}`)}
                >
                  <div className="node-name">{obj.name}</div>
                  <div className="node-variable">{obj.variable}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Predicates */}
        {contractStructure.predicates.length > 0 && (
          <div className="visual-group">
            <div className="group-title">Predicates (Acts)</div>
            <div className="group-content">
              {contractStructure.predicates.map((pred, idx) => (
                <div
                  key={idx}
                  className={`visual-node predicate-node ${highlightedElement === `predicate-${pred.name}` ? 'highlighted' : ''}`}
                  onMouseEnter={() => onElementHover?.(`predicate-${pred.name}`)}
                  onMouseLeave={() => onElementHover?.(null)}
                  onClick={() => onElementClick?.(`predicate-${pred.name}`)}
                >
                  <div className="node-name">{pred.name}</div>
                  <div className="node-params">
                    {pred.params.join(', ')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Rules */}
        {contractStructure.rules.length > 0 && (
          <div className="visual-group">
            <div className="group-title">Rules</div>
            <div className="group-content">
              {contractStructure.rules.map((rule, idx) => (
                <div
                  key={idx}
                  className={`visual-node rule-node ${highlightedElement === `rule-${rule.name}` ? 'highlighted' : ''}`}
                  onMouseEnter={() => onElementHover?.(`rule-${rule.name}`)}
                  onMouseLeave={() => onElementHover?.(null)}
                  onClick={() => onElementClick?.(`rule-${rule.name}`)}
                >
                  <div className="node-name">{rule.name}</div>
                  <div className="node-definition">{rule.definition.substring(0, 50)}...</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ContractVisualization

