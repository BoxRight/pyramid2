"""
FastAPI Development Server for LAML Legal Contract System
Designed with serverless architecture in mind - functions can be extracted to Lambda
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import sys

# Add project root to path for imports
from pathlib import Path
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.contract_compiler import compile_laml_contract
from backend.services.contract_analyzer import analyze_contract
from backend.services.contract_query import query_contract_predicate
from backend.services.nl_to_laml import generate_laml_from_natural_language
from backend.services.contract_renderer import render_contract_html
from backend.storage.local_storage import LocalStorage

app = FastAPI(
    title="LAML Contract API",
    description="Legal Contract Analysis System API",
    version="1.0.0"
)

# CORS middleware for frontend
# Allow frontend on port 3000 (Vite dev server) and any other common ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Alternative Vite port
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage
storage = LocalStorage()

# Request/Response Models
class GenerateNLRequest(BaseModel):
    natural_language: Optional[str] = None  # Optional for now (using existing contracts)
    contract_type: Optional[str] = "solar_lease"
    jurisdiction: Optional[str] = "Mexico"
    additional_context: Optional[Dict[str, Any]] = {}
    auto_compile: Optional[bool] = False
    contract_source: Optional[str] = None  # Optional: specify contract file to use (e.g., "solar_lease_simple.laml")

class CompileRequest(BaseModel):
    contract_id: str
    laml_content: str

class QueryRequest(BaseModel):
    contract_id: str
    predicate_name: str
    query_type: str  # "violation" or "fulfillment"
    instance_name: Optional[str] = None  # Optional: query specific component

class ContractResponse(BaseModel):
    contract_id: str
    status: str
    message: Optional[str] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "LAML Contract API",
        "version": "1.0.0"
    }

@app.post("/contracts/generate-from-nl")
async def generate_from_natural_language(request: GenerateNLRequest):
    """
    Generate LAML contract from natural language input.
    
    TEMPORARY: Currently loads from existing contracts in contracts/ folder.
    TODO: Re-enable Anthropic API for natural language generation.
    
    This endpoint will be a Lambda function: nl-to-laml-generator
    """
    try:
        # TEMPORARY: Load from existing contracts instead of NL generation
        # Use specified contract source or default to solar_lease_simple.laml
        contract_source = request.contract_source or "solar_lease_simple.laml"
        
        # Load contract from contracts/ folder
        contracts_dir = PROJECT_ROOT / "contracts"
        contract_file = contracts_dir / contract_source
        
        if not contract_file.exists():
            # Try to find any .laml file in contracts directory
            available_contracts = list(contracts_dir.glob("*.laml"))
            if available_contracts:
                contract_file = available_contracts[0]
                contract_source = contract_file.name
            else:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Contract file not found: {contract_source}. Available contracts: {[f.name for f in contracts_dir.glob('*.laml')]}"
                )
        
        # Read LAML content
        with open(contract_file, 'r', encoding='utf-8') as f:
            laml_content = f.read()
        
        # Generate contract ID
        import uuid
        contract_id = f"nl-generated-{uuid.uuid4().hex[:8]}"
        
        # Save contract to storage
        contract_id = storage.save_contract(
            contract_id=contract_id,
            laml_content=laml_content,
            contract_type=request.contract_type,
            metadata={
                "source": "existing_contract",
                "contract_file": contract_source,
                "jurisdiction": request.jurisdiction,
                "note": "Temporary: Using existing contract instead of NL generation"
            }
        )
        
        # Basic validation (same as before)
        validation_errors = []
        if 'institution(' not in laml_content:
            validation_errors.append("Missing institution() definition")
        
        return {
            "contract_id": contract_id,
            "laml_content": laml_content,
            "status": "generated",
            "validation_errors": validation_errors,
            "compilation_triggered": request.auto_compile,
            "source": f"existing_contract: {contract_source}"
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"Error in generate_from_natural_language: {error_detail}")  # Log to console
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/contracts/compile")
async def compile_contract(request: CompileRequest):
    """
    Compile LAML contract to AST JSON.
    This endpoint will be a Lambda function: laml-compiler
    """
    try:
        # Save LAML content first if not already saved
        if not storage.contract_exists(request.contract_id):
            storage.save_contract(
                contract_id=request.contract_id,
                laml_content=request.laml_content,
                contract_type="unknown"
            )
        
        # Compile contract
        result = await compile_laml_contract(
            contract_id=request.contract_id,
            laml_content=request.laml_content,
            storage=storage
        )
        
        # Parse contract for display (using AST contract parser)
        # AST file contains hierarchical structure, not results!
        # IMPORTANT: Use the AST file from data/compiled/ast/ (persistent storage), NOT from contracts/ (temporary)
        parsed_contract = None
        if result.get("ast_file"):
            try:
                from backend.lib.ast_contract_parser import ASTContractParser
                
                # The ast_file_path from result should be the path in data/compiled/ast/
                # This is the persistent storage, not the temporary file in contracts/
                ast_file_path = result["ast_file"]
                
                # Handle both absolute and relative paths
                if isinstance(ast_file_path, str):
                    # First, try relative to storage base_dir (data/)
                    storage_path = storage.base_dir / ast_file_path
                    if storage_path.exists():
                        ast_file_path = storage_path
                    elif Path(ast_file_path).is_absolute() and Path(ast_file_path).exists():
                        ast_file_path = Path(ast_file_path)
                    else:
                        # Try relative to project root as last resort
                        ast_file_path = PROJECT_ROOT / ast_file_path
                else:
                    ast_file_path = Path(ast_file_path)
                
                # Verify file exists before parsing
                if not ast_file_path.exists():
                    # Try to get from metadata as fallback
                    if request.contract_id in storage.metadata:
                        meta_ast_path = storage.metadata[request.contract_id].get("s3_ast_path")
                        if meta_ast_path:
                            meta_path = storage.base_dir / meta_ast_path
                            if meta_path.exists():
                                ast_file_path = meta_path
                                print(f"📄 Using AST path from metadata: {ast_file_path}")
                    
                    if not ast_file_path.exists():
                        raise FileNotFoundError(f"AST file not found at {ast_file_path} (tried: {result.get('ast_file')})")
                
                print(f"📄 Parsing contract from AST file: {ast_file_path}")
                print(f"   File exists: {ast_file_path.exists()}")
                if ast_file_path.exists():
                    print(f"   File size: {ast_file_path.stat().st_size} bytes")
                
                parser = ASTContractParser(str(ast_file_path), use_api_improvement=False)
                parsed_contract = parser.parse_contract()
                
                # Verify parsing succeeded
                clauses = parsed_contract.get('clauses_section', {})
                if isinstance(clauses, dict):
                    clauses = clauses.get('clauses', [])
                elif isinstance(clauses, list):
                    pass
                else:
                    clauses = []
                
                print(f"✅ Successfully parsed contract: {len(clauses)} clauses")
            except Exception as e:
                import traceback
                print(f"❌ Warning: Could not parse contract: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                parsed_contract = None
        
        response_data = {
            "contract_id": request.contract_id,
            "status": "compiled",
            "compiled_at": result.get("compiled_at"),
            "s3_ast_path": result.get("ast_file"),  # For compatibility (final contract)
            "parsed_contract": parsed_contract,  # This is what frontend needs for document display
            "num_solutions": result.get("num_solutions"),  # Final contract solutions (authoritative)
            "satisfiable": result.get("satisfiable"),
            "final_instance_name": result.get("final_instance_name"),
            "components": result.get("components", {})  # Component metadata
        }
        
        # Log if parsed_contract is missing (for debugging)
        if not parsed_contract:
            print(f"⚠️  Warning: parsed_contract is None for contract {request.contract_id}")
            print(f"   AST file path: {result.get('ast_file')}")
            print(f"   AST file exists: {Path(result.get('ast_file', '')).exists() if result.get('ast_file') else False}")
        
        return response_data
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"Error in compile_contract: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contracts/{contract_id}/analysis")
async def get_contract_analysis(contract_id: str, instance_name: Optional[str] = None):
    """
    Get violation/fulfillment analysis for a contract.
    By default analyzes final contract (authoritative). 
    Can analyze specific component by passing instance_name query parameter.
    This endpoint will be a Lambda function: laml-analyzer
    """
    try:
        result = await analyze_contract(
            contract_id=contract_id,
            storage=storage,
            instance_name=instance_name  # None = final contract, name = specific component
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/contracts/query")
async def query_contract(request: QueryRequest):
    """
    Query contract for violation/fulfillment consequences.
    By default queries final contract (authoritative).
    Can query specific component by passing instance_name.
    This endpoint will be a Lambda function: laml-query
    """
    try:
        result = await query_contract_predicate(
            contract_id=request.contract_id,
            predicate_name=request.predicate_name,
            query_type=request.query_type,
            storage=storage,
            instance_name=request.instance_name  # None = final contract, name = specific component
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contracts/{contract_id}/html")
async def get_contract_html(contract_id: str):
    """
    Get rendered HTML contract.
    This endpoint will be a Lambda function: contract-renderer
    """
    try:
        html_content = await render_contract_html(
            contract_id=contract_id,
            storage=storage
        )
        return {"html": html_content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/contracts")
async def list_contracts():
    """List all contracts"""
    try:
        contracts = storage.list_contracts()
        return {"contracts": contracts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

