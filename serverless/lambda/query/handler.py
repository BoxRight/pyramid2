"""
Lambda handler for contract queries
Supports violation, fulfillment, and team semantics queries
"""

import json
import boto3
from typing import Dict, Any, List, Optional

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Table names (from environment variables)
CONTRACTS_TABLE = dynamodb.Table('Contracts')
PREDICATES_TABLE = dynamodb.Table('Predicates')
SOLUTIONS_TABLE = dynamodb.Table('Solutions')
ANALYSIS_TABLE = dynamodb.Table('AnalysisResults')

# S3 bucket for vector files
VECTORS_BUCKET = 'laml-contracts-service'


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for contract queries
    
    Expected event structure:
    {
        "query_type": "violation" | "fulfillment" | "team_semantics",
        "contract_id": "string",
        "predicate_name": "string",
        "query_params": {...}
    }
    """
    try:
        query_type = event.get('query_type')
        contract_id = event.get('contract_id')
        predicate_name = event.get('predicate_name')
        
        if not query_type or not contract_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameters: query_type, contract_id'
                })
            }
        
        if query_type == 'violation':
            result = analyze_violation(contract_id, predicate_name)
        elif query_type == 'fulfillment':
            result = analyze_fulfillment(contract_id, predicate_name)
        elif query_type == 'team_semantics':
            result = analyze_team_semantics(contract_id, event.get('query_params', {}))
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Unknown query_type: {query_type}'
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps(result, default=str)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'type': type(e).__name__
            })
        }


def analyze_violation(contract_id: str, predicate_name: str) -> Dict[str, Any]:
    """
    Analyze violation consequences for a predicate
    
    Uses DynamoDB to find:
    1. Solutions where predicate is absent
    2. Other predicates that are always present/absent in violation scenarios
    """
    # Get predicate ID
    predicate_response = PREDICATES_TABLE.query(
        IndexName='predicate_name-index',
        KeyConditionExpression='predicate_name = :name AND contract_id = :cid',
        ExpressionAttributeValues={
            ':name': predicate_name,
            ':cid': contract_id
        }
    )
    
    if not predicate_response['Items']:
        return {
            'predicate': predicate_name,
            'total_violation_scenarios': 0,
            'consequences': [],
            'message': f"Predicate '{predicate_name}' not found in contract"
        }
    
    predicate_id = predicate_response['Items'][0]['predicate_id']
    
    # Get all solutions for this contract
    all_solutions = SOLUTIONS_TABLE.query(
        KeyConditionExpression='contract_id = :cid',
        ExpressionAttributeValues={':cid': contract_id}
    )
    
    # Get solutions containing the predicate
    fulfillment_solutions = set()
    for solution in all_solutions['Items']:
        if predicate_id in solution.get('predicate_ids', []):
            fulfillment_solutions.add(solution['solution_id'])
    
    # Violation scenarios = all solutions - fulfillment solutions
    total_solutions = len(all_solutions['Items'])
    violation_count = total_solutions - len(fulfillment_solutions)
    
    if violation_count == 0:
        return {
            'predicate': predicate_name,
            'total_violation_scenarios': 0,
            'consequences': [],
            'message': f"Predicate '{predicate_name}' is present in all solutions"
        }
    
    # Find predicates that are always present/absent in violation scenarios
    violation_solution_ids = {
        sol['solution_id'] 
        for sol in all_solutions['Items'] 
        if sol['solution_id'] not in fulfillment_solutions
    }
    
    # Analyze consequences
    consequences = analyze_consequences(
        contract_id, 
        violation_solution_ids, 
        predicate_id
    )
    
    return {
        'predicate': predicate_name,
        'total_violation_scenarios': violation_count,
        'total_fulfillment_scenarios': len(fulfillment_solutions),
        'consequences': consequences,
        'num_consequences': len(consequences)
    }


def analyze_fulfillment(contract_id: str, predicate_name: str) -> Dict[str, Any]:
    """
    Analyze fulfillment consequences for a predicate
    Similar to violation analysis but for fulfillment scenarios
    """
    # Get predicate ID
    predicate_response = PREDICATES_TABLE.query(
        IndexName='predicate_name-index',
        KeyConditionExpression='predicate_name = :name AND contract_id = :cid',
        ExpressionAttributeValues={
            ':name': predicate_name,
            ':cid': contract_id
        }
    )
    
    if not predicate_response['Items']:
        return {
            'predicate': predicate_name,
            'total_fulfillment_scenarios': 0,
            'consequences': [],
            'message': f"Predicate '{predicate_name}' not found in contract"
        }
    
    predicate_id = predicate_response['Items'][0]['predicate_id']
    
    # Get all solutions for this contract
    all_solutions = SOLUTIONS_TABLE.query(
        KeyConditionExpression='contract_id = :cid',
        ExpressionAttributeValues={':cid': contract_id}
    )
    
    # Get solutions containing the predicate (fulfillment scenarios)
    fulfillment_solution_ids = {
        sol['solution_id'] 
        for sol in all_solutions['Items'] 
        if predicate_id in sol.get('predicate_ids', [])
    }
    
    if not fulfillment_solution_ids:
        return {
            'predicate': predicate_name,
            'total_fulfillment_scenarios': 0,
            'consequences': [],
            'message': f"Predicate '{predicate_name}' is never fulfilled"
        }
    
    # Analyze consequences
    consequences = analyze_consequences(
        contract_id, 
        fulfillment_solution_ids, 
        predicate_id
    )
    
    return {
        'predicate': predicate_name,
        'total_fulfillment_scenarios': len(fulfillment_solution_ids),
        'consequences': consequences,
        'num_consequences': len(consequences)
    }


def analyze_consequences(
    contract_id: str, 
    target_solution_ids: set, 
    exclude_predicate_id: str
) -> List[Dict[str, Any]]:
    """
    Find predicates that are always present or always absent
    in the target solution set
    """
    # Get all predicates for this contract (excluding target)
    predicates_response = PREDICATES_TABLE.query(
        KeyConditionExpression='contract_id = :cid',
        ExpressionAttributeValues={':cid': contract_id}
    )
    
    # Get all solutions
    all_solutions = SOLUTIONS_TABLE.query(
        KeyConditionExpression='contract_id = :cid',
        ExpressionAttributeValues={':cid': contract_id}
    )
    
    # Build solution map
    solution_map = {
        sol['solution_id']: set(sol.get('predicate_ids', []))
        for sol in all_solutions['Items']
        if sol['solution_id'] in target_solution_ids
    }
    
    if not solution_map:
        return []
    
    # Analyze each predicate
    consequences = []
    total_target_solutions = len(target_solution_ids)
    
    for pred_item in predicates_response['Items']:
        pred_id = pred_item['predicate_id']
        if pred_id == exclude_predicate_id:
            continue
        
        # Count how many target solutions contain this predicate
        count_with_predicate = sum(
            1 for sol_set in solution_map.values()
            if pred_id in sol_set
        )
        
        # Determine consequence type
        if count_with_predicate == total_target_solutions:
            consequence_type = 'always_present'
        elif count_with_predicate == 0:
            consequence_type = 'always_absent'
        else:
            continue  # Skip "sometimes present"
        
        consequences.append({
            'predicate_name': pred_item['predicate_name'],
            'predicate_type': pred_item.get('predicate_type'),
            'full_expression': pred_item.get('full_expression'),
            'consequence_type': consequence_type,
            'count': count_with_predicate,
            'total': total_target_solutions
        })
    
    return consequences


def analyze_team_semantics(contract_id: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform team semantics analysis for legal strategy
    
    Expected query_params:
    {
        "required_elements": [predicate_ids],
        "forbidden_elements": [predicate_ids],
        "analysis_type": "vulnerability" | "compare" | "attack"
    }
    """
    # This would implement the team semantics logic from zdd_query.py
    # For now, return placeholder
    return {
        'analysis_type': query_params.get('analysis_type', 'unknown'),
        'message': 'Team semantics analysis not yet implemented'
    }

