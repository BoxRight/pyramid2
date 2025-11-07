import axios from 'axios'
import { 
  MOCK_GENERATED_CONTRACT, 
  MOCK_ANALYSIS_RESULTS, 
  MOCK_QUERY_RESULTS,
  simulateDelay 
} from './mockData'

// Base URL - will be configured based on environment
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

// Use mock data when API is not available (development mode)
// Check environment variable - must be explicitly 'false' to disable mock data
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA !== 'false' // Default to true

// Debug logging
console.log('🔧 API Configuration:')
console.log('  VITE_USE_MOCK_DATA:', import.meta.env.VITE_USE_MOCK_DATA)
console.log('  USE_MOCK_DATA:', USE_MOCK_DATA)
console.log('  API_BASE_URL:', API_BASE_URL)

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Natural Language to LAML Generation
export async function generateLAMLFromNaturalLanguage(data) {
  if (USE_MOCK_DATA) {
    await simulateDelay(1500) // Simulate API delay
    return {
      ...MOCK_GENERATED_CONTRACT,
      contract_id: `contract-${Date.now()}`,
      contract_type: data.contract_type || 'solar_lease',
      jurisdiction: data.jurisdiction || 'Mexico'
    }
  }

  try {
    const response = await api.post('/contracts/generate-from-nl', data)
    return response.data
  } catch (error) {
    // Fallback to mock data if API fails
    if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      console.warn('API unavailable, using mock data')
      await simulateDelay(1500)
      return {
        ...MOCK_GENERATED_CONTRACT,
        contract_id: `contract-${Date.now()}`,
        contract_type: data.contract_type || 'solar_lease',
        jurisdiction: data.jurisdiction || 'Mexico'
      }
    }
    throw new Error(error.response?.data?.error || 'Failed to generate LAML contract')
  }
}

// Compile Contract
export async function compileContract(data) {
  if (USE_MOCK_DATA) {
    console.log('⚠️ Using MOCK DATA for compile (USE_MOCK_DATA=true)')
    await simulateDelay(2000) // Simulate compilation delay
    // Import parsed contract from mock data
    const { MOCK_PARSED_CONTRACT } = await import('./mockData')
    return {
      contract_id: data.contract_id,
      status: 'compiled',
      compiled_at: new Date().toISOString(),
      s3_ast_path: `compiled/ast/${data.contract_id}.json`,
      parsed_contract: MOCK_PARSED_CONTRACT // Include parsed contract document
    }
  }

  console.log('✅ Using REAL API for compile')
  try {
    const response = await api.post('/contracts/compile', data)
    console.log('📦 Compile response:', {
      contract_id: response.data.contract_id,
      has_parsed_contract: !!response.data.parsed_contract,
      parsed_contract_keys: response.data.parsed_contract ? Object.keys(response.data.parsed_contract) : []
    })
    return response.data
  } catch (error) {
    console.error('❌ Compile API error:', error)
    if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      console.warn('API unavailable, using mock data')
      await simulateDelay(2000)
      return {
        contract_id: data.contract_id,
        status: 'compiled',
        compiled_at: new Date().toISOString(),
        s3_ast_path: `compiled/ast/${data.contract_id}.json`
      }
    }
    throw new Error(error.response?.data?.error || 'Failed to compile contract')
  }
}

// Analyze Contract
export async function analyzeContract(data) {
  if (USE_MOCK_DATA) {
    console.log('⚠️ Using MOCK DATA for analysis (USE_MOCK_DATA=true)')
    await simulateDelay(2500) // Simulate analysis delay
    return {
      ...MOCK_ANALYSIS_RESULTS,
      contract_id: data.contract_id
    }
  }

  console.log('✅ Using REAL API for analysis')
  try {
    const response = await api.get(`/contracts/${data.contract_id}/analysis`)
    console.log('📊 Analysis response:', {
      contract_id: response.data.contract_id,
      num_predicates: response.data.num_predicates,
      total_solutions: response.data.total_solutions,
      violation_results_count: response.data.violation_results?.length || 0
    })
    return response.data
  } catch (error) {
    console.error('❌ Analysis API error:', error)
    if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      console.warn('API unavailable, using mock data')
      await simulateDelay(2500)
      return {
        ...MOCK_ANALYSIS_RESULTS,
        contract_id: data.contract_id
      }
    }
    throw new Error(error.response?.data?.error || 'Failed to analyze contract')
  }
}

// Query Contract
export async function queryContract(data) {
  if (USE_MOCK_DATA) {
    await simulateDelay(800) // Simulate query delay
    
    // Return appropriate mock result based on query type and predicate
    const key = `${data.predicate_name}_${data.query_type}`
    const mockResult = MOCK_QUERY_RESULTS[key]
    
    if (mockResult) {
      return mockResult
    }
    
    // Fallback for unknown predicates
    return {
      predicate: data.predicate_name,
      total_violation_scenarios: data.query_type === 'violation' ? 1 : 0,
      total_fulfillment_scenarios: data.query_type === 'fulfillment' ? 1 : 0,
      consequences: [],
      message: `Query executed for ${data.predicate_name} (${data.query_type})`
    }
  }

  try {
    const response = await api.post('/contracts/query', data)
    return response.data
  } catch (error) {
    if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      console.warn('API unavailable, using mock data')
      await simulateDelay(800)
      const key = `${data.predicate_name}_${data.query_type}`
      return MOCK_QUERY_RESULTS[key] || {
        predicate: data.predicate_name,
        total_violation_scenarios: 0,
        total_fulfillment_scenarios: 0,
        consequences: [],
        message: `Query executed for ${data.predicate_name} (${data.query_type})`
      }
    }
    throw new Error(error.response?.data?.error || 'Query failed')
  }
}

// Get Contract HTML
export async function getContractHTML(contractId) {
  try {
    const response = await api.get(`/contracts/${contractId}/html`)
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.error || 'Failed to get contract HTML')
  }
}

// List Contracts
export async function listContracts() {
  try {
    const response = await api.get('/contracts')
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.error || 'Failed to list contracts')
  }
}

export default api

