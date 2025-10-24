#!/usr/bin/env python3

import sqlite3
from typing import Dict, List, Optional

class SQLFulfillmentAnalyzer:
    """
    Analyzes fulfillment consequences using SQL queries based on the Python JSON analysis methodology.
    
    Key principles:
    1. Contract-specific analysis: Only analyze contracts where predicate is defined
    2. Argument header analysis: Use predicate definitions to determine contract membership
    3. Vector analysis: Use solution vectors to determine true/false states
    4. Logical consequences: Find actual legal relationships, not spurious correlations
    """
    
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        self.conn.close()
    
    def analyze_fulfillment_consequences(self, predicate_name: str, contract_name: Optional[str] = None) -> Dict:
        """
        Analyze what happens when a specific predicate is fulfilled.
        
        Returns:
        - total_fulfillment_scenarios: Number of solutions where predicate is present
        - consequences: List of predicates that are always present/absent in fulfillment scenarios
        - num_consequences: Count of consequence predicates
        """
        
        # Step 1: Find contracts where predicate is DEFINED (argument header analysis)
        contract_query = """
        SELECT DISTINCT c.contract_id, c.contract_name
        FROM contracts c
        JOIN predicates pred ON c.contract_id = pred.contract_id
        WHERE pred.predicate_name = ?
        """
        
        if contract_name:
            contract_query += " AND c.contract_name = ?"
            params = [predicate_name, contract_name]
        else:
            params = [predicate_name]
            
        cursor = self.conn.cursor()
        cursor.execute(contract_query, params)
        contracts = cursor.fetchall()
        
        if not contracts:
            return {
                'predicate': predicate_name,
                'total_fulfillment_scenarios': 0,
                'consequences': [],
                'num_consequences': 0,
                'message': f"Predicate '{predicate_name}' not found in any contracts"
            }
        
        all_consequences = []
        total_fulfillment_scenarios = 0
        
        # Step 2: Analyze each contract separately
        for contract_id, contract_name in contracts:
            print(f"🔍 Analyzing fulfillments in contract: {contract_name}")
            
            # Step 3: Find solutions where predicate is TRUE (vector analysis)
            # This is the key SQL query that replicates the Python logic
            query = """
            WITH fulfillment_solutions AS (
                -- Find all solutions in this contract that contain the target predicate
                SELECT DISTINCT s.solution_id
                FROM solutions s
                JOIN predicates pred ON s.predicate_id = pred.id AND s.contract_id = pred.contract_id
                WHERE pred.predicate_name = ? AND s.contract_id = ?
            ),
            -- Get all other predicates in this contract (excluding target)
            contract_predicates AS (
                SELECT pred.id, pred.predicate_name, pred.full_expression, pred.predicate_type
                FROM predicates pred
                WHERE pred.contract_id = ?
                AND pred.predicate_name != ?
            ),
            -- Count how often each predicate appears in fulfillment scenarios
            predicate_fulfillment_counts AS (
                SELECT 
                    cp.id,
                    cp.predicate_name,
                    cp.full_expression,
                    cp.predicate_type,
                    COUNT(DISTINCT s.solution_id) as fulfillment_count
                FROM contract_predicates cp
                LEFT JOIN solutions s ON cp.id = s.predicate_id AND s.contract_id = ?
                INNER JOIN fulfillment_solutions fs ON s.solution_id = fs.solution_id
                GROUP BY cp.id, cp.predicate_name, cp.full_expression, cp.predicate_type
            ),
            -- Get total fulfillment count for this contract
            total_fulfillments AS (
                SELECT COUNT(*) as total_count FROM fulfillment_solutions
            )
            SELECT 
                pfc.predicate_name,
                pfc.full_expression,
                pfc.predicate_type,
                pfc.fulfillment_count,
                tf.total_count,
                CASE 
                    WHEN pfc.fulfillment_count = tf.total_count THEN 'always_present'
                    WHEN pfc.fulfillment_count = 0 THEN 'always_absent'
                    ELSE 'sometimes_present'
                END as consequence_type
            FROM predicate_fulfillment_counts pfc
            CROSS JOIN total_fulfillments tf
            WHERE pfc.fulfillment_count = tf.total_count OR pfc.fulfillment_count = 0
            ORDER BY consequence_type, pfc.predicate_name
            """
            
            cursor.execute(query, [predicate_name, contract_id, contract_id, predicate_name, contract_id])
            consequences = [dict(row) for row in cursor.fetchall()]
            all_consequences.extend(consequences)
            
            # Get fulfillment count for this contract
            cursor.execute("""
                SELECT COUNT(DISTINCT s.solution_id) as fulfillment_count
                FROM solutions s
                JOIN predicates pred ON s.predicate_id = pred.id AND s.contract_id = pred.contract_id
                WHERE pred.predicate_name = ? AND s.contract_id = ?
            """, [predicate_name, contract_id])
            
            fulfillment_count = cursor.fetchone()['fulfillment_count']
            total_fulfillment_scenarios += fulfillment_count
            
            print(f"   📊 Found {fulfillment_count} fulfillment scenarios")
            print(f"   📋 Found {len(consequences)} consequences")
        
        return {
            'predicate': predicate_name,
            'total_fulfillment_scenarios': total_fulfillment_scenarios,
            'consequences': all_consequences,
            'num_consequences': len(all_consequences)
        }
    
    def get_contract_info(self, predicate_name: str) -> List[Dict]:
        """Get information about contracts where a predicate is defined"""
        query = """
        SELECT 
            c.contract_id,
            c.contract_name,
            c.num_solutions,
            COUNT(pred.id) as num_predicates_in_contract,
            COUNT(CASE WHEN pred.predicate_name = ? THEN 1 END) as target_predicate_count
        FROM contracts c
        JOIN predicates pred ON c.contract_id = pred.contract_id
        WHERE pred.predicate_name = ?
        GROUP BY c.contract_id, c.contract_name, c.num_solutions
        ORDER BY c.contract_id
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query, [predicate_name, predicate_name])
        return [dict(row) for row in cursor.fetchall()]
    
    def get_predicate_info(self, predicate_name: str) -> List[Dict]:
        """Get detailed information about a predicate across contracts"""
        query = """
        SELECT 
            pred.id,
            pred.predicate_name,
            pred.arg1,
            pred.arg2,
            pred.arg3,
            pred.predicate_type,
            pred.full_expression,
            c.contract_name,
            COUNT(s.solution_id) as appears_in_solutions
        FROM predicates pred
        JOIN contracts c ON pred.contract_id = c.contract_id
        LEFT JOIN solutions s ON pred.id = s.predicate_id AND pred.contract_id = s.contract_id
        WHERE pred.predicate_name = ?
        GROUP BY pred.id, pred.predicate_name, pred.arg1, pred.arg2, pred.arg3, 
                 pred.predicate_type, pred.full_expression, c.contract_name
        ORDER BY c.contract_id, pred.id
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query, [predicate_name])
        return [dict(row) for row in cursor.fetchall()]
    
    def show_available_predicates(self) -> None:
        """Show all available predicates in the database"""
        query = """
        SELECT 
            pred.predicate_name,
            COUNT(DISTINCT pred.contract_id) as num_contracts,
            COUNT(pred.id) as total_instances,
            GROUP_CONCAT(DISTINCT c.contract_name, ', ') as contracts
        FROM predicates pred
        JOIN contracts c ON pred.contract_id = c.contract_id
        GROUP BY pred.predicate_name
        ORDER BY pred.predicate_name
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query)
        predicates = cursor.fetchall()
        
        print("   Available predicates:")
        for pred in predicates:
            print(f"   • {pred['predicate_name']}: {pred['total_instances']} instances in {pred['num_contracts']} contracts")
            print(f"     Contracts: {pred['contracts']}")
            print()

def main():
    import sys
    
    print("🔍 SQL Fulfillment Analysis")
    print("=" * 50)
    
    # Get predicate name from command line argument or prompt user
    if len(sys.argv) > 1:
        predicate_name = sys.argv[1]
    else:
        predicate_name = input("Enter predicate name to analyze (e.g., 'pay_rent', 'grant_use', 'maintain_system'): ").strip()
    
    if not predicate_name:
        print("❌ No predicate name provided. Exiting.")
        return
    
    # Initialize analyzer
    analyzer = SQLFulfillmentAnalyzer('enhanced_laml_contracts.db')
    
    print(f"\n📋 Analyzing fulfillments for '{predicate_name}':")
    
    # Get contract information
    contracts = analyzer.get_contract_info(predicate_name)
    if not contracts:
        print(f"❌ Predicate '{predicate_name}' not found in any contracts.")
        print("\n💡 Available predicates:")
        analyzer.show_available_predicates()
        analyzer.close()
        return
    
    print(f"\n🏢 Contracts where '{predicate_name}' is defined:")
    for contract in contracts:
        print(f"   • {contract['contract_name']}: {contract['num_solutions']} solutions, {contract['num_predicates_in_contract']} predicates")
    
    # Get predicate information
    predicates = analyzer.get_predicate_info(predicate_name)
    print(f"\n🔧 Predicate details:")
    for pred in predicates:
        print(f"   • {pred['contract_name']}: {pred['full_expression']} (appears in {pred['appears_in_solutions']} solutions)")
    
    # Analyze fulfillment consequences
    print(f"\n⚖️ Fulfillment Analysis for '{predicate_name}':")
    fulfillment = analyzer.analyze_fulfillment_consequences(predicate_name)
    
    print(f"   Total fulfillment scenarios: {fulfillment['total_fulfillment_scenarios']}")
    print(f"   Consequences: {fulfillment['num_consequences']}")
    
    if fulfillment['num_consequences'] > 0:
        # Show always present consequences (positive consequences of performing)
        always_present = [c for c in fulfillment['consequences'] if c['consequence_type'] == 'always_present']
        if always_present:
            print(f"\n   ✅ Positive consequences (always present when {predicate_name} is fulfilled):")
            for cons in always_present[:5]:  # Show first 5
                print(f"   • {cons['predicate_name']} ({cons['predicate_type']}): {cons['fulfillment_count']}/{cons['total_count']} scenarios")
                print(f"     {cons['full_expression']}")
        
        # Show always absent consequences (prohibited consequences of performing)
        always_absent = [c for c in fulfillment['consequences'] if c['consequence_type'] == 'always_absent']
        if always_absent:
            print(f"\n   ❌ Prohibited consequences (always absent when {predicate_name} is fulfilled):")
            for cons in always_absent[:5]:  # Show first 5
                print(f"   • {cons['predicate_name']} ({cons['predicate_type']}): {cons['fulfillment_count']}/{cons['total_count']} scenarios")
                print(f"     {cons['full_expression']}")
    else:
        print(f"   No consequences found")
    
    analyzer.close()

if __name__ == "__main__":
    main()
