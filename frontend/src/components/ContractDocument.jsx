import './ContractDocument.css'

function ContractDocument({ contractData }) {
  console.log('📄 ContractDocument rendered with:', {
    has_contractData: !!contractData,
    contractData_type: typeof contractData,
    contractData_keys: contractData ? Object.keys(contractData) : []
  })
  
  if (!contractData) {
    console.warn('⚠️ ContractDocument: No contractData provided')
    return (
      <div className="contract-document empty">
        <div className="empty-state">
          <div className="empty-state-title">No Contract Document</div>
          <div className="empty-state-description">
            Compile a contract to see the legal document
          </div>
        </div>
      </div>
    )
  }

  const { metadata, parties_block, objects_section, declarations_section, clauses_section, final_section } = contractData || {}
  
  console.log('📄 ContractDocument data structure:', {
    has_metadata: !!metadata,
    has_parties_block: !!parties_block,
    has_clauses_section: !!clauses_section,
    clauses_section_type: Array.isArray(clauses_section) ? 'array' : typeof clauses_section,
    clauses_count: Array.isArray(clauses_section) ? clauses_section.length : (clauses_section?.clauses?.length || 0)
  })

  return (
    <div className="contract-document">
      <div className="contract-content">
        {/* Title */}
        <div className="contract-title">
          {metadata?.title || 'CONTRATO LEGAL'}
        </div>

        {/* Normativa */}
        {metadata?.normativa && metadata.normativa.length > 0 && (
          <div className="contract-normativa">
            <p><strong>Normativa:</strong> {metadata.normativa.join(', ')}</p>
          </div>
        )}

        {/* Supuesto */}
        {metadata?.supuesto && (
          <div className="contract-supuesto">
            <p><strong>Supuesto:</strong> {metadata.supuesto}</p>
          </div>
        )}

        {/* Opening statement */}
        <div className="contract-opening">
          <p>CONTRATO QUE CONSTITUYEN {parties_block?.parties?.map(p => p.name?.toUpperCase()).join(', ') || 'LAS PARTES'}, SUJETÁNDOSE PARA ELLO LA TENOR DE LAS SIGUIENTES DECLARACIONES Y CLÁUSULAS:</p>
        </div>

        {/* Objects Section */}
        {objects_section && objects_section.objects && objects_section.objects.length > 0 && (
          <div className="contract-section">
            <div className="section-title">OBJETOS</div>
            {objects_section.objects.map((obj, index) => (
              <div key={index} className="object-item">
                {getRomanNumeral(index + 1)}.- <strong>{obj.name?.toUpperCase()}</strong>.- {obj.description || `objeto denominado ${obj.name?.toLowerCase()}`}
              </div>
            ))}
          </div>
        )}

        {/* Declarations Section */}
        {declarations_section && declarations_section.declarations && declarations_section.declarations.length > 0 && (
          <div className="contract-section">
            <div className="section-title">DECLARACIONES</div>
            {declarations_section.declarations.map((declaration, index) => (
              <div key={index} className="declaration">
                <div className="declaration-title">
                  {getRomanNumeral(index + 1)}.-- Declara "{declaration.party}":
                </div>
                {declaration.items && declaration.items.map((item, itemIndex) => (
                  <div key={itemIndex} className="declaration-item">
                    {String.fromCharCode(97 + itemIndex)}. {item}
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}

        {/* Clauses Section */}
        {(() => {
          const clauses = Array.isArray(clauses_section) 
            ? clauses_section 
            : (clauses_section?.clauses || [])
          
          if (clauses.length === 0) return null
          
          return (
            <div className="contract-section">
              <div className="section-title">CLÁUSULAS</div>
              {clauses.map((clause, index) => (
                <div key={index} className="clause">
                  <span className="clause-id">
                    Cláusula {index + 1}.- {clause.title || clause.type?.toUpperCase()}.-
                  </span>{' '}
                  {clause.content}
                </div>
              ))}
            </div>
          )
        })()}

        {/* Final Section */}
        {final_section && (
          <div className="contract-section">
            {final_section.clauses && final_section.clauses.map((clause, index) => {
              // Calculate clause number based on existing clauses
              const existingClausesCount = Array.isArray(clauses_section) 
                ? clauses_section.length 
                : (clauses_section?.clauses?.length || 0)
              
              return (
                <div key={index} className="clause">
                  <span className="clause-id">
                    Cláusula {existingClausesCount + index + 1}.- {clause.title}.-
                  </span>{' '}
                  {clause.content}
                </div>
              )
            })}

            {/* Signatures */}
            {final_section.signatures && (
              <div className="signature-section">
                <p>{final_section.signatures.text || 'Así convenido y sabedores del valor, fuerza y alcance legales del contenido de este contrato, las partes lo firman por duplicado a los _____ días del mes de _____.'}</p>
                <br />
                {final_section.signatures.parties && final_section.signatures.parties.map((party, index) => (
                  <div key={index}>
                    <div className="signature-line">EL {party.toUpperCase()}</div>
                    <br />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Helper function to convert numbers to Roman numerals
function getRomanNumeral(num) {
  const values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
  const symbols = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
  
  let result = ''
  for (let i = 0; i < values.length; i++) {
    const count = Math.floor(num / values[i])
    if (count > 0) {
      result += symbols[i].repeat(count)
      num -= values[i] * count
    }
  }
  return result
}

export default ContractDocument

