"""
Local Storage Layer - Mimics S3/DynamoDB structure for local development
This can be replaced with AWS services when deploying to Lambda
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

class LocalStorage:
    """
    Local file-based storage that mimics S3 bucket structure.
    In Lambda, this would be replaced with boto3 S3 and DynamoDB clients.
    """
    
    def __init__(self, base_dir: str = "data"):
        """Initialize local storage with directory structure"""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create S3-like directory structure
        self.dirs = {
            "source": self.base_dir / "source" / "contracts",
            "compiled_ast": self.base_dir / "compiled" / "ast",  # AST (hierarchical structure)
            "compiled_results": self.base_dir / "compiled" / "results",  # Solver results
            "analysis": self.base_dir / "analysis" / "results",
            "query_cache": self.base_dir / "query_cache",  # Query result cache (DynamoDB AnalysisResults)
            "generated": self.base_dir / "generated" / "html",
            "metadata": self.base_dir / "metadata"
        }
        
        # Create all directories
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Contracts metadata file (simulates DynamoDB Contracts table)
        self.metadata_file = self.base_dir / "contracts_metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load contracts metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save contracts metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def save_contract(self, contract_id: str, laml_content: str, 
                     contract_type: str, metadata: Optional[Dict] = None) -> str:
        """
        Save LAML contract to storage.
        In Lambda: s3.put_object(Bucket=bucket, Key=f"source/contracts/{contract_id}.laml", Body=laml_content)
        """
        # Generate contract ID if not provided
        if not contract_id or contract_id == "new-contract":
            contract_id = f"contract-{uuid.uuid4().hex[:8]}"
        
        # Save LAML file
        laml_file = self.dirs["source"] / f"{contract_id}.laml"
        with open(laml_file, 'w', encoding='utf-8') as f:
            f.write(laml_content)
        
        # Save metadata
        self.metadata[contract_id] = {
            "contract_id": contract_id,
            "contract_type": contract_type,
            "contract_name": contract_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending",
            "s3_laml_path": str(laml_file.relative_to(self.base_dir)),
            **(metadata or {})
        }
        self._save_metadata()
        
        return contract_id
    
    def get_contract(self, contract_id: str) -> Dict[str, Any]:
        """Get contract LAML content"""
        if contract_id not in self.metadata:
            raise FileNotFoundError(f"Contract {contract_id} not found")
        
        laml_path = self.base_dir / self.metadata[contract_id]["s3_laml_path"]
        if not laml_path.exists():
            raise FileNotFoundError(f"Contract file for {contract_id} not found")
        
        with open(laml_path, 'r', encoding='utf-8') as f:
            laml_content = f.read()
        
        return {
            "contract_id": contract_id,
            "laml_content": laml_content,
            **self.metadata[contract_id]
        }
    
    def contract_exists(self, contract_id: str) -> bool:
        """Check if contract exists"""
        return contract_id in self.metadata
    
    def save_compiled_ast(self, contract_id: str, ast_data: Dict[str, Any]) -> str:
        """
        Save compiled AST JSON (hierarchical structure for contract parser).
        In Lambda: s3.put_object(Bucket=bucket, Key=f"compiled/ast/{contract_id}.json", Body=json.dumps(ast_data))
        """
        ast_file = self.dirs["compiled_ast"] / f"{contract_id}.json"
        with open(ast_file, 'w', encoding='utf-8') as f:
            json.dump(ast_data, f, indent=2)
        
        # Update metadata
        if contract_id in self.metadata:
            self.metadata[contract_id]["compiled_at"] = datetime.utcnow().isoformat()
            self.metadata[contract_id]["status"] = "compiled"
            self.metadata[contract_id]["s3_ast_path"] = str(ast_file.relative_to(self.base_dir))
            self._save_metadata()
        
        return str(ast_file)
    
    def save_compiled_results(self, contract_id: str, results_data: Dict[str, Any], instance_name: str) -> str:
        """
        Save compiled results JSON (solver output for analysis).
        In Lambda: s3.put_object(Bucket=bucket, Key=f"compiled/results/{contract_id}_{instance_name}.json", Body=json.dumps(results_data))
        """
        results_file = self.dirs["compiled_results"] / f"{contract_id}_{instance_name}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2)
        
        # Update metadata
        if contract_id in self.metadata:
            self.metadata[contract_id]["s3_results_path"] = str(results_file.relative_to(self.base_dir))
            self.metadata[contract_id]["satisfiable"] = results_data.get("satisfiable", False)
            self.metadata[contract_id]["num_solutions"] = results_data.get("num_solutions", 0)
            self._save_metadata()
        
        return str(results_file)
    
    def get_compiled_ast(self, contract_id: str) -> Dict[str, Any]:
        """Get compiled AST JSON (hierarchical structure)"""
        if contract_id not in self.metadata:
            raise FileNotFoundError(f"Contract {contract_id} not found")
        
        ast_path = self.metadata[contract_id].get("s3_ast_path")
        if not ast_path:
            raise FileNotFoundError(f"Contract {contract_id} not compiled")
        
        ast_file = self.base_dir / ast_path
        with open(ast_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_compiled_results(self, contract_id: str, instance_name: str = None) -> Dict[str, Any]:
        """Get compiled results JSON (solver output)"""
        if contract_id not in self.metadata:
            raise FileNotFoundError(f"Contract {contract_id} not found")
        
        # If instance_name not provided, use final instance
        if not instance_name:
            instance_name = self.metadata[contract_id].get("final_instance_name")
            if not instance_name:
                raise FileNotFoundError(f"No final instance found for contract {contract_id}")
        
        # Try to find results file
        results_path = self.metadata[contract_id].get("s3_results_path")
        if results_path:
            results_file = self.base_dir / results_path
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # Fallback: try to load from component results
        components = self.metadata[contract_id].get("components", {})
        if instance_name in components:
            component_info = components[instance_name]
            component_file = Path(component_info["file"])
            if component_file.exists():
                with open(component_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        raise FileNotFoundError(f"Results for {instance_name} not found for contract {contract_id}")
    
    def save_component_results(self, contract_id: str, component_results: Dict[str, Any], final_instance_name: str):
        """
        Save component compilation results metadata.
        Components are prerequisites, final contract is authoritative.
        """
        if contract_id not in self.metadata:
            return
        
        self.metadata[contract_id]["components"] = component_results
        self.metadata[contract_id]["final_instance_name"] = final_instance_name
        self.metadata[contract_id]["num_components"] = len(component_results)
        self._save_metadata()
    
    def save_cascade_metadata(self, contract_id: str, cascade_metadata: Dict[str, Any]):
        """
        Save cascade execution metadata.
        Tracks execution order and component dependencies.
        """
        if contract_id not in self.metadata:
            return
        
        self.metadata[contract_id]["cascade_metadata"] = cascade_metadata
        executions = cascade_metadata.get("executions", [])
        self.metadata[contract_id]["execution_order"] = [e["instance"] for e in executions]
        self._save_metadata()
    
    def get_component_result(self, contract_id: str, instance_name: str) -> Dict[str, Any]:
        """Get a specific component's compilation result"""
        if contract_id not in self.metadata:
            raise FileNotFoundError(f"Contract {contract_id} not found")
        
        components = self.metadata[contract_id].get("components", {})
        if instance_name not in components:
            raise FileNotFoundError(f"Component {instance_name} not found for contract {contract_id}")
        
        component_info = components[instance_name]
        # Load the actual data from file (file path is absolute)
        component_file = Path(component_info["file"])
        if not component_file.exists():
            raise FileNotFoundError(f"Component file not found: {component_file}")
        
        with open(component_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_analysis_results(self, contract_id: str, analysis_data: Dict[str, Any]) -> str:
        """
        Save analysis results.
        In Lambda: s3.put_object(Bucket=bucket, Key=f"analysis/results/{contract_id}.json", Body=json.dumps(analysis_data))
        """
        analysis_file = self.dirs["analysis"] / f"{contract_id}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2)
        
        # Update metadata
        if contract_id in self.metadata:
            self.metadata[contract_id]["analyzed_at"] = datetime.utcnow().isoformat()
            self.metadata[contract_id]["status"] = "ready"
            self._save_metadata()
        
        return str(analysis_file)
    
    def get_analysis_results(self, contract_id: str) -> Dict[str, Any]:
        """Get analysis results"""
        analysis_file = self.dirs["analysis"] / f"{contract_id}.json"
        if not analysis_file.exists():
            raise FileNotFoundError(f"Analysis results for {contract_id} not found")
        
        with open(analysis_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_html(self, contract_id: str, html_content: str) -> str:
        """Save rendered HTML contract"""
        html_file = self.dirs["generated"] / f"{contract_id}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return str(html_file)
    
    def list_contracts(self) -> List[Dict[str, Any]]:
        """List all contracts (simulates DynamoDB scan)"""
        return list(self.metadata.values())
    
    def get_query_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached query result.
        In Lambda: DynamoDB AnalysisResults table
        Cache key format: contract_id#query_type#predicate_name
        Returns: The cached result (not the wrapper)
        """
        cache_file = self.dirs["query_cache"] / f"{cache_key.replace('#', '_')}.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                # Return just the result, not the wrapper
                return cached_data.get("result")
        return None
    
    def save_query_cache(self, cache_key: str, result: Dict[str, Any]) -> str:
        """
        Save query result to cache.
        In Lambda: DynamoDB AnalysisResults table
        PK: contract_id, SK: analysis_type#predicate_name
        """
        cache_file = self.dirs["query_cache"] / f"{cache_key.replace('#', '_')}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                "cache_key": cache_key,
                "result": result,
                "cached_at": datetime.utcnow().isoformat()
            }, f, indent=2)
        return str(cache_file)
    
    def invalidate_contract_cache(self, contract_id: str):
        """
        Invalidate all cached queries for a contract.
        Called when contract is recompiled.
        In Lambda: Delete all items from AnalysisResults where PK = contract_id
        """
        # Delete all cache files for this contract
        cache_dir = self.dirs["query_cache"]
        if cache_dir.exists():
            for cache_file in cache_dir.glob(f"{contract_id}_*.json"):
                cache_file.unlink()

