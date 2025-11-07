"""
Contract Compilation Service
Wraps lamlc binary execution - can be extracted to Lambda function: laml-compiler
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Path to lamlc binary (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
LAMLC_BINARY = PROJECT_ROOT / "lamlc"
LAWS_DIR = PROJECT_ROOT / "laws"
PRINCIPLES_DIR = PROJECT_ROOT / "principles"


async def compile_laml_contract(
    contract_id: str,
    laml_content: str,
    storage: Any  # LocalStorage instance
) -> Dict[str, Any]:
    """
    Compile LAML contract to AST JSON.
    
    In Lambda, this would:
    1. Download LAML from S3
    2. Execute lamlc binary (from Lambda Layer)
    3. Upload AST JSON to S3
    4. Return metadata
    
    Args:
        contract_id: Contract identifier
        laml_content: LAML source code
        storage: Storage instance (LocalStorage or S3)
    
    Returns:
        Dict with compiled AST data and metadata
    """
    
    # Create temporary file in contracts directory so imports resolve correctly
    # lamlc resolves imports relative to the contract file location
    contracts_dir = PROJECT_ROOT / "contracts"
    contracts_dir.mkdir(exist_ok=True)
    
    # Use a temporary filename in contracts directory
    laml_file = contracts_dir / f"{contract_id}.laml"
    ast_output_file = contracts_dir / f"{contract_id}_ast.json"
    
    # Initialize cleanup tracking variables (for finally block)
    # Store original paths for cleanup (they may be reassigned in try block)
    original_ast_file = ast_output_file
    result_files = []
    combined_file = None
    
    try:
        # Write LAML content to contracts directory
        with open(laml_file, 'w', encoding='utf-8') as f:
            f.write(laml_content)
        
        # Execute lamlc compiler from project root
        # Use relative path from project root
        rel_laml_path = os.path.relpath(laml_file, PROJECT_ROOT)
        
        # Generate AST JSON (hierarchical structure for contract parser)
        # ast_output_file already initialized above for cleanup
        rel_ast_path = os.path.relpath(ast_output_file, PROJECT_ROOT)
        
        # Execute lamlc compiler
        # Note: -o flag doesn't actually work - lamlc generates laml_results_*.json automatically
        # We use --ast-json to generate the hierarchical AST structure
        # We use -c (cascade) to get execution order metadata for component dependencies
        result = subprocess.run(
            [
                str(LAMLC_BINARY),
                rel_laml_path,
                "--ast-json", rel_ast_path,
                "-c"  # Cascade: include results from dependent institutions (via directObject)
                # Results files (laml_results_*.json) are automatically generated in project root
                # Cascade also generates laml_results_combined.json with execution metadata
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            raise Exception(f"Compilation failed: {result.stderr}")
        
        # lamlc generates multiple files: laml_results_{instance_name}.json
        # With -c flag, also generates laml_results_combined.json (metadata)
        # Find ALL generated result files (components + final contract)
        all_result_files = list(PROJECT_ROOT.glob("laml_results_*.json"))
        
        if not all_result_files:
            raise Exception(f"Compilation succeeded but no result files generated")
        
        # Separate combined metadata from actual result files
        # Store in variables initialized before try block for cleanup
        combined_file = PROJECT_ROOT / "laml_results_combined.json"
        result_files = [f for f in all_result_files if f.name != "laml_results_combined.json"]
        
        # Load cascade metadata if available
        cascade_metadata = None
        execution_order = None
        if combined_file.exists():
            try:
                with open(combined_file, 'r', encoding='utf-8') as f:
                    cascade_metadata = json.load(f)
                    # Extract execution order from cascade metadata
                    executions = cascade_metadata.get("executions", [])
                    execution_order = [e["instance"] for e in executions]
                    # Create mapping from instance name to file
                    instance_to_file = {e["instance"]: e["results_file"] for e in executions}
            except Exception as e:
                print(f"Warning: Could not load cascade metadata: {e}")
        
        # Sort by modification time to get execution order (components first, final last)
        # But prefer cascade metadata order if available
        result_files.sort(key=lambda x: x.stat().st_mtime)
        
        # Load all component and final contract results
        component_results = {}
        final_contract_result = None
        
        for result_file in result_files:
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            # Extract instance name from filename
            instance_name = result_file.stem.replace('laml_results_', '')
            
            # Store component result
            # Use absolute path for file reference
            component_results[instance_name] = {
                "file": str(result_file.absolute()),
                "data": result_data,
                "instance_name": instance_name,
                "num_solutions": result_data.get("num_solutions", 0),
                "satisfiable": result_data.get("satisfiable", False)
            }
            
            # Last file is typically the final composite contract (authoritative)
            final_contract_result = result_file
        
        # The final contract is the last execution (authoritative solution space)
        final_contract_file = result_files[-1]
        final_instance_name = final_contract_file.stem.replace('laml_results_', '')
        
        with open(final_contract_file, 'r', encoding='utf-8') as f:
            final_results_data = json.load(f)
        
        # Load AST JSON (hierarchical structure for contract parser)
        # Check both relative and absolute paths
        if not ast_output_file.exists():
            # Try absolute path
            abs_ast_path = PROJECT_ROOT / rel_ast_path
            if abs_ast_path.exists():
                ast_output_file = abs_ast_path
            else:
                raise Exception(f"AST file not generated: {ast_output_file}")
        
        # Read AST data from temporary file
        with open(ast_output_file, 'r', encoding='utf-8') as f:
            ast_data = json.load(f)
        
        # Save AST to persistent storage (data/compiled/ast/)
        # This is the file that will be used for parsing and rendering
        ast_file_path = storage.save_compiled_ast(contract_id, ast_data)
        
        # Verify the saved file exists before proceeding
        saved_ast_path = Path(ast_file_path)
        if not saved_ast_path.exists():
            raise Exception(f"Failed to save AST file to storage: {ast_file_path}")
        
        print(f"✅ AST saved to persistent storage: {ast_file_path}")
        
        # Save results (solver output) to storage
        results_file_path = storage.save_compiled_results(contract_id, final_results_data, final_instance_name)
        
        # Save component results metadata
        storage.save_component_results(contract_id, component_results, final_instance_name)
        
        # Save cascade metadata if available
        if cascade_metadata:
            storage.save_cascade_metadata(contract_id, cascade_metadata)
        
        # Invalidate query cache when contract is recompiled
        # (Old cached queries may be invalid)
        storage.invalidate_contract_cache(contract_id)
        
        return {
            "contract_id": contract_id,
            "ast_file": ast_file_path,  # AST (hierarchical structure)
            "results_file": results_file_path,  # Results (solver output)
            "final_instance_name": final_instance_name,
            "compiled_at": datetime.utcnow().isoformat(),
            "num_solutions": final_results_data.get("num_solutions", 0),
            "satisfiable": final_results_data.get("satisfiable", False),
            "components": {
                name: {
                    "instance_name": name,
                    "num_solutions": comp["num_solutions"],
                    "satisfiable": comp["satisfiable"]
                }
                for name, comp in component_results.items()
            },
            "ast_data": ast_data,  # AST (hierarchical)
            "results_data": final_results_data,  # Results (solver output)
            "cascade_metadata": cascade_metadata,  # Execution order metadata (if cascade flag used)
            "execution_order": execution_order  # Ordered list of instance names (if cascade flag used)
        }
        
    except subprocess.TimeoutExpired:
        raise Exception("Compilation timeout (exceeded 5 minutes)")
    except FileNotFoundError:
        raise Exception(f"lamlc binary not found at {LAMLC_BINARY}")
    except Exception as e:
        raise Exception(f"Compilation error: {str(e)}")
    finally:
        # Automatic cleanup of all temporary files
        # Critical for serverless architecture (Lambda ephemeral filesystem)
        # Variables are initialized before try block so they're always in scope
        
        # 1. Clean up temporary LAML file in contracts/ folder
        try:
            if laml_file.exists():
                laml_file.unlink()
                print(f"🧹 Cleaned up temporary LAML file: {laml_file.name}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up LAML file {laml_file}: {e}")
        
        # 2. Clean up temporary AST file in contracts/ folder (already saved to data/compiled/ast/)
        # Use original path (may have been reassigned in try block)
        try:
            # Try original path first
            if original_ast_file.exists():
                original_ast_file.unlink()
                print(f"🧹 Cleaned up temporary AST file: {original_ast_file.name}")
            # Also try the ast_output_file variable in case it's different
            elif 'ast_output_file' in locals() and ast_output_file != original_ast_file and ast_output_file.exists():
                ast_output_file.unlink()
                print(f"🧹 Cleaned up temporary AST file: {ast_output_file.name}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up AST file: {e}")
        
        # 3. Clean up all laml_results_*.json files in project root
        # (These are already saved to data/compiled/results/ for long-term storage)
        try:
            for result_file in result_files:
                try:
                    if result_file.exists():
                        result_file.unlink()
                        print(f"🧹 Cleaned up result file: {result_file.name}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not clean up result file {result_file}: {e}")
        except Exception as e:
            print(f"⚠️  Warning: Error cleaning up result files: {e}")
        
        # 4. Clean up cascade metadata file
        try:
            if combined_file and combined_file.exists():
                combined_file.unlink()
                print(f"🧹 Cleaned up cascade metadata: {combined_file.name}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up cascade metadata: {e}")
        
        # 5. Safety net: Clean up ANY remaining laml_results_*.json files in project root
        # This catches files that might have been created but not tracked
        try:
            all_remaining = list(PROJECT_ROOT.glob("laml_results_*.json"))
            for f in all_remaining:
                try:
                    if f.exists():
                        f.unlink()
                        print(f"🧹 Cleaned up remaining result file: {f.name}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not clean up {f.name}: {e}")
        except Exception as e:
            print(f"⚠️  Warning: Error in final cleanup pass: {e}")
        
        # 6. Safety net: Clean up ANY remaining AST files in contracts/ folder for this contract
        try:
            contract_ast_files = list(contracts_dir.glob(f"{contract_id}_ast.json"))
            for f in contract_ast_files:
                try:
                    if f.exists():
                        f.unlink()
                        print(f"🧹 Cleaned up remaining AST file: {f.name}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not clean up AST file {f.name}: {e}")
        except Exception as e:
            print(f"⚠️  Warning: Error cleaning up contract AST files: {e}")
        
        # 7. Final safety net: Clean up ALL _ast.json files in contracts/ folder
        # This is aggressive but necessary for serverless - no temporary files should persist
        try:
            all_ast_files = list(contracts_dir.glob("*_ast.json"))
            if all_ast_files:
                print(f"⚠️  Found {len(all_ast_files)} remaining AST files in contracts/ - cleaning up")
                for f in all_ast_files:
                    try:
                        if f.exists():
                            f.unlink()
                            print(f"🧹 Cleaned up remaining AST file: {f.name}")
                    except Exception as e:
                        print(f"⚠️  Warning: Could not clean up {f.name}: {e}")
        except Exception as e:
            print(f"⚠️  Warning: Error in final AST cleanup: {e}")

