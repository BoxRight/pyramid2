#!/usr/bin/env python3
"""
Enhanced LAML JSON to SQL Converter with Responsibility Query Support
Takes all laml_results_*.json files and creates SQL tables optimized for responsibility analysis
"""

import json
import sqlite3
import os
import glob
from pathlib import Path

def create_enhanced_database_schema(cursor):
    """Create enhanced database schema for LAML results with responsibility support"""
    
    # Contracts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contracts (
            contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_name TEXT UNIQUE,
            satisfiable BOOLEAN,
            num_solutions INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Enhanced predicates table with type classification
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predicates (
            id INTEGER,
            predicate_name TEXT,
            arg1 TEXT,
            arg2 TEXT,
            arg3 TEXT,
            full_expression TEXT,
            predicate_type TEXT CHECK(predicate_type IN ('act', 'fact', 'claim', 'obligation', 'prohibition')),
            contract_id INTEGER,
            PRIMARY KEY (id, contract_id),
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id)
        )
    ''')
    
    # Parties/Entities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parties (
            party_id INTEGER PRIMARY KEY AUTOINCREMENT,
            party_name TEXT UNIQUE,
            party_type TEXT CHECK(party_type IN ('person', 'thing', 'service', 'entity'))
        )
    ''')
    
    # Predicate-party relationships with position tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predicate_parties (
            predicate_id INTEGER,
            contract_id INTEGER,
            party_id INTEGER,
            position INTEGER CHECK(position IN (1, 2, 3)),
            FOREIGN KEY (predicate_id, contract_id) REFERENCES predicates(id, contract_id),
            FOREIGN KEY (party_id) REFERENCES parties(party_id),
            PRIMARY KEY (predicate_id, contract_id, party_id, position)
        )
    ''')
    
    # Solutions table (unchanged)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS solutions (
            solution_id INTEGER,
            predicate_id INTEGER,
            contract_id INTEGER,
            FOREIGN KEY (predicate_id, contract_id) REFERENCES predicates(id, contract_id),
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id)
        )
    ''')
    
    # Enhanced claim types table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claim_types (
            predicate_id INTEGER,
            contract_id INTEGER,
            claim_type TEXT,
            FOREIGN KEY (predicate_id, contract_id) REFERENCES predicates(id, contract_id),
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id)
        )
    ''')
    
    # Cross-contract dependencies
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contract_dependencies (
            source_contract_id INTEGER,
            target_contract_id INTEGER,
            dependency_type TEXT,
            FOREIGN KEY (source_contract_id) REFERENCES contracts(contract_id),
            FOREIGN KEY (target_contract_id) REFERENCES contracts(contract_id)
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_predicates_name ON predicates(predicate_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_predicates_type ON predicates(predicate_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_predicate_parties_pred ON predicate_parties(predicate_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_predicate_parties_party ON predicate_parties(party_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_solutions_solution ON solutions(solution_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_solutions_pred ON solutions(predicate_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_parties_name ON parties(party_name)')
    
    print("✅ Enhanced database schema created with responsibility support")

def determine_predicate_type(predicate_name):
    """Determine predicate type based on naming patterns"""
    if 'claim' in predicate_name:
        return 'claim'
    elif predicate_name in ['pay_rent', 'maintain_item', 'grant_use', 'deliver_item', 'get_representation_permit', 'interconnect', 'sell_surplus', 'buy_system', 'condition_met']:
        return 'obligation'
    elif predicate_name in ['forbid']:
        return 'prohibition'
    elif predicate_name in ['buy_system', 'sell_surplus', 'interconnect', 'get_representation_permit']:
        return 'act'
    else:
        return 'fact'

def extract_parties_from_args(args):
    """Extract parties from predicate arguments"""
    parties = []
    for i, arg in enumerate(args):
        if arg and arg not in ['USD_200_monthly', 'USD_15000', 'SolarPanelSystem', 'LeaseTermCompleted']:
            parties.append((arg, i + 1))  # (party_name, position)
    return parties

def process_enhanced_json_file(json_file, cursor):
    """Process a single JSON file with enhanced responsibility support"""
    
    # Extract contract name from filename
    contract_name = Path(json_file).stem.replace('laml_results_', '')
    
    print(f"📄 Processing {contract_name}...")
    
    # Load JSON data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print(f"   📊 JSON data: {len(data.get('mappings', {}))} mappings, {len(data.get('solutions', []))} solutions")
    
    # Insert contract metadata
    cursor.execute('''
        INSERT OR REPLACE INTO contracts 
        (contract_name, satisfiable, num_solutions)
        VALUES (?, ?, ?)
    ''', (
        contract_name,
        data.get('satisfiable', False),
        data.get('num_solutions', 0)
    ))
    
    contract_id = cursor.lastrowid
    
    # Insert predicates with enhanced structure
    predicate_count = 0
    for pred_id, pred_data in data.get('mappings', {}).items():
        predicate_type = determine_predicate_type(pred_data['predicate'])
        args = pred_data['args']
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO predicates 
                (id, predicate_name, arg1, arg2, arg3, full_expression, predicate_type, contract_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                int(pred_id),
                pred_data['predicate'],
                args[0] if len(args) > 0 else None,
                args[1] if len(args) > 1 else None,
                args[2] if len(args) > 2 else None,
                pred_data['full'],
                predicate_type,
                contract_id
            ))
            predicate_count += 1
        except Exception as e:
            print(f"❌ Error inserting predicate {pred_id}: {e}")
            continue
        
        # Extract and insert parties
        parties = extract_parties_from_args(args)
        for party_name, position in parties:
            # Skip if position is out of range (fix for the constraint error)
            if position > 3:
                continue
                
            # Insert party if not exists
            cursor.execute('''
                INSERT OR IGNORE INTO parties (party_name, party_type)
                VALUES (?, ?)
            ''', (party_name, 'person' if party_name in ['HomeOwner', 'SolarCorp', 'grid', 'cre'] else 'entity'))
            
            # Get party_id
            cursor.execute('SELECT party_id FROM parties WHERE party_name = ?', (party_name,))
            party_id = cursor.fetchone()[0]
            
            # Insert predicate-party relationship
            cursor.execute('''
                INSERT OR REPLACE INTO predicate_parties (predicate_id, contract_id, party_id, position)
                VALUES (?, ?, ?, ?)
            ''', (int(pred_id), contract_id, party_id, position))
    
    # Insert solutions
    for solution_id, predicate_ids in enumerate(data.get('solutions', [])):
        for pred_id in predicate_ids:
            cursor.execute('''
                INSERT INTO solutions (solution_id, predicate_id, contract_id)
                VALUES (?, ?, ?)
            ''', (solution_id, int(pred_id), contract_id))
    
    # Insert claim types
    for claim_type, claims in data.get('claims', {}).items():
        for claim in claims:
            # Find matching predicate
            pred_id = None
            for k, v in data.get('mappings', {}).items():
                if (v['predicate'] == claim['predicate'] and 
                    v['args'] == claim['args']):
                    pred_id = int(k)
                    break
            
            if pred_id:
                cursor.execute('''
                    INSERT OR REPLACE INTO claim_types (predicate_id, contract_id, claim_type)
                    VALUES (?, ?, ?)
                ''', (pred_id, contract_id, claim_type))
    
    print(f"✅ {contract_name}: {predicate_count} predicates inserted, {len(data.get('solutions', []))} solutions")

def create_responsibility_views(cursor):
    """Create views for common responsibility queries"""
    
    # View for party obligations
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS party_obligations AS
        SELECT 
            p.party_name,
            pred.predicate_name,
            pred.full_expression,
            c.contract_name
        FROM parties p
        JOIN predicate_parties pp ON p.party_id = pp.party_id
        JOIN predicates pred ON pp.predicate_id = pred.id
        JOIN contracts c ON pred.contract_id = c.contract_id
        WHERE pred.predicate_type = 'obligation'
        AND pp.position = 1
    ''')
    
    # View for cross-party claims
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS cross_party_claims AS
        SELECT 
            p1.party_name as party1,
            p2.party_name as party2,
            pred.predicate_name,
            pred.full_expression,
            c.contract_name
        FROM predicates pred
        JOIN predicate_parties pp1 ON pred.id = pp1.predicate_id AND pp1.position = 1
        JOIN parties p1 ON pp1.party_id = p1.party_id
        JOIN predicate_parties pp2 ON pred.id = pp2.predicate_id AND pp2.position = 2
        JOIN parties p2 ON pp2.party_id = p2.party_id
        JOIN contracts c ON pred.contract_id = c.contract_id
        WHERE pred.predicate_type IN ('claim', 'obligation')
    ''')
    
    # View for solution analysis
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS solution_analysis AS
        SELECT 
            s.solution_id,
            c.contract_name,
            COUNT(DISTINCT s.predicate_id) as num_predicates,
            GROUP_CONCAT(pred.predicate_name, ', ') as predicates
        FROM solutions s
        JOIN contracts c ON s.contract_id = c.contract_id
        JOIN predicates pred ON s.predicate_id = pred.id
        GROUP BY s.solution_id, c.contract_name
    ''')
    
    print("✅ Responsibility analysis views created")

def main():
    """Main function to convert all JSON files to enhanced SQL"""
    
    # Connect to SQLite database
    conn = sqlite3.connect('enhanced_laml_contracts.db')
    cursor = conn.cursor()
    
    # Create enhanced database schema
    create_enhanced_database_schema(cursor)
    
    # Find all LAML result JSON files
    json_files = glob.glob('laml_results_*.json')
    
    if not json_files:
        print("❌ No laml_results_*.json files found!")
        return
    
    print(f"🔍 Found {len(json_files)} JSON files to process")
    
    # Process each JSON file
    for json_file in sorted(json_files):
        try:
            process_enhanced_json_file(json_file, cursor)
        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")
    
    # Create responsibility analysis views
    create_responsibility_views(cursor)
    
    # Commit all changes
    conn.commit()
    
    # Show summary
    cursor.execute('SELECT COUNT(*) FROM contracts')
    num_contracts = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM predicates')
    num_predicates = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM parties')
    num_parties = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM solutions')
    num_solutions = cursor.fetchone()[0]
    
    print(f"\n🎉 Enhanced Conversion Complete!")
    print(f"📊 Summary:")
    print(f"   • {num_contracts} contracts")
    print(f"   • {num_predicates} predicates")
    print(f"   • {num_parties} parties")
    print(f"   • {num_solutions} solution entries")
    print(f"   • Database: enhanced_laml_contracts.db")
    
    # Show responsibility query examples
    print(f"\n🔍 Responsibility Query Examples:")
    print(f"   • Party obligations: SELECT * FROM party_obligations WHERE party_name = 'HomeOwner';")
    print(f"   • Cross-party claims: SELECT * FROM cross_party_claims WHERE party1 = 'HomeOwner' AND party2 = 'SolarCorp';")
    print(f"   • Solution analysis: SELECT * FROM solution_analysis WHERE contract_name = 'enhanced_solar_contract';")
    print(f"   • Fulfillment analysis: SELECT p.predicate_name, COUNT(DISTINCT s.solution_id) FROM predicates p JOIN solutions s ON p.id = s.predicate_id WHERE p.predicate_name = 'pay_rent' GROUP BY p.predicate_name;")
    
    conn.close()

if __name__ == "__main__":
    main()
