"""
Contract Analysis Service
Analyzes contracts for violations and fulfillments - can be extracted to Lambda function: laml-analyzer

Uses the FINAL contract (authoritative solution space) for analysis.
Components are analyzed separately and can be queried individually.
"""

from pathlib import Path
from typing import Dict, Any

from backend.lib.violation_analysis import LAMLViolationAnalyzer


async def analyze_contract(
    contract_id: str,
    storage: Any,  # LocalStorage instance
    instance_name: str = None  # Optional: analyze specific component instead of final
) -> Dict[str, Any]:
    """
    Analyze contract for violations and fulfillments.
    
    Uses the FINAL contract (last .valid() call) as the authoritative solution space.
    Components can be analyzed separately by passing instance_name.
    
    In Lambda, this would:
    1. Download final AST JSON from S3 (or component if specified)
    2. Run analysis using violation_analysis.py logic
    3. Store results in DynamoDB/S3
    4. Return analysis results
    
    Args:
        contract_id: Contract identifier
        storage: Storage instance
        instance_name: Optional component instance name (if None, uses final contract)
    
    Returns:
        Dict with analysis results
    """
    
    # Get compiled results (solver output) - not AST!
    # LAMLViolationAnalyzer needs the results file, not the AST
    if instance_name:
        # Analyze specific component
        try:
            results_data = storage.get_component_result(contract_id, instance_name)
            results_file_path = Path(storage.metadata[contract_id]["components"][instance_name]["file"])
        except FileNotFoundError:
            raise FileNotFoundError(f"Component {instance_name} not found for contract {contract_id}")
    else:
        # Analyze final contract (authoritative)
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
    
    # Get all predicates
    predicates = []
    for pred_id, pred_info in analyzer.predicate_mappings.items():
        predicates.append({
            "predicate_id": pred_id,
            "predicate_name": pred_info["predicate"],
            "full_expression": pred_info.get("full", ""),
            "predicate_type": pred_info.get("type", "act")
        })
    
    # Analyze violations for all predicates
    violation_results = []
    fulfillment_results = []
    
    for predicate in predicates:
        pred_name = predicate["predicate_name"]
        
        # Violation analysis
        try:
            violation_result = analyzer.analyze_violation_consequences(pred_name)
            # Format consequences for frontend
            formatted_consequences = []
            for cons in violation_result.get("consequences", []):
                formatted_consequences.append({
                    "predicate_name": cons.get("predicate_name", ""),
                    "predicate_type": cons.get("predicate_type", "act"),
                    "full_expression": cons.get("full_expression", ""),
                    "consequence_type": cons.get("consequence_type", ""),
                    "count": cons.get("appears_in_violations", 0),
                    "total": violation_result.get("total_violation_scenarios", 0)
                })
            
            violation_results.append({
                "predicate": pred_name,
                "total_violation_scenarios": violation_result.get("total_violation_scenarios", 0),
                "total_fulfillment_scenarios": violation_result.get("total_fulfillment_scenarios", 0),
                "consequences": formatted_consequences,
                "num_consequences": len(formatted_consequences)
            })
        except Exception as e:
            print(f"Warning: Could not analyze violation for {pred_name}: {e}")
            violation_results.append({
                "predicate": pred_name,
                "total_violation_scenarios": 0,
                "total_fulfillment_scenarios": 0,
                "consequences": [],
                "num_consequences": 0,
                "error": str(e)
            })
        
        # Fulfillment analysis (simplified - analyze what happens when predicate is fulfilled)
        try:
            # Get solutions where predicate is present
            target_pred_id = analyzer.get_predicate_id(pred_name)
            fulfillment_solutions = [
                sol for sol in analyzer.solutions
                if target_pred_id in sol
            ]
            
            if fulfillment_solutions:
                # Analyze consequences in fulfillment scenarios
                fulfillment_consequences = []
                total_fulfillments = len(fulfillment_solutions)
                
                # Check which other predicates are always present/absent in fulfillment scenarios
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
                
                fulfillment_results.append({
                    "predicate": pred_name,
                    "total_fulfillment_scenarios": total_fulfillments,
                    "consequences": fulfillment_consequences,
                    "num_consequences": len(fulfillment_consequences)
                })
            else:
                fulfillment_results.append({
                    "predicate": pred_name,
                    "total_fulfillment_scenarios": 0,
                    "consequences": [],
                    "num_consequences": 0,
                    "message": f"Predicate '{pred_name}' is never fulfilled"
                })
        except Exception as e:
            print(f"Warning: Could not analyze fulfillment for {pred_name}: {e}")
            fulfillment_results.append({
                "predicate": pred_name,
                "total_fulfillment_scenarios": 0,
                "consequences": [],
                "num_consequences": 0,
                "error": str(e)
            })
    
    # Compile results
    analysis_results = {
        "contract_id": contract_id,
        "instance_name": instance_name or storage.metadata[contract_id].get("final_instance_name", "final"),
        "is_component": instance_name is not None,
        "total_solutions": analyzer.num_solutions,
        "num_predicates": len(predicates),
        "status": "ready",
        "satisfiable": results_data.get("satisfiable", False),
        "predicates": [p["predicate_name"] for p in predicates],
        "violation_results": violation_results,
        "fulfillment_results": fulfillment_results
    }
    
    # Save analysis results
    analysis_file = storage.save_analysis_results(contract_id, analysis_results)
    
    return analysis_results
