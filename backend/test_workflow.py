#!/usr/bin/env python3
"""
Test script to simulate the complete workflow
Tests: Generate → Compile → Analyze → Query
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.storage.local_storage import LocalStorage
from backend.services.nl_to_laml import generate_laml_from_natural_language
from backend.services.contract_compiler import compile_laml_contract
from backend.services.contract_analyzer import analyze_contract
from backend.services.contract_query import query_contract_predicate


async def test_workflow():
    """Simulate the complete contract workflow"""
    
    print("=" * 60)
    print("LAML Contract System - Workflow Simulation")
    print("=" * 60)
    print()
    
    # Initialize storage
    storage = LocalStorage()
    
    # Step 1: Load Existing Contract
    print("📝 Step 1: Load Existing Contract")
    print("-" * 60)
    
    # Use existing contract from contracts folder
    contract_file = "solar_lease_simple.laml"
    example_contract_path = PROJECT_ROOT / "contracts" / contract_file
    
    if not example_contract_path.exists():
        print(f"❌ Contract file not found: {example_contract_path}")
        print("   Available contracts:")
        contracts_dir = PROJECT_ROOT / "contracts"
        if contracts_dir.exists():
            for f in contracts_dir.glob("*.laml"):
                print(f"      - {f.name}")
        return
    
    try:
        with open(example_contract_path, 'r', encoding='utf-8') as f:
            laml_content = f.read()
        
        contract_id = "test-contract-001"
        storage.save_contract(
            contract_id=contract_id,
            laml_content=laml_content,
            contract_type="solar_lease",
            metadata={"source": "existing_contract", "jurisdiction": "Mexico", "file": contract_file}
        )
        
        print(f"✅ Loaded contract: {contract_file}")
        print(f"   Contract ID: {contract_id}")
        print(f"   LAML length: {len(laml_content)} characters")
        print(f"   Lines: {len(laml_content.splitlines())}")
    except Exception as e:
        print(f"❌ Failed to load contract: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Step 2: Compile Contract
    print("🔨 Step 2: Compile LAML Contract")
    print("-" * 60)
    
    try:
        # Get contract from storage
        contract_data = storage.get_contract(contract_id)
        laml_content = contract_data["laml_content"]
        
        result = await compile_laml_contract(
            contract_id=contract_id,
            laml_content=laml_content,
            storage=storage
        )
        
        print(f"✅ Compilation successful")
        print(f"   Contract ID: {contract_id}")
        print(f"   AST file: {result['ast_file']}")
        print(f"   Final instance: {result.get('final_instance_name', 'N/A')}")
        print(f"   Solutions: {result.get('num_solutions', 0)} (authoritative)")
        print(f"   Satisfiable: {result.get('satisfiable', False)}")
        print(f"   Compiled at: {result.get('compiled_at', 'N/A')}")
        
        # Show components if any
        components = result.get('components', {})
        if components:
            print(f"   Components found: {len(components)}")
            for name, comp in components.items():
                print(f"      - {name}: {comp.get('num_solutions', 0)} solutions, satisfiable={comp.get('satisfiable', False)}")
        else:
            print(f"   Components: None (single contract)")
    except Exception as e:
        print(f"❌ Compilation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Step 3: Analyze Contract
    print("🔍 Step 3: Analyze Contract")
    print("-" * 60)
    
    try:
        result = await analyze_contract(
            contract_id=contract_id,
            storage=storage
        )
        
        print(f"✅ Analysis complete")
        print(f"   Total solutions: {result.get('total_solutions', 0)}")
        print(f"   Predicates: {result.get('num_predicates', 0)}")
        print(f"   Satisfiable: {result.get('satisfiable', False)}")
        print()
        
        # Show violation results summary
        violation_results = result.get('violation_results', [])
        print(f"   Violation Analysis:")
        for vr in violation_results[:3]:  # Show first 3
            print(f"      - {vr['predicate']}: {vr['total_violation_scenarios']} violation scenarios, {vr['num_consequences']} consequences")
        
        if len(violation_results) > 3:
            print(f"      ... and {len(violation_results) - 3} more")
        
        print()
        print(f"   Fulfillment Analysis:")
        fulfillment_results = result.get('fulfillment_results', [])
        for fr in fulfillment_results[:3]:  # Show first 3
            print(f"      - {fr['predicate']}: {fr['total_fulfillment_scenarios']} fulfillment scenarios, {fr['num_consequences']} consequences")
        
        if len(fulfillment_results) > 3:
            print(f"      ... and {len(fulfillment_results) - 3} more")
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Step 4: Query Specific Predicate
    print("❓ Step 4: Query Contract Predicate")
    print("-" * 60)
    
    # Query pay_rent violation
    predicate_name = "pay_rent"
    query_type = "violation"
    
    print(f"Query: What happens if '{predicate_name}' is violated?")
    print()
    
    try:
        result = await query_contract_predicate(
            contract_id=contract_id,
            predicate_name=predicate_name,
            query_type=query_type,
            storage=storage
        )
        
        print(f"✅ Query successful")
        print(f"   Predicate: {result['predicate']}")
        print(f"   Violation scenarios: {result.get('total_violation_scenarios', 0)}")
        print(f"   Fulfillment scenarios: {result.get('total_fulfillment_scenarios', 0)}")
        print(f"   Consequences: {result.get('num_consequences', 0)}")
        print()
        
        if result.get('consequences'):
            print(f"   Consequences:")
            for cons in result['consequences'][:5]:  # Show first 5
                cons_type = cons.get('consequence_type', 'unknown')
                pred_name = cons.get('predicate_name', 'unknown')
                count = cons.get('count', 0)
                total = cons.get('total', 0)
                print(f"      - {pred_name}: {cons_type} ({count}/{total} scenarios)")
            
            if len(result['consequences']) > 5:
                print(f"      ... and {len(result['consequences']) - 5} more")
        else:
            print(f"   No consequences found")
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Step 5: Query Fulfillment
    print("❓ Step 5: Query Fulfillment")
    print("-" * 60)
    
    query_type = "fulfillment"
    print(f"Query: What happens when '{predicate_name}' is fulfilled?")
    print()
    
    try:
        result = await query_contract_predicate(
            contract_id=contract_id,
            predicate_name=predicate_name,
            query_type=query_type,
            storage=storage
        )
        
        print(f"✅ Query successful")
        print(f"   Predicate: {result['predicate']}")
        print(f"   Fulfillment scenarios: {result.get('total_fulfillment_scenarios', 0)}")
        print(f"   Consequences: {result.get('num_consequences', 0)}")
        print()
        
        if result.get('consequences'):
            print(f"   Consequences:")
            for cons in result['consequences'][:5]:  # Show first 5
                cons_type = cons.get('consequence_type', 'unknown')
                pred_name = cons.get('predicate_name', 'unknown')
                count = cons.get('count', 0)
                total = cons.get('total', 0)
                print(f"      - {pred_name}: {cons_type} ({count}/{total} scenarios)")
            
            if len(result['consequences']) > 5:
                print(f"      ... and {len(result['consequences']) - 5} more")
        else:
            print(f"   No consequences found")
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Step 6: Test Component Query (if components exist)
    components = storage.metadata.get(contract_id, {}).get("components", {})
    if components and len(components) > 1:
        print("🔍 Step 6: Test Component Query")
        print("-" * 60)
        
        # Find a component that's not the final one
        final_name = storage.metadata[contract_id].get("final_instance_name")
        component_names = [name for name in components.keys() if name != final_name and components[name].get("num_solutions", 0) > 0]
        
        if component_names:
            component_name = component_names[0]  # Use first non-final component
            print(f"Querying component: {component_name}")
            print(f"   Solutions: {components[component_name].get('num_solutions', 0)}")
            print()
            
            try:
                # Try to analyze the component
                component_result = await analyze_contract(
                    contract_id=contract_id,
                    storage=storage,
                    instance_name=component_name
                )
                
                print(f"✅ Component analysis successful")
                print(f"   Component: {component_name}")
                print(f"   Total solutions: {component_result.get('total_solutions', 0)}")
                print(f"   Predicates: {component_result.get('num_predicates', 0)}")
                print(f"   Is component: {component_result.get('is_component', False)}")
            except Exception as e:
                print(f"⚠️  Component analysis failed: {e}")
                print(f"   (This is okay - component may not have queryable predicates)")
    
    print()
    print("=" * 60)
    print("✅ Workflow Simulation Complete!")
    print("=" * 60)
    print()
    print(f"Contract ID: {contract_id}")
    print(f"Final instance: {storage.metadata.get(contract_id, {}).get('final_instance_name', 'N/A')}")
    print(f"Components: {len(components)}")
    print(f"Data stored in: {storage.base_dir}")
    print()
    print("Next steps:")
    print("  1. Start the backend server: cd backend && python main.py")
    print("  2. Start the frontend: cd frontend && npm run dev")
    print("  3. View the contract in the UI")


if __name__ == "__main__":
    asyncio.run(test_workflow())

