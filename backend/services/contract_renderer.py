"""
Contract HTML Renderer Service
Renders contracts as HTML - can be extracted to Lambda function: contract-renderer
"""

from pathlib import Path
from typing import Dict, Any


async def render_contract_html(
    contract_id: str,
    storage: Any  # LocalStorage instance
) -> str:
    """
    Render contract as HTML document.
    
    In Lambda, this would:
    1. Get contract AST from DynamoDB/S3
    2. Parse contract structure
    3. Generate HTML using template
    4. Upload to S3
    5. Return HTML content
    
    Args:
        contract_id: Contract identifier
        storage: Storage instance
    
    Returns:
        HTML content string
    """
    
    # Get compiled AST (hierarchical structure for contract parser)
    try:
        ast_data = storage.get_compiled_ast(contract_id)
        ast_file_path = storage.base_dir / storage.metadata[contract_id]["s3_ast_path"]
    except FileNotFoundError:
        raise FileNotFoundError(f"Contract {contract_id} not compiled")
    
    # Parse contract using AST parser (needs AST, not results!)
    try:
        from backend.lib.ast_contract_parser import ASTContractParser
        
        parser = ASTContractParser(str(ast_file_path), use_api_improvement=False)
        parsed_contract = parser.parse_contract()
        
        # Generate HTML from parsed contract
        html = _generate_html_from_parsed_contract(parsed_contract)
        
        # Save HTML
        storage.save_html(contract_id, html)
        
        return html
        
    except Exception as e:
        raise Exception(f"Failed to render contract: {str(e)}")


def _generate_html_from_parsed_contract(parsed_contract: Dict[str, Any]) -> str:
    """Generate HTML from parsed contract structure"""
    
    metadata = parsed_contract.get("metadata", {})
    parties = parsed_contract.get("parties_block", {}).get("parties", [])
    objects = parsed_contract.get("objects_section", {}).get("objects", [])
    declarations = parsed_contract.get("declarations_section", {}).get("declarations", [])
    clauses = parsed_contract.get("clauses_section", [])
    final_section = parsed_contract.get("final_section", {})
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata.get('title', 'Contract')}</title>
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            line-height: 1.6;
        }}
        h1 {{
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 30px;
        }}
        h2 {{
            font-size: 14px;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .party {{
            margin-bottom: 15px;
        }}
        .clause {{
            margin-bottom: 15px;
        }}
        .signature-section {{
            margin-top: 40px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <h1>{metadata.get('title', 'Contract')}</h1>
    
    <h2>PARTES</h2>
    {_render_parties(parties)}
    
    <h2>OBJETO</h2>
    {_render_objects(objects)}
    
    <h2>DECLARACIONES</h2>
    {_render_declarations(declarations)}
    
    <h2>CLÁUSULAS</h2>
    {_render_clauses(clauses)}
    
    {_render_final_section(final_section)}
</body>
</html>"""
    
    return html


def _render_parties(parties: list) -> str:
    """Render parties section"""
    html = ""
    for party in parties:
        html += f'<div class="party">{party.get("name", "")} como {party.get("role", "")}</div>'
    return html


def _render_objects(objects: list) -> str:
    """Render objects section"""
    html = ""
    for obj in objects:
        html += f'<div class="object">{obj.get("description", "")}</div>'
    return html


def _render_declarations(declarations: list) -> str:
    """Render declarations section"""
    html = ""
    for decl in declarations:
        party = decl.get("party", "")
        html += f'<h3>{party.upper()}</h3>'
        for item in decl.get("items", []):
            html += f'<div class="declaration">{item}</div>'
    return html


def _render_clauses(clauses: list) -> str:
    """Render clauses section"""
    html = ""
    for clause in clauses:
        html += f'<div class="clause"><strong>{clause.get("title", "")}</strong><br>{clause.get("content", "")}</div>'
    return html


def _render_final_section(final_section: Dict[str, Any]) -> str:
    """Render final section"""
    html = ""
    for clause in final_section.get("clauses", []):
        html += f'<div class="clause"><strong>{clause.get("title", "")}</strong><br>{clause.get("content", "")}</div>'
    
    signatures = final_section.get("signatures", {})
    if signatures:
        html += f'<div class="signature-section"><p>{signatures.get("text", "")}</p>'
        for party in signatures.get("parties", []):
            html += f'<p><strong>{party}</strong></p>'
        html += '</div>'
    
    return html

