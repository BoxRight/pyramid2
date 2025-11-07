import { useState } from 'react'
import './NaturalLanguageInput.css'
import { generateLAMLFromNaturalLanguage } from '../services/api'
import MockDataIndicator from './MockDataIndicator'

function NaturalLanguageInput({ onContractGenerated }) {
  const [naturalLanguage, setNaturalLanguage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const exampleQueries = [
    "Create a solar lease contract between SolarCorp and HomeOwner. The monthly rent is $200. Include maintenance obligations and return conditions.",
    "I need a lease agreement for a solar panel system. The lessor is EnergyCompany and the lessee is PropertyOwner. Rent is $150 per month.",
    "Generate a contract for leasing solar equipment with a 5-year term and $300 monthly payment."
  ].map(example => ({
    text: example,
    label: example.length > 80 ? example.substring(0, 80) + '...' : example
  }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!naturalLanguage.trim()) {
      setError('Please enter a contract description')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      // Auto-detect contract type and use default jurisdiction
      const result = await generateLAMLFromNaturalLanguage({
        natural_language: naturalLanguage,
        contract_type: 'solar_lease', // Auto-detect from description
        jurisdiction: 'Mexico', // Default
        auto_compile: false
      })

      setSuccess('Contract generated successfully! Using mock data for demonstration.')
      onContractGenerated(result)
      // Keep input for user to see what was used
      // setNaturalLanguage('') // Clear input
    } catch (err) {
      setError(err.message || 'Failed to generate contract')
    } finally {
      setLoading(false)
    }
  }

  const handleExampleClick = (example) => {
    setNaturalLanguage(example.text || example)
  }

  return (
    <div className="natural-language-input">
      <div className="view-header">
        <h2>Create Contract</h2>
      </div>

      <div className="view-content">
        <div className="nl-input-container">
          {import.meta.env.VITE_USE_MOCK_DATA !== 'false' && <MockDataIndicator />}
          <form onSubmit={handleSubmit} className="nl-form">
            <div className="form-group">
              <label htmlFor="natural-language">Describe Your Contract</label>
              <textarea
                id="natural-language"
                value={naturalLanguage}
                onChange={(e) => setNaturalLanguage(e.target.value)}
                placeholder="Describe your contract in plain language. For example: 'Create a solar lease between SolarCorp and HomeOwner with $200 monthly rent, including maintenance obligations and return conditions.'"
                rows={8}
                required
              />
              <div className="input-hint">
                Include: parties, obligations, terms, and any specific requirements
              </div>
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {success && (
              <div className="success-message">
                {success}
              </div>
            )}

            <button 
              type="submit" 
              className="submit-button"
              disabled={loading || !naturalLanguage.trim()}
            >
              {loading ? (
                <>
                  <span className="loading-spinner"></span>
                  Generating LAML...
                </>
              ) : (
                'Generate Contract'
              )}
            </button>
          </form>

          <div className="examples-section">
            <h3>Example Queries</h3>
            <div className="examples-list">
              {exampleQueries.map((example, index) => (
                <button
                  key={index}
                  className="example-button"
                  onClick={() => handleExampleClick(example)}
                  type="button"
                >
                  <span className="example-text">{example.label || example.text || example}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NaturalLanguageInput

