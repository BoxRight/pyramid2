#!/usr/bin/env python3

import json
from typing import Dict, List, Set

class LAMLViolationAnalyzer:
    """
    Analyzes violations by parsing LAML JSON results directly.
    
    Key principles:
    1. Parse JSON solutions as integer vectors
    2. Find solutions where target predicate is absent (violation scenarios)
    3. Analyze what other predicates appear in those violation scenarios
    4. Identify always present/absent consequences
    """
    
    def __init__(self, json_file_path: str):
        with open(json_file_path, 'r') as f:
            self.data = json.load(f)
        
        # Extract predicate mappings
        self.predicate_mappings = self.data['mappings']
        self.solutions = self.data['solutions']
        self.num_solutions = self.data['num_solutions']
        
        print(f"📊 Loaded {self.num_solutions} solutions from {json_file_path}")
        print(f"🔧 Found {len(self.predicate_mappings)} predicates")
    
    def get_predicate_id(self, predicate_name: str) -> int:
        """Get predicate ID by name"""
        for pred_id, pred_info in self.predicate_mappings.items():
            if pred_info['predicate'] == predicate_name:
                return int(pred_id)
        raise ValueError(f"Predicate '{predicate_name}' not found")
    
    def get_predicate_name(self, pred_id: int) -> str:
        """Get predicate name by ID"""
        return self.predicate_mappings[str(pred_id)]['predicate']
    
    def analyze_violation_consequences(self, predicate_name: str) -> Dict:
        """
        Analyze what happens when a specific predicate is violated (not fulfilled).
        
        Returns:
        - total_violation_scenarios: Number of solutions where predicate is absent
        - consequences: List of predicates that are always present/absent in violation scenarios
        - num_consequences: Count of consequence predicates
        """
        
        # Get predicate ID
        try:
            target_pred_id = self.get_predicate_id(predicate_name)
        except ValueError as e:
            return {
                'predicate': predicate_name,
                'total_violation_scenarios': 0,
                'consequences': [],
                'num_consequences': 0,
                'error': str(e)
            }
        
        print(f"\n🔍 Analyzing violations for '{predicate_name}' (ID: {target_pred_id})")
        
        # Step 1: Find violation scenarios (solutions where target predicate is absent)
        violation_solutions = []
        fulfillment_solutions = []
        
        for i, solution in enumerate(self.solutions):
            if target_pred_id in solution:
                fulfillment_solutions.append(i)
            else:
                violation_solutions.append(i)
        
        total_violations = len(violation_solutions)
        total_fulfillments = len(fulfillment_solutions)
        
        print(f"   📊 Fulfillment scenarios: {total_fulfillments}")
        print(f"   📊 Violation scenarios: {total_violations}")
        print(f"   📊 Total scenarios: {total_fulfillments + total_violations}")
        
        if total_violations == 0:
            return {
                'predicate': predicate_name,
                'total_violation_scenarios': 0,
                'consequences': [],
                'num_consequences': 0,
                'message': f"Predicate '{predicate_name}' is present in all solutions"
            }
        
        # Step 2: Analyze consequences in violation scenarios
        # Get all other predicate IDs (excluding target)
        other_pred_ids = [int(pred_id) for pred_id in self.predicate_mappings.keys() 
                         if int(pred_id) != target_pred_id]
        
        # Count how often each predicate appears in violation scenarios
        predicate_counts = {}
        for pred_id in other_pred_ids:
            count = 0
            for violation_idx in violation_solutions:
                if pred_id in self.solutions[violation_idx]:
                    count += 1
            predicate_counts[pred_id] = count
        
        # Step 3: Identify consequences
        consequences = []
        
        # Always present consequences (appear in ALL violation scenarios)
        always_present = []
        for pred_id, count in predicate_counts.items():
            if count == total_violations:
                always_present.append({
                    'predicate_id': pred_id,
                    'predicate_name': self.get_predicate_name(pred_id),
                    'full_expression': self.predicate_mappings[str(pred_id)]['full'],
                    'appears_in_violations': count,
                    'consequence_type': 'always_present'
                })
        
        # Always absent consequences (appear in NONE of violation scenarios)
        always_absent = []
        for pred_id, count in predicate_counts.items():
            if count == 0:
                always_absent.append({
                    'predicate_id': pred_id,
                    'predicate_name': self.get_predicate_name(pred_id),
                    'full_expression': self.predicate_mappings[str(pred_id)]['full'],
                    'appears_in_violations': count,
                    'consequence_type': 'always_absent'
                })
        
        consequences = always_present + always_absent
        
        print(f"   📋 Found {len(always_present)} always present consequences")
        print(f"   📋 Found {len(always_absent)} always absent consequences")
        print(f"   📋 Total consequences: {len(consequences)}")
        
        return {
            'predicate': predicate_name,
            'predicate_id': target_pred_id,
            'total_violation_scenarios': total_violations,
            'total_fulfillment_scenarios': total_fulfillments,
            'consequences': consequences,
            'num_consequences': len(consequences),
            'always_present_count': len(always_present),
            'always_absent_count': len(always_absent)
        }
    
    def show_sample_solutions(self, predicate_name: str, num_samples: int = 5):
        """Show sample solutions for debugging"""
        target_pred_id = self.get_predicate_id(predicate_name)
        
        print(f"\n🔍 Sample solutions for '{predicate_name}' (ID: {target_pred_id}):")
        
        # Show fulfillment samples
        fulfillment_samples = []
        violation_samples = []
        
        for i, solution in enumerate(self.solutions):
            if target_pred_id in solution:
                if len(fulfillment_samples) < num_samples:
                    fulfillment_samples.append((i, solution))
            else:
                if len(violation_samples) < num_samples:
                    violation_samples.append((i, solution))
        
        print(f"\n   ✅ Fulfillment samples (first {len(fulfillment_samples)}):")
        for idx, solution in fulfillment_samples:
            pred_names = [self.get_predicate_name(pid) for pid in solution]
            print(f"   Solution {idx}: {solution} → {', '.join(pred_names)}")
        
        print(f"\n   ❌ Violation samples (first {len(violation_samples)}):")
        for idx, solution in violation_samples:
            pred_names = [self.get_predicate_name(pid) for pid in solution]
            print(f"   Solution {idx}: {solution} → {', '.join(pred_names)}")

def analyze_contract(contract_name: str, json_file: str):
    """Analyze a specific contract"""
    print(f"\n{'='*60}")
    print(f"🔍 Analyzing Contract: {contract_name}")
    print(f"📁 File: {json_file}")
    print(f"{'='*60}")
    
    try:
        # Initialize analyzer
        analyzer = LAMLViolationAnalyzer(json_file)
        
        # Show predicate mappings
        print(f"\n📋 Predicate Mappings:")
        for pred_id, pred_info in analyzer.predicate_mappings.items():
            print(f"   {pred_id}: {pred_info['predicate']} → {pred_info['full']}")
        
        # Analyze violations for 'pay_rent'
        predicate_name = 'pay_rent'
        
        # Show sample solutions first
        analyzer.show_sample_solutions(predicate_name, num_samples=3)
        
        # Analyze violation consequences
        print(f"\n⚖️ Violation Analysis for '{predicate_name}':")
        violation = analyzer.analyze_violation_consequences(predicate_name)
        
        print(f"\n📊 Results:")
        print(f"   Total violation scenarios: {violation['total_violation_scenarios']}")
        print(f"   Total fulfillment scenarios: {violation['total_fulfillment_scenarios']}")
        print(f"   Consequences: {violation['num_consequences']}")
        print(f"   Always present: {violation['always_present_count']}")
        print(f"   Always absent: {violation['always_absent_count']}")
        
        if violation['num_consequences'] > 0:
            # Show always present consequences (positive consequences of not performing)
            always_present = [c for c in violation['consequences'] if c['consequence_type'] == 'always_present']
            if always_present:
                print(f"\n   ✅ Positive consequences (always present when {predicate_name} is NOT fulfilled):")
                for cons in always_present[:5]:  # Show first 5
                    print(f"   • {cons['predicate_name']} (ID: {cons['predicate_id']}): {cons['appears_in_violations']}/{violation['total_violation_scenarios']} scenarios")
                    print(f"     {cons['full_expression']}")
            
            # Show always absent consequences (prohibited consequences of not performing)
            always_absent = [c for c in violation['consequences'] if c['consequence_type'] == 'always_absent']
            if always_absent:
                print(f"\n   ❌ Prohibited consequences (always absent when {predicate_name} is NOT fulfilled):")
                for cons in always_absent[:5]:  # Show first 5
                    print(f"   • {cons['predicate_name']} (ID: {cons['predicate_id']}): {cons['appears_in_violations']}/{violation['total_violation_scenarios']} scenarios")
                    print(f"     {cons['full_expression']}")
        else:
            print(f"   No consequences found")
            
        return violation
        
    except Exception as e:
        print(f"❌ Error analyzing {contract_name}: {e}")
        return None

def main():
    print("🔍 LAML Violation Analysis (JSON Parser)")
    print("=" * 50)
    
    # Analyze both contracts that contain pay_rent
    contracts_to_analyze = [
        ("Core Lease Component", "laml_results_core_lease_component.json"),
        ("Enhanced Solar Contract", "laml_results_enhanced_solar_contract.json")
    ]
    
    results = {}
    
    for contract_name, json_file in contracts_to_analyze:
        result = analyze_contract(contract_name, json_file)
        if result:
            results[contract_name] = result
    
    # Compare results
    print(f"\n{'='*60}")
    print("📊 COMPARISON OF RESULTS")
    print(f"{'='*60}")
    
    for contract_name, result in results.items():
        print(f"\n🏢 {contract_name}:")
        print(f"   Violation scenarios: {result['total_violation_scenarios']}")
        print(f"   Fulfillment scenarios: {result['total_fulfillment_scenarios']}")
        print(f"   Always present consequences: {result['always_present_count']}")
        print(f"   Always absent consequences: {result['always_absent_count']}")
        
        # Show key findings
        always_absent = [c for c in result['consequences'] if c['consequence_type'] == 'always_absent']
        if always_absent:
            print(f"   Key prohibited consequence: {always_absent[0]['predicate_name']}")
        
        always_present = [c for c in result['consequences'] if c['consequence_type'] == 'always_present']
        if always_present:
            print(f"   Key positive consequence: {always_present[0]['predicate_name']}")

if __name__ == "__main__":
    main()
