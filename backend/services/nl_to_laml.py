"""
Natural Language to LAML Generation Service
Uses Claude API to convert natural language to LAML - can be extracted to Lambda function: nl-to-laml-generator
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent


async def generate_laml_from_natural_language(
    natural_language: str,
    contract_type: str = "solar_lease",
    jurisdiction: str = "Mexico",
    additional_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate LAML contract from natural language using Claude API.
    
    In Lambda, this would:
    1. Load templates/examples from S3
    2. Call Claude API (or Bedrock)
    3. Validate generated LAML
    4. Return LAML code
    
    Args:
        natural_language: Natural language description
        contract_type: Type of contract (solar_lease, etc.)
        jurisdiction: Legal jurisdiction
        additional_context: Additional context dict
    
    Returns:
        Dict with generated LAML code and metadata
    """
    
    # Initialize Anthropic client
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    
    anthropic = Anthropic(api_key=api_key)
    
    # Load example contracts and templates
    examples = _load_example_contracts(contract_type)
    templates = _load_laml_templates(contract_type)
    
    # Build prompt
    prompt = _build_laml_generation_prompt(
        natural_language,
        contract_type,
        jurisdiction,
        additional_context or {},
        templates,
        examples
    )
    
    # Call Claude API
    try:
        response = anthropic.messages.create(
            model="claude-3-5-sonnet-20240620",  # Use available model version
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Extract LAML code from response
        laml_code = _extract_laml_code(response.content[0].text)
        
        # Validate LAML structure (basic validation)
        validation_errors = _validate_laml(laml_code)
        
        # Generate contract ID
        import uuid
        contract_id = f"nl-generated-{uuid.uuid4().hex[:8]}"
        
        return {
            "contract_id": contract_id,
            "laml_content": laml_code,
            "validation_errors": validation_errors,
            "status": "generated"
        }
        
    except Exception as e:
        raise Exception(f"Failed to generate LAML: {str(e)}")


def _load_example_contracts(contract_type: str) -> str:
    """Load example LAML contracts"""
    examples_dir = PROJECT_ROOT / "contracts"
    
    # Load simple solar lease as default example
    example_file = examples_dir / "solar_lease_simple.laml"
    if example_file.exists():
        with open(example_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    return "# No example contracts found"


def _load_laml_templates(contract_type: str) -> str:
    """Load LAML templates for contract type"""
    # For now, return basic template structure
    return """
# Template structure:
# institution(name, ...) = institution(...) {
#     Type bindings
#     Predicates (acts)
#     Rules (obligations/claims)
# }
"""


def _build_laml_generation_prompt(
    nl_input: str,
    contract_type: str,
    jurisdiction: str,
    context: Dict[str, Any],
    templates: str,
    examples: str
) -> str:
    """Build comprehensive prompt for Claude"""
    
    return f"""You are a legal contract expert specializing in LAML (Legal Markup Language).

Your task is to convert natural language contract descriptions into valid LAML code.

INPUT:
Natural Language: "{nl_input}"
Contract Type: {contract_type}
Jurisdiction: {jurisdiction}
Additional Context: {json.dumps(context, indent=2)}

REFERENCE MATERIAL:
LAML Templates for {contract_type}:
{templates}

Example LAML Contracts:
{examples}

LAML SYNTAX RULES:
1. Use institution() to define contracts
2. Define parties with Person() types
3. Define objects with Thing() types
4. Use predicates for acts: act_name(party1, object, party2) = Person(...), Thing(...)
5. Use rules with implies for obligations: rule_name = condition implies oblig(action)
6. Import laws from ../laws/ directory using: import "../laws/ccf_core_lease.laml"
7. Import principles from ../principles/ directory
8. Use comments starting with # for documentation
9. Create contract instance with :- operator
10. Call .valid() on contract instance

REQUIREMENTS:
- Generate complete, valid LAML code
- Include all necessary imports
- Follow the structure of example contracts
- Include proper type bindings
- Add appropriate rules for obligations and claims
- Include metadata comments (@id, @derives, @priority) if applicable

OUTPUT:
Return ONLY the LAML code, no explanations or markdown formatting.
Do not wrap the code in code blocks or markdown."""


def _extract_laml_code(response_text: str) -> str:
    """Extract LAML code from Claude response"""
    # Remove markdown code blocks if present
    code = response_text.strip()
    
    # Remove ```laml or ``` markers
    if code.startswith("```"):
        lines = code.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines)
    
    return code.strip()


def _validate_laml(laml_code: str) -> list:
    """Basic LAML validation"""
    errors = []
    
    # Check for required elements
    if 'institution(' not in laml_code:
        errors.append("Missing institution() definition")
    
    if 'Person(' not in laml_code and 'Thing(' not in laml_code:
        errors.append("Missing type bindings (Person/Thing)")
    
    # Check for syntax issues
    if laml_code.count('(') != laml_code.count(')'):
        errors.append("Mismatched parentheses")
    
    if laml_code.count('{') != laml_code.count('}'):
        errors.append("Mismatched braces")
    
    return errors

