#!/usr/bin/env python3
"""
Test API endpoints to verify the corrected backend implementation
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    """Test the API endpoints"""
    
    print("=" * 60)
    print("API Endpoint Testing")
    print("=" * 60)
    print()
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"   ✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Server not running. Start with: cd backend && python main.py")
        return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    print()
    
    # Test 2: Load and compile contract
    print("2. Testing contract compilation...")
    
    # Load test contract
    with open("contracts/solar_lease_simple.laml", 'r') as f:
        laml_content = f.read()
    
    contract_id = f"api-test-{int(time.time())}"
    
    try:
        response = requests.post(
            f"{BASE_URL}/contracts/compile",
            json={
                "contract_id": contract_id,
                "laml_content": laml_content
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Compilation successful")
            print(f"   Contract ID: {result['contract_id']}")
            print(f"   Final instance: {result.get('final_instance_name', 'N/A')}")
            print(f"   Solutions: {result.get('num_solutions', 0)} (authoritative)")
            print(f"   Components: {len(result.get('components', {}))}")
            
            # Show components
            components = result.get('components', {})
            for name, comp in components.items():
                if comp.get('num_solutions', 0) > 0:
                    print(f"      - {name}: {comp.get('num_solutions', 0)} solutions")
        else:
            print(f"   ❌ Compilation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    print()
    
    # Test 3: Get analysis
    print("3. Testing contract analysis...")
    try:
        response = requests.get(f"{BASE_URL}/contracts/{contract_id}/analysis")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Analysis successful")
            print(f"   Instance: {result.get('instance_name', 'N/A')}")
            print(f"   Total solutions: {result.get('total_solutions', 0)}")
            print(f"   Predicates: {result.get('num_predicates', 0)}")
            print(f"   Violation results: {len(result.get('violation_results', []))}")
            print(f"   Fulfillment results: {len(result.get('fulfillment_results', []))}")
        else:
            print(f"   ❌ Analysis failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 4: Query predicate
    print("4. Testing predicate query...")
    try:
        response = requests.post(
            f"{BASE_URL}/contracts/query",
            json={
                "contract_id": contract_id,
                "predicate_name": "pay_rent",
                "query_type": "violation"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Query successful")
            print(f"   Predicate: {result.get('predicate', 'N/A')}")
            print(f"   Violation scenarios: {result.get('total_violation_scenarios', 0)}")
            print(f"   Consequences: {result.get('num_consequences', 0)}")
        else:
            print(f"   ❌ Query failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 5: Component analysis (if components exist)
    print("5. Testing component analysis...")
    try:
        # Get compilation result to find components
        compile_response = requests.post(
            f"{BASE_URL}/contracts/compile",
            json={
                "contract_id": contract_id,
                "laml_content": laml_content
            }
        )
        
        if compile_response.status_code == 200:
            compile_result = compile_response.json()
            components = compile_result.get('components', {})
            final_name = compile_result.get('final_instance_name')
            
            # Find a component that's not the final one
            component_names = [name for name in components.keys() 
                             if name != final_name and components[name].get('num_solutions', 0) > 0]
            
            if component_names:
                component_name = component_names[0]
                print(f"   Querying component: {component_name}")
                
                response = requests.get(
                    f"{BASE_URL}/contracts/{contract_id}/analysis",
                    params={"instance_name": component_name}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Component analysis successful")
                    print(f"   Component: {result.get('instance_name', 'N/A')}")
                    print(f"   Is component: {result.get('is_component', False)}")
                    print(f"   Total solutions: {result.get('total_solutions', 0)}")
                else:
                    print(f"   ⚠️  Component analysis failed: {response.status_code}")
            else:
                print(f"   ⚠️  No components to test")
    except Exception as e:
        print(f"   ⚠️  Component test error: {e}")
    
    print()
    print("=" * 60)
    print("✅ API Testing Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_api()

