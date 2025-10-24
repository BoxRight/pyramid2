#!/usr/bin/env python3
"""
Enhanced Legal Vector Query System with Team Semantics
Combines ZDD query functionality with team semantics legal argument analysis
"""

import sys
import re
import json
import os
from collections import defaultdict
import shlex
from typing import List, Set, Dict, Tuple, Optional, Any

MAX_VECTORS_TO_PRINT = 100000

# ==================== TEAM SEMANTICS ALGORITHMS ====================

def dependency_measure(X: int, team: List[List[int]]) -> int:
    """Measures how much team collapses when variable X is removed"""
    original_size = len(team)
    
    team_without_X = []
    for vector in team:
        v_without_X = [v for v in vector if v != X]
        if v_without_X not in team_without_X:
            team_without_X.append(v_without_X)
    
    return original_size - len(team_without_X)

def essential_variable(X: int, team: List[List[int]]) -> bool:
    """Test if X appears in every vector"""
    for vector in team:
        if X not in vector:
            return False
    return True

def core_elements(team: List[List[int]]) -> List[int]:
    """Find variables that appear in ALL vectors"""
    if not team:
        return []
    
    core_variables = set(team[0])
    for vector in team[1:]:
        core_variables = core_variables.intersection(set(vector))
        if not core_variables:
            break
    
    return list(core_variables)

def universal_support(X: int, team: List[List[int]]) -> float:
    """Proportion of vectors containing X"""
    if not team:
        return 0.0
    count_with_X = sum(1 for vector in team if X in vector)
    return count_with_X / len(team)

def fragility(X: int, team: List[List[int]]) -> int:
    """Size of smallest vector containing X"""
    min_size = float('inf')
    for vector in team:
        if X in vector and len(vector) < min_size:
            min_size = len(vector)
    return min_size if min_size != float('inf') else 0

def robustness(X: int, team: List[List[int]]) -> int:
    """Size of largest vector containing X"""
    max_size = 0
    for vector in team:
        if X in vector and len(vector) > max_size:
            max_size = len(vector)
    return max_size

def leverage(X: int, team: List[List[int]]) -> float:
    """Dependency normalized by team size"""
    if not team:
        return 0.0
    dep_score = dependency_measure(X, team)
    return dep_score / len(team)

def criticality(X: int, team: List[List[int]]) -> float:
    """Combined fragility and leverage measure"""
    return fragility(X, team) * leverage(X, team)

def attack_surface(team_phi: List[List[int]], team_psi: List[List[int]]) -> List[List[int]]:
    """Intersection of compliant teams"""
    return [v for v in team_phi if v in team_psi]

def defense_space(team_phi: List[List[int]], team_psi: List[List[int]]) -> List[List[int]]:
    """Vectors unique to team_phi"""
    return [v for v in team_phi if v not in team_psi]

def team_intersection(team_phi: List[List[int]], team_psi: List[List[int]]) -> List[List[int]]:
    """Standard set intersection for teams"""
    return [v for v in team_phi if v in team_psi]

def team_union(team_phi: List[List[int]], team_psi: List[List[int]]) -> List[List[int]]:
    """Standard set union for teams"""
    union = team_phi.copy()
    for vector in team_psi:
        if vector not in union:
            union.append(vector)
    return union

# ==================== DATA LOADING AND INDEXING ====================

def load_kelsen_data(json_filename):
    """Load and index kelsen_data.json for contract lookups and relational queries."""
    if not os.path.isfile(json_filename):
        raise FileNotFoundError(f"JSON file not found: {json_filename}")
    
    with open(json_filename, 'r') as f:
        data = json.load(f)
    
    contract_map = {}
    subject1_index = {}
    subject2_index = {}
    clause_map = {}
    matrix_map = {}
    
    for contract in data.get('contracts', []):
        contract_id = contract['id']
        contract_map[contract_id] = {
            'description': contract['description'],
            'subject1': contract['subject1'],
            'subject2': contract['subject2'],
            'type': contract['type'],
            'key': contract['key']
        }
        subject1 = contract['subject1']
        subject2 = contract['subject2']
        if subject1 not in subject1_index:
            subject1_index[subject1] = []
        subject1_index[subject1].append(contract_id)
        if subject2 not in subject2_index:
            subject2_index[subject2] = []
        subject2_index[subject2].append(contract_id)
    
    for clause in data.get('clauses', []):
        clause_map[clause['key']] = {
            'condition_id1': clause['condition_id1'],
            'condition_id2': clause['condition_id2'],
            'consequence_id': clause['consequence_id']
        }
    
    for matrix in data.get('matrices', []):
        matrix_map[matrix['key']] = {
            'rows': matrix['rows'],
            'cols': matrix['cols'],
            'type': matrix['type'],
            'data': matrix['data']
        }
    
    return contract_map, subject1_index, subject2_index, clause_map, matrix_map

def load_vectors_from_file(filename: str, max_vectors: int = None) -> List[List[int]]:
    """Load all vectors from file into memory for team analysis"""
    if not os.path.isfile(filename):
        print(f"Warning: Vector file not found at {filename}. Returning empty list.", file=sys.stderr)
        return []
        
    vectors = []
    zdd_groups = []  # New: Store ZDD metadata and vectors
    current_zdd = None
    current_vectors = []
    
    with open(filename, 'r') as f:
        first_line = f.readline()
        if first_line.startswith('#') or 'Final results' in first_line:
            pass
        else:
            f.seek(0)
        
        for line in f:
            line = line.strip()
            if line == '' or line.startswith('#'):
                # Check for ZDD metadata
                if line.startswith('# ZDD '):
                    # Save previous ZDD if exists
                    if current_zdd and current_vectors:
                        zdd_groups.append({
                            'metadata': current_zdd,
                            'vectors': current_vectors.copy()
                        })
                    
                    # Parse new ZDD metadata
                    parts = line.split(':')
                    if len(parts) >= 2:
                        zdd_info = parts[1].strip()
                        current_zdd = {
                            'name': zdd_info,
                            'magic': None,
                            'arrays': None
                        }
                        current_vectors = []
                
                elif line.startswith('# Magic:') and current_zdd:
                    try:
                        current_zdd['magic'] = int(line.split(':')[1].strip())
                    except (ValueError, IndexError):
                        pass
                
                elif line.startswith('# Arrays:') and current_zdd:
                    try:
                        current_zdd['arrays'] = int(line.split(':')[1].strip())
                    except (ValueError, IndexError):
                        pass
                
                continue
            
            vector_match = re.search(r'\[(.*?)\]', line)
            if not vector_match:
                continue
                
            vector_str = vector_match.group(1)
            try:
                vector = [int(x.strip()) for x in vector_str.split(',') if x.strip()]
                vectors.append(vector)
                
                if current_zdd:
                    current_vectors.append(vector)
                
                if max_vectors and len(vectors) >= max_vectors:
                    break
            except ValueError:
                continue
        
        # Save the last ZDD
        if current_zdd and current_vectors:
            zdd_groups.append({
                'metadata': current_zdd,
                'vectors': current_vectors
            })
    
    # Store ZDD groups globally for ZDD-aware queries
    global _zdd_groups
    _zdd_groups = zdd_groups
    
    return vectors

# ==================== VECTOR QUERY FUNCTIONS ====================

def query_vectors(vectors_list: List[List[int]], required_elements, forbidden_elements, contract_map, allowed_ids=None, max_print=MAX_VECTORS_TO_PRINT):
    """Query a list of vectors, returning matching vectors and necessary IDs."""
    found_vectors = []
    
    for vector in vectors_list:
        satisfies_subject = allowed_ids is None or any(vid in allowed_ids for vid in vector)
        if (satisfies_subject and
            all(elem in vector for elem in required_elements) and
            not any(elem in vector for elem in forbidden_elements)):
            found_vectors.append(vector)
        
        if len(found_vectors) >= max_print:
            break
    
    necessary_ids = set()
    if found_vectors:
        necessary_ids = set(found_vectors[0])
        for vector in found_vectors[1:]:
            necessary_ids &= set(vector)
    
    return found_vectors, necessary_ids

# ==================== ZDD-AWARE QUERY FUNCTIONS ====================

def query_vectors_zdd_aware(required_elements, forbidden_elements, contract_map, allowed_ids=None, max_print=MAX_VECTORS_TO_PRINT):
    """Query vectors with ZDD awareness, returning results grouped by ZDD."""
    global _zdd_groups
    
    if not _zdd_groups:
        # Fallback to regular query if no ZDD groups available
        return query_vectors([], required_elements, forbidden_elements, contract_map, allowed_ids, max_print)
    
    zdd_results = []
    total_found_vectors = []
    
    for zdd_group in _zdd_groups:
        zdd_vectors = zdd_group['vectors']
        zdd_metadata = zdd_group['metadata']
        
        # Analyze ZDD domain
        zdd_domain = analyze_zdd_domain(zdd_vectors, zdd_metadata)
        
        # Check if required elements are applicable to this ZDD
        applicable_required = []
        non_applicable_required = []
        
        for elem in required_elements:
            if is_integer_applicable_to_zdd(elem, zdd_domain, zdd_metadata):
                applicable_required.append(elem)
            else:
                non_applicable_required.append(elem)
        
        # Apply the same query logic to this ZDD's vectors
        found_vectors = []
        for vector in zdd_vectors:
            satisfies_subject = allowed_ids is None or any(vid in allowed_ids for vid in vector)
            if (satisfies_subject and
                all(elem in vector for elem in applicable_required) and
                not any(elem in vector for elem in forbidden_elements)):
                found_vectors.append(vector)
        
        # Calculate necessary IDs for this ZDD
        necessary_ids = set()
        if found_vectors:
            necessary_ids = set(found_vectors[0])
            for vector in found_vectors[1:]:
                necessary_ids &= set(vector)
        
        # Determine status based on applicability and results
        if non_applicable_required:
            status = "NOT_APPLICABLE"
            status_reason = f"Required elements {non_applicable_required} not applicable to this ZDD domain"
        elif found_vectors:
            status = "FULFILLED"
            status_reason = f"Found {len(found_vectors)} matching vectors"
        else:
            status = "VIOLATED"
            status_reason = f"Required elements {applicable_required} missing from applicable ZDD"
        
        # Store results for this ZDD
        zdd_result = {
            'zdd_name': zdd_metadata['name'],
            'zdd_magic': zdd_metadata['magic'],
            'zdd_arrays': zdd_metadata['arrays'],
            'zdd_domain': zdd_domain,
            'found_vectors': found_vectors,
            'necessary_ids': necessary_ids,
            'vector_count': len(found_vectors),
            'status': status,
            'status_reason': status_reason,
            'applicable_required': applicable_required,
            'non_applicable_required': non_applicable_required
        }
        
        zdd_results.append(zdd_result)
        total_found_vectors.extend(found_vectors)
    
    # Calculate overall necessary IDs - find IDs that are necessary in ALL applicable ZDDs
    overall_necessary_ids = set()
    
    # For fulfillment analysis: look at ZDDs where the required elements are present
    if required_elements:
        applicable_zdds = [z for z in zdd_results if z['status'] == 'FULFILLED']
    # For violation analysis: look at ZDDs where forbidden elements are absent but vectors exist
    else:
        applicable_zdds = [z for z in zdd_results if z['status'] == 'VIOLATED' and z['vector_count'] > 0]
    
    if applicable_zdds:
        # Start with the necessary IDs from the first applicable ZDD
        overall_necessary_ids = applicable_zdds[0]['necessary_ids'].copy()
        
        # Intersect with necessary IDs from all other applicable ZDDs
        for zdd_result in applicable_zdds[1:]:
            overall_necessary_ids &= zdd_result['necessary_ids']
    
    return zdd_results, total_found_vectors, overall_necessary_ids

def split_vectors(vectors_list: List[List[int]], id1, id2, contract_map):
    """Split vectors based on presence of id1 or id2, returning sets Y (id1) and Z (id2)."""
    Y = set()  # IDs from vectors containing id1
    Z = set()  # IDs from vectors containing id2
    
    for vector in vectors_list:
        id1_present = id1 in vector
        id2_present = id2 in vector
        
        if not id1_present and not id2_present:
            print(f"Split fails: both actions interact with certainty.")
            print(f"Found vector without ID {id1} or ID {id2}: {vector}")
            return None, None, False
        
        if id1_present:
            Y.update(vector)
        if id2_present:
            Z.update(vector)
    
    print(f"Split succeeded: both actions interact with uncertainty.")
    print(f"Processed {len(vectors_list):,} vectors.")
    return Y, Z, True

def permissive_vectors(vectors_list: List[List[int]], id1, id2, contract_map):
    """Check if id1 and id2 are independent by observing all four presence/absence combinations."""
    # Track combinations: (id1_present, id2_present) -> count
    combinations = defaultdict(int)
    
    for vector in vectors_list:
        id1_present = id1 in vector
        id2_present = id2 in vector
        combinations[(id1_present, id2_present)] += 1
    
    print(f"Processed {len(vectors_list):,} vectors.")
    
    # Check for all four combinations
    expected_combinations = {(True, True), (True, False), (False, True), (False, False)}
    observed_combinations = set(combinations.keys())
    
    print("\nObserved combinations:")
    for (id1_present, id2_present), count in sorted(combinations.items()):
        id1_status = "present" if id1_present else "absent"
        id2_status = "present" if id2_present else "absent"
        print(f"  (ID {id1} {id1_status}, ID {id2} {id2_status}): {count} vectors")
    
    if observed_combinations == expected_combinations:
        print("\nPermissive: actions are independent")
        print(f"All four combinations observed, indicating ID {id1} ('{contract_map[id1]['description']}') "
              f"and ID {id2} ('{contract_map[id2]['description']}') are independent.")
    else:
        print("\nPermissive: actions are not independent")
        print(f"Only {len(observed_combinations)} of 4 combinations observed, indicating dependency "
              f"between ID {id1} ('{contract_map[id1]['description']}') and ID {id2} ('{contract_map[id2]['description']}').")
        missing = expected_combinations - observed_combinations
        if missing:
            print("Missing combinations:")
            for (id1_present, id2_present) in sorted(missing):
                id1_status = "present" if id1_present else "absent"
                id2_status = "present" if id2_present else "absent"
                print(f"  (ID {id1} {id1_status}, ID {id2} {id2_status})")
    
    return combinations, len(observed_combinations) == 4

# ==================== ZDD DOMAIN ANALYSIS ====================

def analyze_zdd_domain(zdd_vectors: List[List[int]], zdd_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the domain of a ZDD by examining its integer ranges"""
    if not zdd_vectors:
        return {'min_id': None, 'max_id': None, 'id_range': set(), 'domain_type': 'empty'}
    
    all_ids = set()
    for vector in zdd_vectors:
        all_ids.update(vector)
    
    if not all_ids:
        return {'min_id': None, 'max_id': None, 'id_range': set(), 'domain_type': 'empty'}
    
    min_id = min(all_ids)
    max_id = max(all_ids)
    
    # Analyze domain characteristics
    domain_info = {
        'min_id': min_id,
        'max_id': max_id,
        'id_range': all_ids,
        'total_ids': len(all_ids),
        'domain_type': f'range_{min_id}_{max_id}'  # Use actual range as domain type
    }
    
    return domain_info

def is_integer_applicable_to_zdd(integer: int, zdd_domain: Dict[str, Any], zdd_metadata: Dict[str, Any]) -> bool:
    """Determine if an integer is applicable to a ZDD's domain"""
    if not zdd_domain or zdd_domain['domain_type'] == 'empty':
        return False
    
    # Check if integer is within the ZDD's ID range (definitely applicable)
    if integer in zdd_domain['id_range']:
        return True
    
    # For integers not in the range, we need to be conservative
    # Since we don't have semantic metadata, we can't definitively say
    # whether an integer should be in a ZDD or not
    
    # Option 1: Assume NOT applicable (conservative)
    # This means if an integer is not in the ZDD's range, we assume it doesn't belong there
    return False
    
    # Option 2: Allow some flexibility around the range
    # This could be useful if IDs are assigned sequentially by domain
    # domain_type = zdd_domain['domain_type']
    # if domain_type.startswith('range_'):
    #     try:
    #         parts = domain_type.split('_')
    #         range_min = int(parts[1])
    #         range_max = int(parts[2])
    #         # Allow some flexibility around the range (within 5 IDs)
    #         return range_min - 5 <= integer <= range_max + 5
    #     except (IndexError, ValueError):
    #         return False
    # return False

# ==================== TEAM SEMANTICS ANALYSIS ====================

def team_semantic_analysis(team: List[List[int]], contract_map: Dict, team_name: str = "Team") -> Dict:
    """Comprehensive team semantic analysis"""
    if not team:
        return {"error": "Empty team"}
    
    # Get all variables in the team
    all_vars = set()
    for vector in team:
        all_vars.update(vector)
    all_vars = list(all_vars)
    
    analysis = {
        "team_name": team_name,
        "team_size": len(team),
        "total_variables": len(all_vars),
        "core_elements": core_elements(team),
        "variable_analysis": {}
    }
    
    # Analyze each variable
    for var in all_vars:
        var_analysis = {
            "id": var,
            "description": contract_map.get(var, {}).get('description', 'Unknown'),
            "support": universal_support(var, team),
            "fragility": fragility(var, team),
            "dependency": dependency_measure(var, team),
            "leverage": leverage(var, team),
            "criticality": criticality(var, team),
            "robustness": robustness(var, team),
            "essential": essential_variable(var, team)
        }
        analysis["variable_analysis"][var] = var_analysis
    
    return analysis

def generate_argument_strategy(plaintiff_team: List[List[int]], defendant_team: List[List[int]], 
                             contract_map: Dict) -> Dict:
    """Generate legal argument strategy using team semantics"""
    
    # Analyze both teams
    plaintiff_analysis = team_semantic_analysis(plaintiff_team, contract_map, "Plaintiff")
    defendant_analysis = team_semantic_analysis(defendant_team, contract_map, "Defendant")
    
    # Find attack targets (defendant vulnerabilities)
    attack_targets = []
    if "variable_analysis" in defendant_analysis:
        for var_id, var_data in defendant_analysis["variable_analysis"].items():
            if var_data["criticality"] > 0:
                attack_targets.append({
                    "variable": var_id,
                    "description": var_data["description"],
                    "criticality": var_data["criticality"],
                    "dependency": var_data["dependency"],
                    "fragility": var_data["fragility"],
                    "priority": var_data["criticality"] + (var_data["dependency"] * 0.5)
                })
    
    attack_targets.sort(key=lambda x: x["priority"], reverse=True)
    
    # Find what plaintiff must establish
    must_establish = plaintiff_analysis.get("core_elements", [])
    
    # Find contested ground
    contested = attack_surface(plaintiff_team, defendant_team)
    
    # Find defense positions
    defense_positions = defense_space(plaintiff_team, defendant_team)
    
    # Calculate strategic metrics
    plaintiff_vulnerabilities = []
    if "variable_analysis" in plaintiff_analysis:
        for var_id, var_data in plaintiff_analysis["variable_analysis"].items():
            if var_data["criticality"] > 0:
                plaintiff_vulnerabilities.append({
                    "variable": var_id,
                    "description": var_data["description"],
                    "criticality": var_data["criticality"],
                    "dependency": var_data["dependency"]
                })
    
    plaintiff_vulnerabilities.sort(key=lambda x: x["criticality"], reverse=True)
    
    strategy = {
        "plaintiff_analysis": plaintiff_analysis,
        "defendant_analysis": defendant_analysis,
        "attack_targets": attack_targets[:5],  # Top 5 targets
        "must_establish": must_establish,
        "plaintiff_vulnerabilities": plaintiff_vulnerabilities[:3],  # Top 3 vulnerabilities
        "contested_ground": len(contested),
        "contested_vectors": contested,
        "defense_positions": len(defense_positions),
        "defense_vectors": defense_positions,
        "strategic_advantage": "PLAINTIFF" if len(plaintiff_team) > len(defendant_team) else 
                              "DEFENDANT" if len(defendant_team) > len(plaintiff_team) else "BALANCED"
    }
    
    return strategy

def simulate_attack_impact(team: List[List[int]], target_variable: int, contract_map: Dict) -> Dict:
    """Simulate the impact of successfully attacking a target variable"""
    original_size = len(team)
    
    # Remove vectors containing the target variable
    modified_team = [vector for vector in team if target_variable not in vector]
    new_size = len(modified_team)
    
    impact = {
        "target_variable": target_variable,
        "target_description": contract_map.get(target_variable, {}).get('description', 'Unknown'),
        "original_team_size": original_size,
        "modified_team_size": new_size,
        "vectors_eliminated": original_size - new_size,
        "impact_percentage": ((original_size - new_size) / original_size * 100) if original_size > 0 else 0,
        "remaining_vectors": modified_team[:5] if len(modified_team) <= 5 else modified_team[:5],  # Show first 5
        "team_still_viable": new_size > 0
    }
    
    if new_size > 0:
        impact["new_core"] = core_elements(modified_team)
    
    return impact

# ==================== ENHANCED COMMAND PROCESSING ====================

def process_team_semantic_command(parts, all_vectors, contract_map):
    """Process team semantic analysis commands"""
    cmd = parts[0].lower()
    
    if cmd == 'analyze_team':
        if len(parts) < 2:
            print("Error: Missing team specification")
            print("Usage: analyze_team <required_elements> [forbidden_elements]")
            print("Example: analyze_team [1,2,3] [-4,-5]")
            return
        
        try:
            # Parse required elements
            required_str = parts[1].strip()
            if required_str.startswith('[') and required_str.endswith(']'):
                required_str = required_str[1:-1]
            required = [int(x.strip()) for x in required_str.split(',') if x.strip()]
            
            # Parse forbidden elements if provided
            forbidden = []
            if len(parts) > 2:
                forbidden_str = parts[2].strip()
                if forbidden_str.startswith('[') and forbidden_str.endswith(']'):
                    forbidden_str = forbidden_str[1:-1]
                forbidden = [abs(int(x.strip())) for x in forbidden_str.split(',') if x.strip()]
            
            # Get matching vectors
            found_vectors, _ = query_vectors(all_vectors, required, forbidden, contract_map)
            
            if not found_vectors:
                print("No vectors found matching the criteria")
                return
            
            # Perform team semantic analysis
            analysis = team_semantic_analysis(found_vectors, contract_map, "Query Team")
            
            print(f"\n=== TEAM SEMANTIC ANALYSIS ===")
            print(f"Team: {analysis['team_name']}")
            print(f"Size: {analysis['team_size']} vectors")
            print(f"Variables: {analysis['total_variables']}")
            
            core = analysis['core_elements']
            if core:
                print(f"\nCORE ELEMENTS (required in ALL vectors):")
                for var_id in core:
                    desc = contract_map.get(var_id, {}).get('description', 'Unknown')
                    print(f"  ID {var_id}: {desc}")
            else:
                print(f"\nNo core elements found")
            
            print(f"\nVARIABLE ANALYSIS:")
            var_analysis = analysis['variable_analysis']
            sorted_vars = sorted(var_analysis.items(), key=lambda x: x[1]['criticality'], reverse=True)
            
            for var_id, data in sorted_vars[:10]:  # Top 10 by criticality
                print(f"  ID {var_id}: {data['description']}")
                print(f"    Support: {data['support']:.3f} | Fragility: {data['fragility']} | "
                      f"Criticality: {data['criticality']:.3f}")
                print(f"    Dependency: {data['dependency']} | Leverage: {data['leverage']:.3f} | "
                      f"Essential: {data['essential']}")
                
        except ValueError as e:
            print(f"Error parsing elements: {e}")
            
    elif cmd == 'compare_teams':
        if len(parts) < 3:
            print("Error: Missing team specifications")
            print("Usage: compare_teams <team1_elements> <team2_elements>")
            print("Example: compare_teams [1,2,3] [4,5,6]")
            return
        
        try:
            # Parse team 1
            team1_str = parts[1].strip()
            if team1_str.startswith('[') and team1_str.endswith(']'):
                team1_str = team1_str[1:-1]
            team1_required = [int(x.strip()) for x in team1_str.split(',') if x.strip()]
            
            # Parse team 2
            team2_str = parts[2].strip()
            if team2_str.startswith('[') and team2_str.endswith(']'):
                team2_str = team2_str[1:-1]
            team2_required = [int(x.strip()) for x in team2_str.split(',') if x.strip()]
            
            # Get vectors for both teams
            team1_vectors, _ = query_vectors(all_vectors, team1_required, [], contract_map)
            team2_vectors, _ = query_vectors(all_vectors, team2_required, [], contract_map)
            
            if not team1_vectors or not team2_vectors:
                print("One or both teams have no matching vectors")
                return
            
            # Generate strategy
            strategy = generate_argument_strategy(team1_vectors, team2_vectors, contract_map)
            
            print(f"\n=== LEGAL ARGUMENT STRATEGY ===")
            print(f"Team 1 (Plaintiff): {strategy['plaintiff_analysis']['team_size']} vectors")
            print(f"Team 2 (Defendant): {strategy['defendant_analysis']['team_size']} vectors")
            print(f"Strategic Advantage: {strategy['strategic_advantage']}")
            
            print(f"\nTOP ATTACK TARGETS (Team 2 vulnerabilities):")
            for i, target in enumerate(strategy['attack_targets'][:3], 1):
                print(f"  {i}. ID {target['variable']}: {target['description']}")
                print(f"     Priority: {target['priority']:.3f} | Impact: {target['dependency']} paths eliminated")
                print(f"     Fragility: {target['fragility']} | Criticality: {target['criticality']:.3f}")
            
            must_establish = strategy['must_establish']
            if must_establish:
                print(f"\nMUST ESTABLISH (Team 1 core elements):")
                for var_id in must_establish:
                    desc = contract_map.get(var_id, {}).get('description', 'Unknown')
                    print(f"  ID {var_id}: {desc}")
            
            if strategy['plaintiff_vulnerabilities']:
                print(f"\nTEAM 1 VULNERABILITIES (protect these):")
                for vuln in strategy['plaintiff_vulnerabilities']:
                    print(f"  ID {vuln['variable']}: {vuln['description']}")
                    print(f"    Criticality: {vuln['criticality']:.3f} | Impact if lost: {vuln['dependency']} paths")
            
            print(f"\nCONTESTED GROUND: {strategy['contested_ground']} overlapping vectors")
            print(f"DEFENSE POSITIONS: {strategy['defense_positions']} unique to Team 1")
            
            # Resource allocation recommendations
            print(f"\nRESOURCE ALLOCATION RECOMMENDATIONS:")
            total_core = len(must_establish)
            total_attacks = len(strategy['attack_targets'][:3])
            
            if total_core > 0:
                print(f"  Core Elements: 40% of resources ({total_core} elements)")
            if total_attacks > 0:
                print(f"  Attack Targets: 30% of resources ({total_attacks} targets)")
            print(f"  Defense/Support: 20% of resources")
            print(f"  Contingency: 10% of resources")
            
        except ValueError as e:
            print(f"Error parsing teams: {e}")
            
    elif cmd == 'vulnerability_scan':
        if len(parts) < 2:
            print("Error: Missing team specification")
            print("Usage: vulnerability_scan <team_elements>")
            return
        
        try:
            # Parse team elements
            team_str = parts[1].strip()
            if team_str.startswith('[') and team_str.endswith(']'):
                team_str = team_str[1:-1]
            team_required = [int(x.strip()) for x in team_str.split(',') if x.strip()]
            
            # Get vectors
            team_vectors, _ = query_vectors(all_vectors, team_required, [], contract_map)
            
            if not team_vectors:
                print("No vectors found matching the criteria")
                return
            
            # Analyze vulnerabilities
            analysis = team_semantic_analysis(team_vectors, contract_map, "Target Team")
            
            print(f"\n=== VULNERABILITY SCAN ===")
            print(f"Team size: {analysis['team_size']} vectors")
            
            # Sort by vulnerability (high criticality = vulnerable)
            var_analysis = analysis['variable_analysis']
            vulnerabilities = sorted(var_analysis.items(), 
                                   key=lambda x: x[1]['criticality'], reverse=True)
            
            print(f"\nTOP VULNERABILITIES:")
            for i, (var_id, data) in enumerate(vulnerabilities[:5], 1):
                risk_level = "HIGH" if data['criticality'] > 0.5 else "MEDIUM" if data['criticality'] > 0.2 else "LOW"
                evidence_need = "HIGH" if data['fragility'] <= 2 else "MEDIUM" if data['fragility'] <= 4 else "LOW"
                
                print(f"  {i}. ID {var_id}: {data['description']}")
                print(f"     Risk Level: {risk_level} | Criticality: {data['criticality']:.3f}")
                print(f"     Attack Impact: Eliminates {data['dependency']} compliance paths")
                print(f"     Evidence Needed to Attack: {evidence_need} (complexity: {data['fragility']})")
                print(f"     Support Level: {data['support']:.1%} of scenarios")
            
            # Defensive recommendations
            high_risk_vars = [var_id for var_id, data in vulnerabilities if data['criticality'] > 0.5]
            if high_risk_vars:
                print(f"\nDEFENSIVE RECOMMENDATIONS:")
                print(f"  HIGH PRIORITY: Strengthen evidence for {len(high_risk_vars)} high-risk elements")
                for var_id in high_risk_vars[:3]:
                    desc = contract_map.get(var_id, {}).get('description', 'Unknown')
                    print(f"    - Fortify ID {var_id}: {desc}")
            
        except ValueError as e:
            print(f"Error parsing team: {e}")
            
    elif cmd == 'simulate_attack':
        if len(parts) < 3:
            print("Error: Missing team or target specification")
            print("Usage: simulate_attack <team_elements> <target_variable>")
            print("Example: simulate_attack [1,2,3,4] 2")
            return
        
        try:
            # Parse team elements
            team_str = parts[1].strip()
            if team_str.startswith('[') and team_str.endswith(']'):
                team_str = team_str[1:-1]
            team_required = [int(x.strip()) for x in team_str.split(',') if x.strip()]
            
            # Parse target variable
            target_var = int(parts[2])
            
            # Get vectors
            team_vectors, _ = query_vectors(all_vectors, team_required, [], contract_map)
            
            if not team_vectors:
                print("No vectors found matching the criteria")
                return
            
            # Simulate attack
            impact = simulate_attack_impact(team_vectors, target_var, contract_map)
            
            print(f"\n=== ATTACK SIMULATION ===")
            print(f"Target: ID {impact['target_variable']} ({impact['target_description']})")
            print(f"Impact: {impact['vectors_eliminated']} of {impact['original_team_size']} vectors eliminated")
            print(f"Damage: {impact['impact_percentage']:.1f}% of opponent's legal theories destroyed")
            
            if impact['team_still_viable']:
                print(f"Result: Target team reduced to {impact['modified_team_size']} vectors")
                if impact.get('new_core'):
                    print(f"New core requirements:")
                    for var_id in impact['new_core']:
                        desc = contract_map.get(var_id, {}).get('description', 'Unknown')
                        print(f"  ID {var_id}: {desc}")
                else:
                    print(f"No core requirements remain after attack")
            else:
                print(f"Result: TOTAL VICTORY - Target team becomes non-viable!")
            
        except ValueError as e:
            print(f"Error parsing parameters: {e}")

def process_command(command, all_vectors, contract_map, subject1_index, subject2_index, clause_map, matrix_map, filename=None):
    """Enhanced command processing with team semantics"""
    print(f"\nProcessing command: {command}")
    
    try:
        parts = shlex.split(command)
    except ValueError as e:
        print(f"Error: Command parsing failed. Check for unclosed quotes. Details: {e}")
        return

    if not parts:
        return
    
    cmd = parts[0].lower()
    
    # Check if it's a team semantic command
    if cmd in ('analyze_team', 'compare_teams', 'vulnerability_scan', 'simulate_attack'):
        process_team_semantic_command(parts, all_vectors, contract_map)
        return
    
    # Enhanced help
    if cmd == 'help':
        print("\nEnhanced Vector Query Tool - Commands:")
        print("\n--- BASIC QUERIES ---")
        print("  help                  - Show this help menu")
        print("  path <elements>       - Find vectors matching path [1,-2,3] (1=required, -2=forbidden)")
        print("  path_zdd <elements>   - ZDD-aware analysis showing per-ZDD results")
        print("  path_subject <subject> [elements] - Find vectors with contracts where subject1 or subject2 is <subject>")
        print("  count                 - Count total vectors in the file")
        print("  sample <n>            - Show first n vectors from the file")
        
        print("\n--- SUBJECT/CONTRACT QUERIES ---")
        print("  subject1_desc <subject> - Find descriptions where subject1 is <subject>")
        print("  subject2_desc <subject> - Find descriptions where subject2 is <subject>")
        print("  is_subject1_desc <subject> <description> - Check if <subject> is subject1 of <description>")
        print("  violates <subject1> <subject2> <description> - Find vectors where contract could be violated")
        print("  responsibility <subject> <description> <norm_key> [fulfills|violates] - Find consequences for subject")
        
        print("\n--- CLASSICAL TEAM SEMANTICS ---")
        print("  split <id1> <id2>     - Split vectors into Y (id1 present) and Z (id2 present)")
        print("  permissive <id1> <id2> - Check if id1 and id2 are independent")
        
        print("\n--- LEGAL STRATEGY ANALYSIS ---")
        print("  analyze_team <required> [forbidden] - Comprehensive team semantic analysis")
        print("  compare_teams <team1> <team2> - Generate legal argument strategy")
        print("  vulnerability_scan <team> - Find vulnerabilities in a legal position")
        print("  simulate_attack <team> <target> - Simulate impact of attacking specific element")
        
        print("\n--- EXAMPLES ---")
        print("  analyze_team [1,2,3]  - Analyze team with required elements 1,2,3")
        print("  compare_teams [1,2] [3,4] - Compare plaintiff vs defendant teams")
        print("  vulnerability_scan [5,6,7] - Find weak points in team with elements 5,6,7")
        print("  simulate_attack [1,2,3,4] 2 - Simulate attacking element 2 in team [1,2,3,4]")
        return
    
    # Process existing commands
    elif cmd == 'path':
        if len(parts) < 2:
            print("Error: Missing path elements")
            return
        
        try:
            path_str = parts[1].strip()
            if path_str.startswith('[') and path_str.endswith(']'):
                path_str = path_str[1:-1]
            path_elements = [int(x) for x in path_str.split(',')]
            required = [x for x in path_elements if x > 0]
            forbidden = [-x for x in path_elements if x < 0]
            
            # Use ZDD-aware query
            zdd_results, found_vectors, necessary_ids = query_vectors_zdd_aware(required, forbidden, contract_map)
            
            print(f"Found {len(found_vectors)} matching vectors across {len(zdd_results)} ZDDs")
            
            # Show ZDD-specific results
            for zdd_result in zdd_results:
                print(f"ZDD {zdd_result['zdd_name']}: {zdd_result['vector_count']} vectors - {zdd_result['status']}")
                if zdd_result['status'] == "NOT_APPLICABLE":
                    print(f"  Reason: {zdd_result['status_reason']}")
            
            if necessary_ids:
                print("\nCore elements (in all vectors):")
                for nid in sorted(necessary_ids):
                    desc = contract_map.get(nid, {}).get('description', 'Unknown')
                    print(f"  ID {nid}: {desc}")
            
            # Show sample vectors
            for i, vector in enumerate(found_vectors[:5]):
                vector_details = []
                for vid in vector:
                    contract = contract_map.get(vid)
                    if contract:
                        vector_details.append(f"ID {vid}: '{contract['description']}'")
                    else:
                        vector_details.append(f"ID {vid}: 'Unknown contract'")
                print(f"Vector {i+1}: {vector} -> {', '.join(vector_details)}")
                    
        except ValueError:
            print("Error: Invalid path format. Use format [1,-2,3]")
    
    elif cmd == 'path_zdd':
        if len(parts) < 2:
            print("Error: Missing path elements")
            return
        
        try:
            path_str = parts[1].strip()
            if path_str.startswith('[') and path_str.endswith(']'):
                path_str = path_str[1:-1]
            path_elements = [int(x) for x in path_str.split(',')]
            required = [x for x in path_elements if x > 0]
            forbidden = [-x for x in path_elements if x < 0]
            
            # Use ZDD-aware query
            zdd_results, found_vectors, necessary_ids = query_vectors_zdd_aware(required, forbidden, contract_map)
            
            print(f"ZDD-AWARE ANALYSIS:")
            print(f"Query: required={required}, forbidden={forbidden}")
            print(f"Total vectors found: {len(found_vectors)}")
            print(f"ZDDs analyzed: {len(zdd_results)}")
            print()
            
            # Detailed ZDD breakdown
            for zdd_result in zdd_results:
                print(f"ZDD {zdd_result['zdd_name']} (Magic: {zdd_result['zdd_magic']}, Arrays: {zdd_result['zdd_arrays']}):")
                print(f"  Status: {zdd_result['status']}")
                print(f"  Reason: {zdd_result['status_reason']}")
                print(f"  Domain: {zdd_result['zdd_domain']['domain_type']} (IDs {zdd_result['zdd_domain']['min_id']}-{zdd_result['zdd_domain']['max_id']})")
                print(f"  Vectors: {zdd_result['vector_count']}")
                
                if zdd_result['applicable_required']:
                    print(f"  Applicable required elements: {zdd_result['applicable_required']}")
                if zdd_result['non_applicable_required']:
                    print(f"  Non-applicable required elements: {zdd_result['non_applicable_required']}")
                
                if zdd_result['necessary_ids']:
                    print(f"  Core elements in this ZDD:")
                    for nid in sorted(zdd_result['necessary_ids']):
                        desc = contract_map.get(nid, {}).get('description', 'Unknown')
                        print(f"    ID {nid}: {desc}")
                
                if zdd_result['found_vectors']:
                    print(f"  Sample vectors:")
                    for i, vector in enumerate(zdd_result['found_vectors'][:3]):
                        print(f"    Vector {i+1}: {vector}")
                
                print()
            
            # Summary
            violated_zdds = [z for z in zdd_results if z['status'] == 'VIOLATED']
            fulfilled_zdds = [z for z in zdd_results if z['status'] == 'FULFILLED']
            not_applicable_zdds = [z for z in zdd_results if z['status'] == 'NOT_APPLICABLE']
            
            if violated_zdds:
                print(f"VIOLATED ZDDs ({len(violated_zdds)}):")
                for zdd in violated_zdds:
                    print(f"  - {zdd['zdd_name']}: {zdd['status_reason']}")
            
            if fulfilled_zdds:
                print(f"FULFILLED ZDDs ({len(fulfilled_zdds)}):")
                for zdd in fulfilled_zdds:
                    print(f"  - {zdd['zdd_name']} ({zdd['vector_count']} vectors)")
            
            if not_applicable_zdds:
                print(f"NOT APPLICABLE ZDDs ({len(not_applicable_zdds)}):")
                for zdd in not_applicable_zdds:
                    print(f"  - {zdd['zdd_name']}: {zdd['status_reason']}")
                    
        except ValueError:
            print("Error: Invalid path format. Use format [1,-2,3]")
    
    elif cmd == 'path_subject':
        if len(parts) < 2:
            print("Error: Missing subject")
            return
        
        subject = parts[1].strip()
        required = []
        forbidden = []
        
        if len(parts) > 2:
            try:
                path_str = parts[2].strip()
                if path_str.startswith('[') and path_str.endswith(']'):
                    path_str = path_str[1:-1]
                path_elements = [int(x) for x in path_str.split(',')]
                required = [x for x in path_elements if x > 0]
                forbidden = [-x for x in path_elements if x < 0]
            except ValueError:
                print("Error: Invalid elements format. Use format [1,-2,3]")
                return
        
        allowed_ids = set(subject1_index.get(subject, []) + subject2_index.get(subject, []))
        if not allowed_ids:
            print(f"No contracts found with subject: {subject}")
            return
        
        found_vectors, necessary_ids = query_vectors(all_vectors, required, forbidden, contract_map, allowed_ids=allowed_ids)
        print(f"Found {len(found_vectors)} matching vectors for subject '{subject}'")
        
        if necessary_ids:
            print("Core elements (in all vectors):")
            for nid in sorted(necessary_ids):
                desc = contract_map.get(nid, {}).get('description', 'Unknown')
                print(f"  ID {nid}: {desc}")
    
    elif cmd == 'subject1_desc':
        if len(parts) < 2:
            print("Error: Missing subject")
            return
        
        subject = parts[1].strip()
        contract_ids = subject1_index.get(subject, [])
        if not contract_ids:
            print(f"No contracts found where subject1 is: {subject}")
            return
        
        print(f"Contracts where subject1 is '{subject}':")
        for cid in contract_ids:
            contract = contract_map.get(cid, {})
            print(f"ID {cid}: '{contract.get('description', 'Unknown contract')}'")
    
    elif cmd == 'subject2_desc':
        if len(parts) < 2:
            print("Error: Missing subject")
            return
        
        subject = parts[1].strip()
        contract_ids = subject2_index.get(subject, [])
        if not contract_ids:
            print(f"No contracts found where subject2 is: {subject}")
            return
        
        print(f"Contracts where subject2 is '{subject}':")
        for cid in contract_ids:
            contract = contract_map.get(cid, {})
            print(f"ID {cid}: '{contract.get('description', 'Unknown contract')}'")
    
    elif cmd == 'is_subject1_desc':
        if len(parts) < 3:
            print("Error: Missing subject or description")
            return
        
        subject = parts[1].strip()
        description = parts[2].strip()
        contract_ids = subject1_index.get(subject, [])
        
        if not contract_ids:
            print(f"No, '{subject}' is not subject1 of any contract with description containing '{description}'")
            return
        
        matching_ids = []
        for cid in contract_ids:
            contract = contract_map.get(cid, {})
            if description.lower() in contract.get('description', '').lower():
                matching_ids.append(cid)
        
        if matching_ids:
            print(f"Yes, '{subject}' is subject1 of contracts with description containing '{description}':")
            for cid in matching_ids:
                print(f"ID {cid}: '{contract_map[cid]['description']}'")
        else:
            print(f"No, '{subject}' is not subject1 of any contract with description containing '{description}'")
    
    elif cmd == 'violates':
        if len(parts) < 4:
            print("Error: Missing subject1, subject2, or description")
            return
        
        subject1 = parts[1].strip()
        subject2 = parts[2].strip()
        description = parts[3].strip()
        
        contract_ids = subject1_index.get(subject1, [])
        if not contract_ids:
            print(f"No contracts found with subject1='{subject1}', subject2='{subject2}', and description='{description}'")
            return
        
        matching_ids = []
        for cid in contract_ids:
            contract = contract_map.get(cid, {})
            if (contract.get('subject2') == subject2 and
                contract.get('description', '').lower() == description.lower()):
                matching_ids.append(cid)
        
        if not matching_ids:
            print(f"No contracts found with subject1='{subject1}', subject2='{subject2}', and description='{description}'")
            return
        
        print(f"Found {len(matching_ids)} matching contract(s):")
        for cid in matching_ids:
            contract = contract_map[cid]
            print(f"ID {cid}: description='{contract['description']}', "
                  f"subject1={contract['subject1']}, subject2={contract['subject2']}, "
                  f"type={contract['type']}, key='{contract['key']}'")
        
        forbidden = matching_ids
        print(f"\nQuerying vectors where contract IDs {matching_ids} are violated:")
        try:
            found_vectors, _ = query_vectors(all_vectors, [], forbidden, contract_map)
            if not found_vectors:
                print(f"No vectors found where contract IDs {matching_ids} are violated")
            else:
                print(f"Found {len(found_vectors)} violation scenarios")
        except Exception as e:
            print(f"Error querying vectors: {e}")
    
    elif cmd == 'responsibility':
        if len(parts) < 4:
            print("Error: Missing subject, description, or norm_key")
            return
        
        subject = parts[1].strip()
        description = parts[2].strip()
        norm_key = parts[3].strip()
        mode = 'both' if len(parts) == 4 else parts[4].strip().lower()
        
        if mode not in ('fulfills', 'violates', 'both'):
            print("Error: Mode must be 'fulfills', 'violates', or omitted (for both)")
            return
        
        contract_ids = set(subject1_index.get(subject, []) + subject2_index.get(subject, []))
        if not contract_ids:
            print(f"No contracts found with subject='{subject}' and description='{description}'")
            return
        
        matching_ids = []
        for cid in contract_ids:
            contract = contract_map.get(cid, {})
            contract_desc = contract.get('description', '').lower()
            # Strip keyword tags from description for matching (e.g., "(delivery/installation)" -> "")
            import re
            clean_description = re.sub(r'\s*\([^)]*\)\s*', '', description.lower())
            if contract_desc == clean_description:
                matching_ids.append(cid)
        
        if not matching_ids:
            print(f"No contracts found with subject='{subject}' and description='{description}'")
            return
        
        # Find the main contract
        main_contract = contract_map[matching_ids[0]]
        print(f"OBLIGATION ANALYSIS:")
        print(f"Subject: {subject}")
        print(f"Obligation: {main_contract['description']}")
        print(f"Between: {main_contract['subject1']} and {main_contract['subject2']}")
        
        # Get norm information - look for contract with matching key
        norm_contract = None
        for cid, contract in contract_map.items():
            if contract.get('key') == norm_key:
                norm_contract = contract
                break
        
        if not norm_contract:
            print(f"No norm found with key='{norm_key}'")
            return
        
        print(f"Norm found: {norm_contract['description']}")
        
        # Look for related clauses
        related_clauses = []
        for clause_key, clause in clause_map.items():
            if (clause.get('condition_id1') == matching_ids[0] or 
                clause.get('condition_id2') == matching_ids[0] or
                clause.get('consequence_id') == matching_ids[0]):
                related_clauses.append(clause)
        
        if related_clauses:
            print(f"Found {len(related_clauses)} related clauses")
        
        # Analyze the specific mode requested
        for cid in matching_ids:
            if mode in ('fulfills', 'both'):
                print(f"\nFULFILLMENT ANALYSIS:")
                required = [cid]
                forbidden = []
                
                try:
                    zdd_results, found_vectors, necessary_ids = query_vectors_zdd_aware(required, forbidden, contract_map)
                    if found_vectors:
                        # Find what other IDs are always present when this ID is fulfilled
                        if necessary_ids:
                            print(f"CONSEQUENCES - Always required when fulfilled:")
                            for nid in sorted(necessary_ids):
                                if nid != cid:  # Don't show the obligation itself
                                    contract = contract_map.get(nid, {})
                                    desc = contract.get('description', 'Unknown contract')
                                    subject1 = contract.get('subject1', 'Unknown')
                                    subject2 = contract.get('subject2', 'Unknown')
                                    print(f"  • {desc} (between {subject1} and {subject2})")
                        else:
                            print(f"No other obligations consistently required when fulfilled")
                        
                        # Show per-ZDD fulfillment consequences
                        fulfilled_zdds = [z for z in zdd_results if z['status'] == 'FULFILLED']
                        if fulfilled_zdds:
                            print(f"\nFulfillment consequences by contract section:")
                            for zdd in fulfilled_zdds:
                                if zdd['necessary_ids']:
                                    zdd_necessary = [nid for nid in zdd['necessary_ids'] if nid != cid]
                                    if zdd_necessary:
                                        print(f"\n  When fulfilled in {zdd['zdd_name']}:")
                                        for nid in sorted(zdd_necessary):
                                            contract = contract_map.get(nid, {})
                                            desc = contract.get('description', 'Unknown contract')
                                            print(f"    • {desc}")
                    else:
                        print(f"No scenarios found where obligation is fulfilled")
                except Exception as e:
                    print(f"Error analyzing fulfillment: {e}")
            
            if mode in ('violates', 'both'):
                print(f"\nVIOLATION ANALYSIS:")
                required = []
                forbidden = [cid]
                
                try:
                    zdd_results, found_vectors, necessary_ids = query_vectors_zdd_aware(required, forbidden, contract_map)
                    if found_vectors:
                        # Find what other IDs are always present when this ID is absent
                        if necessary_ids:
                            print(f"CONSEQUENCES - Always present when violated:")
                            for nid in sorted(necessary_ids):
                                contract = contract_map.get(nid, {})
                                desc = contract.get('description', 'Unknown contract')
                                subject1 = contract.get('subject1', 'Unknown')
                                subject2 = contract.get('subject2', 'Unknown')
                                print(f"  • {desc} (between {subject1} and {subject2})")
                        
                        # Check for unsatisfiable sections (0 vectors when ID is absent)
                        unsatisfiable_sections = []
                        for zdd_result in zdd_results:
                            if zdd_result['status'] == 'VIOLATED' and zdd_result['vector_count'] == 0:
                                unsatisfiable_sections.append(zdd_result['zdd_name'])
                        
                        if unsatisfiable_sections:
                            print(f"\nCRITICAL: Contract becomes invalid when obligation is violated in these sections:")
                            for section in unsatisfiable_sections:
                                print(f"  • {section}")
                        
                        # Show detailed ZDD breakdown with necessary IDs
                        applicable_zdds = [z for z in zdd_results if z['vector_count'] > 0]
                        if applicable_zdds:
                            print(f"\nViolation consequences by contract section:")
                            for zdd in applicable_zdds:
                                if zdd['necessary_ids']:
                                    print(f"\n  When violated in {zdd['zdd_name']}:")
                                    for nid in sorted(zdd['necessary_ids']):
                                        contract = contract_map.get(nid, {})
                                        desc = contract.get('description', 'Unknown contract')
                                        print(f"    • {desc}")
                    else:
                        print(f"No scenarios found where obligation could be violated")
                except Exception as e:
                    print(f"Error analyzing violation: {e}")
    
    elif cmd == 'split':
        if len(parts) != 3:
            print("Error: Must provide exactly two IDs (e.g., split 1 2)")
            return
        
        try:
            id1 = int(parts[1])
            id2 = int(parts[2])
        except ValueError:
            print("Error: IDs must be integers")
            return
        
        if id1 not in contract_map or id2 not in contract_map:
            print(f"Error: One or both IDs ({id1}, {id2}) not found in contract map")
            return
        
        print(f"Splitting vectors for ID {id1} ('{contract_map[id1]['description']}') and ID {id2} ('{contract_map[id2]['description']}')")
        try:
            Y, Z, success = split_vectors(all_vectors, id1, id2, contract_map)
            if success:
                print(f"\nSet Y (IDs from vectors containing ID {id1}):")
                if Y:
                    for cid in sorted(Y):
                        desc = contract_map.get(cid, {}).get('description', 'Unknown contract')
                        print(f"  ID {cid}: '{desc}'")
                else:
                    print(f"  No vectors found containing ID {id1}")
                
                print(f"\nSet Z (IDs from vectors containing ID {id2}):")
                if Z:
                    for cid in sorted(Z):
                        desc = contract_map.get(cid, {}).get('description', 'Unknown contract')
                        print(f"  ID {cid}: '{desc}'")
                else:
                    print(f"  No vectors found containing ID {id2}")
            else:
                print("Split failed, see message above.")
        except Exception as e:
            print(f"Error splitting vectors: {e}")
    
    elif cmd == 'permissive':
        if len(parts) != 3:
            print("Error: Must provide exactly two IDs (e.g., permissive 1 2)")
            return
        
        try:
            id1 = int(parts[1])
            id2 = int(parts[2])
        except ValueError:
            print("Error: IDs must be integers")
            return
        
        if id1 not in contract_map or id2 not in contract_map:
            print(f"Error: One or both IDs ({id1}, {id2}) not found in contract map")
            return
        
        print(f"Checking permissive independence for ID {id1} ('{contract_map[id1]['description']}') and ID {id2} ('{contract_map[id2]['description']}')")
        try:
            combinations, is_independent = permissive_vectors(all_vectors, id1, id2, contract_map)
        except Exception as e:
            print(f"Error checking permissive independence: {e}")
    
    elif cmd == 'count':
        try:
            # The count command should still read from the file directly, as it's a simple line count
            # and doesn't need the loaded vector data. This avoids confusion if the file is very large.
            count = 0
            with open(filename, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        count += 1
            print(f"Total vectors in file: {count:,}")
        except Exception as e:
            print(f"Error counting vectors: {e}")
    
    elif cmd == 'sample':
        try:
            # The sample command should also read from the file to show the raw lines
            n = 10
            if len(parts) > 1:
                n = int(parts[1])
                if n <= 0:
                    print("Error: Sample size must be positive")
                    return
            
            with open(filename, 'r') as f:
                count = 0
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        vector_match = re.search(r'\[(.*?)\]', line)
                        if vector_match:
                            try:
                                vector = [int(x.strip()) for x in vector_match.group(1).split(',') if x.strip()]
                                vector_details = []
                                for vid in vector:
                                    contract = contract_map.get(vid)
                                    if contract:
                                        vector_details.append(f"ID {vid}: '{contract['description']}'")
                                    else:
                                        vector_details.append(f"ID {vid}: 'Unknown contract'")
                                print(f"Vector: {vector} -> {', '.join(vector_details)}")
                                count += 1
                                if count >= n:
                                    break
                            except ValueError:
                                print(f"Skipping invalid vector: {line.strip()}")
        except Exception as e:
            print(f"Error sampling vectors: {e}")
    
    else:
        print(f"Unknown command: {cmd}")

def main():
    """Main function with enhanced error handling and usage information"""
    if len(sys.argv) < 2:
        print("Enhanced Legal Vector Query System with Team Semantics")
        print("Usage: python enhanced_zdd_query.py <vector_file> [command]")
        print("\nExamples:")
        print("  python enhanced_zdd_query.py vectors.txt")
        print("  python enhanced_zdd_query.py vectors.txt 'analyze_team [1,2,3]'")
        print("  python enhanced_zdd_query.py vectors.txt 'compare_teams [1,2] [3,4]'")
        sys.exit(1)
    
    filename = sys.argv[1]
    json_filename = "kelsen_data.json"
    
    # Verify files exist
    if not os.path.isfile(filename):
        print(f"Error: Vector file not found: {filename}")
        sys.exit(1)
    
    try:
        contract_map, subject1_index, subject2_index, clause_map, matrix_map = load_kelsen_data(json_filename)
        print(f"Loaded {len(contract_map)} contracts from {json_filename}")
    except Exception as e:
        print(f"Error loading JSON: {e}")
        print("Note: Some features may not work without kelsen_data.json")
        contract_map, subject1_index, subject2_index, clause_map, matrix_map = {}, {}, {}, {}, {}

    # Load all vectors into memory for efficiency
    all_vectors = load_vectors_from_file(filename)
    if not all_vectors and os.path.isfile(filename):
        print(f"Warning: No vectors were loaded from {filename}. File might be empty or invalid.", file=sys.stderr)
    elif all_vectors:
        print(f"Loaded {len(all_vectors)} vectors into memory for analysis.")

    # Check if we're in single-command mode or interactive mode
    if len(sys.argv) > 2 or not sys.stdin.isatty():
        if len(sys.argv) > 2:
            command = ' '.join(sys.argv[2:])
        else:
            command = sys.stdin.read().strip()
        
        if not command:
            print("Error: No command provided")
            sys.exit(1)
        
        try:
            process_command(command, all_vectors, contract_map, subject1_index, subject2_index, clause_map, matrix_map, filename)
        except Exception as e:
            print(f"Error processing command: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        return

    # Interactive mode
    print(f"Enhanced Vector Query Tool - reading from {filename}")
    if contract_map:
        print(f"Using legal contract data from {json_filename}")
    print("Type 'help' for available commands, 'quit' or 'exit' to quit")
    
    while True:
        try:
            command = input("> ").strip()
            if not command:
                continue
            
            if command.lower() in ('quit', 'exit'):
                print("Goodbye!")
                break
                
            process_command(command, all_vectors, contract_map, subject1_index, subject2_index, clause_map, matrix_map, filename)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            # In interactive mode, continue on errors

if __name__ == "__main__":
    main()