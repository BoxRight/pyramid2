"""
Contract Query Service
Queries contracts for specific predicate violations/fulfillments - can be extracted to Lambda function: laml-query

Strategy: Compute on first request, cache results for future queries
"""

from pathlib import Path
from typing import Dict, Any, Optional

from backend.lib.violation_analysis import LAMLViolationAnalyzer


async def query_contract_predicate(
    contract_id: str,
    predicate_name: str,
    query_type: str,  # "violation" or "fulfillment"
    storage: Any,  # LocalStorage instance
    instance_name: str = None  # Optional: query specific component instead of final
) -> Dict[str, Any]:
    """
    Query contract for violation/fulfillment consequences of a specific predicate.
    
    Strategy: Cache-aside pattern
    1. Check cache first (DynamoDB AnalysisResults table)
    2. If cache miss: Compute analysis, cache result, return
    3. If cache hit: Return cached result instantly
    
    In Lambda, this would:
    1. Query DynamoDB AnalysisResults for cached result
    2. If not cached: Load from S3, compute, cache in DynamoDB
    3. Return formatted results
    
    Args:
        contract_id: Contract identifier
        predicate_name: Name of predicate to query
        query_type: "violation" or "fulfillment"
        storage: Storage instance
        instance_name: Optional instance name for component queries
    
    Returns:
        Dict with query results
    """
    
    # Step 1: Check cache first
    cache_key = f"{contract_id}#{query_type}#{predicate_name}"
    if instance_name:
        cache_key = f"{contract_id}#{instance_name}#{query_type}#{predicate_name}"
    
    cached_result = storage.get_query_cache(cache_key)
    if cached_result:
        # Cache hit - return instantly!
        return cached_result
    
    # Step 2: Cache miss - compute analysis
    # Get compiled results (solver output) - not AST!
    # LAMLViolationAnalyzer needs the results file, not the AST
    if instance_name:
        # Query specific component
        try:
            results_data = storage.get_component_result(contract_id, instance_name)
            results_file_path = Path(storage.metadata[contract_id]["components"][instance_name]["file"])
        except FileNotFoundError:
            raise FileNotFoundError(f"Component {instance_name} not found for contract {contract_id}")
    else:
        # Query final contract (authoritative)
        try:
            results_data = storage.get_compiled_results(contract_id)
            results_path = storage.metadata[contract_id].get("s3_results_path")
            if results_path:
                results_file_path = storage.base_dir / results_path
            else:
                # Fallback to component results file
                final_name = storage.metadata[contract_id].get("final_instance_name")
                components = storage.metadata[contract_id].get("components", {})
                if final_name in components:
                    results_file_path = Path(components[final_name]["file"])
                else:
                    raise FileNotFoundError(f"Results file not found for contract {contract_id}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Contract {contract_id} not compiled. Please compile first.")
    
    # Initialize analyzer with results file (solver output)
    analyzer = LAMLViolationAnalyzer(str(results_file_path))
    
    if query_type == "violation":
        # Analyze violation consequences
        result = analyzer.analyze_violation_consequences(predicate_name)
        
        # Format consequences for frontend
        formatted_consequences = []
        for cons in result.get("consequences", []):
            formatted_consequences.append({
                "predicate_name": cons.get("predicate_name", ""),
                "predicate_type": cons.get("predicate_type", "act"),
                "full_expression": cons.get("full_expression", ""),
                "consequence_type": cons.get("consequence_type", ""),
                "count": cons.get("appears_in_violations", 0),
                "total": result.get("total_violation_scenarios", 0)
            })
        
        query_result = {
            "predicate": predicate_name,
            "total_violation_scenarios": result.get("total_violation_scenarios", 0),
            "total_fulfillment_scenarios": result.get("total_fulfillment_scenarios", 0),
            "consequences": formatted_consequences,
            "num_consequences": len(formatted_consequences)
        }
        
        # Step 3: Cache result for future queries
        storage.save_query_cache(cache_key, query_result)
        
        return query_result
    
    elif query_type == "fulfillment":
        # Analyze fulfillment consequences
        try:
            target_pred_id = analyzer.get_predicate_id(predicate_name)
            fulfillment_solutions = [
                sol for sol in analyzer.solutions
                if target_pred_id in sol
            ]
            
            if not fulfillment_solutions:
                return {
                    "predicate": predicate_name,
                    "total_fulfillment_scenarios": 0,
                    "consequences": [],
                    "message": f"Predicate '{predicate_name}' is never fulfilled"
                }
            
            # Analyze consequences
            fulfillment_consequences = []
            total_fulfillments = len(fulfillment_solutions)
            
            for other_pred_id, other_pred_info in analyzer.predicate_mappings.items():
                if int(other_pred_id) == target_pred_id:
                    continue
                
                count_present = sum(1 for sol in fulfillment_solutions if int(other_pred_id) in sol)
                
                if count_present == total_fulfillments:
                    fulfillment_consequences.append({
                        "predicate_name": other_pred_info["predicate"],
                        "predicate_type": other_pred_info.get("type", "act"),
                        "full_expression": other_pred_info.get("full", ""),
                        "consequence_type": "always_present",
                        "count": count_present,
                        "total": total_fulfillments
                    })
                elif count_present == 0:
                    fulfillment_consequences.append({
                        "predicate_name": other_pred_info["predicate"],
                        "predicate_type": other_pred_info.get("type", "act"),
                        "full_expression": other_pred_info.get("full", ""),
                        "consequence_type": "always_absent",
                        "count": 0,
                        "total": total_fulfillments
                    })
            
            query_result = {
                "predicate": predicate_name,
                "total_fulfillment_scenarios": total_fulfillments,
                "consequences": fulfillment_consequences,
                "num_consequences": len(fulfillment_consequences)
            }
            
            # Step 3: Cache result for future queries
            storage.save_query_cache(cache_key, query_result)
            
            return query_result
        except ValueError as e:
            raise ValueError(f"Predicate '{predicate_name}' not found in contract")
    
    else:
        raise ValueError(f"Invalid query_type: {query_type}. Must be 'violation' or 'fulfillment'")

