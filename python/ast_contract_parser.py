#!/usr/bin/env python3
"""
AST Contract Parser
Generates Mexican-style contracts from LAML AST following the specified structure.
"""

import json
import sys
import os
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

class ASTContractParser:
    def __init__(self, ast_file: str, use_api_improvement: bool = False):
        """Initialize parser with AST file."""
        # Load environment variables from .env file
        load_dotenv()
        
        with open(ast_file, 'r', encoding='utf-8') as f:
            self.ast = json.load(f)
        
        self.contract = {
            "metadata": {},
            "parties_block": {},
            "objects_section": {},
            "declarations_section": {},
            "clauses_section": [],
            "final_section": {}
        }
        
        self.use_api_improvement = use_api_improvement
        
        # Initialize Anthropic client if API improvement is enabled
        if self.use_api_improvement:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required for API improvement")
            self.anthropic = Anthropic(api_key=api_key)
    
    def parse_contract(self) -> Dict[str, Any]:
        """Parse AST and generate contract structure."""
        # Extract normativa from imports
        self._extract_normativa()
        
        # Extract contract title from first institution
        self._extract_contract_title()
        
        # Extract parties from institution parameters
        self._extract_parties()
        
        # Extract objects from institution parameters
        self._extract_objects()
        
        # Generate objects section from statements
        self._generate_objects_section()
        
        # Generate declarations
        self._generate_declarations()
        
        # Generate clauses from statements and rules
        self._generate_clauses()
        
        # Generate final section
        self._generate_final_section()
        
        return self.contract
    
    def _extract_normativa(self):
        """Extract legal references from imports."""
        imports = self.ast.get('imports', [])
        if imports:
            # Use import paths directly as legal references
            self.contract["metadata"]["normativa"] = imports
    
    def _extract_contract_title(self):
        """Extract contract title from first institution name."""
        institutions = self.ast.get('institutions', [])
        if institutions:
            first_institution = institutions[0]
            institution_name = first_institution.get('name', '')
            
            # Use institution name directly as contract title
            self.contract["metadata"]["title"] = f"CONTRATO DE {institution_name.upper()}"
    
    def _extract_parties(self):
        """Extract parties from institution parameters."""
        institutions = self.ast.get('institutions', [])
        if not institutions:
            return
        
        first_institution = institutions[0]
        parameters = first_institution.get('parameters', [])
        bindings = first_institution.get('bindings', [])
        
        parties = []
        for param in parameters:
            # Find binding for this parameter
            binding = next((b for b in bindings if b.get('variable') == param), None)
            if binding and binding.get('base_type') == 'Person':
                parties.append({
                    "name": param,
                    "predicate": binding.get('predicate', param),
                    "subtype": binding.get('subtype', '_'),
                    "role": self._determine_party_role(param)
                })
        
        self.contract["parties_block"] = {
            "parties": parties
        }
    
    def _determine_party_role(self, param_name: str) -> str:
        """Determine party role from parameter name."""
        return param_name
    
    def _extract_objects(self):
        """Extract objects from institution parameters."""
        institutions = self.ast.get('institutions', [])
        if not institutions:
            return
        
        first_institution = institutions[0]
        parameters = first_institution.get('parameters', [])
        bindings = first_institution.get('bindings', [])
        
        objects = []
        for param in parameters:
            binding = next((b for b in bindings if b.get('variable') == param), None)
            if binding and binding.get('base_type') in ['Thing', 'Service']:
                objects.append({
                    "name": param,
                    "predicate": binding.get('predicate', param),
                    "base_type": binding.get('base_type'),
                    "subtype": binding.get('subtype', '_')
                })
        
        self.contract["objects"] = objects
    
    def _int_to_roman(self, num: int) -> str:
        """Convert integer to Roman numeral."""
        if num <= 0:
            return ""
        
        # Roman numeral mapping
        values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        symbols = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        
        result = ""
        for i in range(len(values)):
            count = num // values[i]
            result += symbols[i] * count
            num -= values[i] * count
        
        return result

    def _generate_objects_section(self):
        """Generate objects section from things (not acts)."""
        institutions = self.ast.get('institutions', [])
        if not institutions:
            return
        
        first_institution = institutions[0]
        parameters = first_institution.get('parameters', [])
        bindings = first_institution.get('bindings', [])
        
        objects = []
        thing_count = 0
        
        # Create a mapping of parameter names to their bindings
        param_bindings = {}
        for binding in bindings:
            variable = binding.get('variable', '')
            if variable in parameters:
                param_bindings[variable] = binding
        
        for param_name in parameters:
            if param_name in param_bindings:
                binding = param_bindings[param_name]
                
                # Check if this parameter is a Thing
                if binding.get('base_type') == 'Thing':
                    thing_count += 1
                    roman_numeral = self._int_to_roman(thing_count)
                    
                    # Get subtype for description
                    subtype = binding.get('subtype', '_')
                    if subtype == 'movable':
                        description = f"bien mueble denominado {param_name}"
                    elif subtype == 'immovable':
                        description = f"bien inmueble denominado {param_name}"
                    else:
                        description = f"objeto denominado {param_name}"
                    
                    objects.append({
                        "name": param_name,
                        "description": description,
                        "roman_numeral": roman_numeral
                    })
        
        self.contract["objects_section"] = {
            "objects": objects
        }
    
    def _generate_declarations(self):
        """Generate party declarations."""
        parties = self.contract["parties_block"]["parties"]
        declarations = []
        
        for i, party in enumerate(parties):
            party_declaration = {
                "party": party["name"],
                "role": party["role"],
                "items": []
            }
            
            # Generate declaration items based on party type
            if party["subtype"] == "corporate" or party["role"] in ["arrendador", "propietaria"]:
                party_declaration["items"].extend([
                    f"Declara '{party['predicate'].upper()}', ser persona moral con capacidad legal para contratar y obligarse en el presente contrato.",
                    f"Que cuenta con la capacidad legal y económica para la celebración de este contrato.",
                    f"Que es la legítima {party['role']} del objeto materia del presente contrato."
                ])
            else:
                party_declaration["items"].extend([
                    f"Declara '{party['predicate'].upper()}', ser persona física con capacidad legal para contratar y obligarse en el presente contrato.",
                    f"Que cuenta con la capacidad legal y económica para la celebración de este contrato.",
                    f"Que desea adquirir los derechos de {party['role']} en el presente contrato."
                ])
            
            declarations.append(party_declaration)
        
        # Add mutual declarations
        mutual_declaration = {
            "type": "mutual",
            "items": [
                "Que se reconocen la personalidad con la que se ostentan dentro del presente contrato por lo que el mismo carece de vicios, dolo o mala fe.",
                "Que cuentan con la capacidad legal y económica para la celebración de este contrato.",
                "Que ambas partes conocen la naturaleza del presente contrato, saben y aceptan sus condiciones, así como el alcance de sus efectos respecto del cumplimiento o incumplimiento del mismo."
            ]
        }
        declarations.append(mutual_declaration)
        
        self.contract["declarations_section"] = {
            "declarations": declarations
        }
    
    def _generate_clauses(self):
        """Generate clauses from statements and rules."""
        institutions = self.ast.get('institutions', [])
        if not institutions:
            return
        
        clauses = []
        clause_number = 1
        
        # Process ONLY the first institution (contract), not imported laws
        first_institution = institutions[0]
        statements = first_institution.get('statements', [])
        rules = first_institution.get('rules', [])
        
        # Generate clauses from statements (acts and facts)
        for stmt in statements:
            clause = self._generate_statement_clause(stmt, clause_number)
            if clause:
                clauses.append(clause)
                clause_number += 1
        
        # Generate clauses from rules
        for rule in rules:
            clause = self._generate_rule_clause(rule, clause_number)
            if clause:
                clauses.append(clause)
                clause_number += 1
        
        self.contract["clauses_section"] = clauses
    
    def _generate_final_section(self):
        """Generate final section with standard clauses."""
        parties = self.contract["parties_block"]["parties"]
        party_names = [p["predicate"] for p in parties]
        
        # Calculate final clause numbers based on existing clauses
        existing_clauses = len(self.contract["clauses_section"])
        final_clauses = [
            {
                "id": f"Cláusula {existing_clauses + 1}",
                "title": "TERMINACIÓN",
                "content": "Las partes podrán dar por terminado el presente contrato por mutuo acuerdo, el cual deberá constar por escrito."
            },
            {
                "id": f"Cláusula {existing_clauses + 2}", 
                "title": "JURISDICCIÓN",
                "content": "Las partes se someten a la jurisdicción de los Tribunales competentes para la interpretación y ejecución de los pactos que anteceden."
            },
            {
                "id": f"Cláusula {existing_clauses + 3}",
                "title": "GASTOS", 
                "content": "Las partes convienen en que los gastos, derechos y honorarios que devengue el otorgamiento respectivo, serán por cuenta y cargo de las partes."
            }
        ]
        
        signatures = {
            "text": "Así convenido y sabedores del valor, fuerza y alcance legales del contenido de este contrato, las partes lo firman por duplicado a los _____ días del mes de _____.",
            "parties": party_names
        }
        
        self.contract["final_section"] = {
            "clauses": final_clauses,
            "signatures": signatures
        }
    
    def _generate_statement_clause(self, stmt: Dict[str, Any], clause_number: int) -> Optional[Dict[str, Any]]:
        """Generate clause from statement."""
        name = stmt.get('name', '')
        stmt_type = stmt.get('statement_type', '')
        parameters = stmt.get('parameters', [])
        
        if stmt_type == 'act':
            # Generate act description
            if len(parameters) >= 3:
                subject = parameters[0]
                object_param = parameters[1] if len(parameters) > 1 else parameters[-1]
                indirect_object = parameters[-1] if len(parameters) > 2 else None
                
                # Use parameter names directly
                subject_nl = subject
                object_nl = object_param
                indirect_nl = indirect_object if indirect_object else ""
                
                description = f"el acto jurídico que realiza {subject_nl} frente a {indirect_nl} con objeto de {object_nl}"
                
                return {
                    "id": f"Cláusula {clause_number}",
                    "title": f"ACTO DE {name.upper().replace('_', ' ')}",
                    "content": f"Las partes reconocen {description}.",
                    "type": "statement_act"
                }
        
        return None
    
    def _generate_rule_clause(self, rule: Dict[str, Any], clause_number: int) -> Optional[Dict[str, Any]]:
        """Generate clause from rule."""
        name = rule.get('name', '')
        expression = rule.get('expression', {})
        
        # Parse rule expression to generate natural language
        clause_text = self._parse_rule_expression(expression)
        
        if clause_text:
            return {
                "id": f"Cláusula {clause_number}",
                "title": f"OBLIGACIÓN DE {name.upper().replace('RULE_', '')}",
                "content": clause_text,
                "type": "rule_obligation"
            }
        
        return None
    
    def _parse_rule_expression(self, expression: Dict[str, Any]) -> str:
        """Parse rule expression to natural language (recursive)."""
        expr_type = expression.get('expression_type', '')
        
        if expr_type == 'binary_operation':
            operator = expression.get('operator', '')
            left = expression.get('left', {})
            right = expression.get('right', {})
            
            if operator == 'implies':
                condition = self._parse_rule_expression(left)  # Recursive call
                consequence = self._parse_rule_expression(right)  # Recursive call
                return f"En el supuesto de que {condition}, entonces {consequence}"
            elif operator == 'and':
                left_text = self._parse_rule_expression(left)
                right_text = self._parse_rule_expression(right)
                return f"{left_text} y {right_text}"
            elif operator == 'or':
                left_text = self._parse_rule_expression(left)
                right_text = self._parse_rule_expression(right)
                return f"{left_text} o {right_text}"
            elif operator == 'not':
                # Handle 'not' as binary_operation (AST issue) with left: null
                if left is None or left == {}:
                    right_text = self._parse_rule_expression(right)
                    return f"no se cumpla con que {right_text}"
                else:
                    # Fallback for other binary 'not' cases
                    left_text = self._parse_rule_expression(left)
                    right_text = self._parse_rule_expression(right)
                    return f"no ({left_text} {right_text})"
        
        elif expr_type == 'unary_operation':
            operator = expression.get('operator', '')
            right = expression.get('right', {})
            if operator == 'not':
                right_text = self._parse_rule_expression(right)
                return f"no se cumpla con que {right_text}"
        
        elif expr_type == 'predicate':
            return self._parse_predicate_expression(expression)
        
        return "[EXPRESIÓN DESCONOCIDA]"
    
    def _get_type_bindings_for_predicate(self, predicate_name: str, args: List[str]) -> Dict[str, str]:
        """Get type bindings for a predicate from the AST."""
        institutions = self.ast.get('institutions', [])
        if not institutions:
            return {}
        
        # Look through all institutions for the predicate
        for institution in institutions:
            statements = institution.get('statements', [])
            for stmt in statements:
                if stmt.get('name') == predicate_name:
                    bindings = stmt.get('bindings', [])
                    type_map = {}
                    for binding in bindings:
                        variable = binding.get('variable', '')
                        base_type = binding.get('base_type', '')
                        # Map variable to its type regardless of whether it's in args
                        type_map[variable] = base_type
                    return type_map
        return {}
    
    def _infer_verb_from_types(self, predicate_name: str, args: List[str]) -> str:
        """Infer appropriate verb based on type bindings from AST."""
        type_bindings = self._get_type_bindings_for_predicate(predicate_name, args)
        
        if len(args) >= 3:
            subject = args[0]
            object_param = args[1] 
            indirect_object = args[2]
            
            subject_type = type_bindings.get(subject, '')
            object_type = type_bindings.get(object_param, '')
            indirect_type = type_bindings.get(indirect_object, '')
            
            # Infer verb based on complete legal drafting patterns by type combinations
            if subject_type == 'Person' and object_type == 'Thing' and indirect_type == 'Person':
                # Thing between two Persons - determine legal drafting pattern
                action = predicate_name.replace('_', ' ').capitalize()
                return f"'{subject}' transfiere {action} de '{object_param}' a '{indirect_object}'"
            elif subject_type == 'Person' and object_type == 'Thing':
                # Person acts on Thing
                action = predicate_name.replace('_', ' ').capitalize()
                return f"'{subject}' posee {action} de '{object_param}'"
            elif subject_type == 'Person' and object_type == 'Service' and indirect_type == 'Person':
                # Service between two Persons
                action = predicate_name.replace('_', ' ').capitalize()
                return f"'{subject}' presta {action} a '{indirect_object}'"
            elif subject_type == 'Person' and object_type == 'Service':
                # Person performs Service
                action = predicate_name.replace('_', ' ').capitalize()
                return f"'{subject}' ejecuta {action}"
            elif subject_type == 'Person' and indirect_type == 'Person':
                # Direct Person to Person relationship
                action = predicate_name.replace('_', ' ').capitalize()
                return f"'{subject}' se relaciona con '{indirect_object}' mediante {action}"
            else:
                # Generic fallback for any type combination
                action = predicate_name.replace('_', ' ').capitalize()
                return f"'{subject}' realiza {action}"
        
        # Fallback for other cases
        action = predicate_name.replace('_', ' ').capitalize()
        if len(args) >= 2:
            return f"se ejecutará {action} entre '{args[0]}' y '{args[1]}'"
        else:
            return f"se ejecutará {action}"
    
    def _parse_predicate_expression(self, expr: Dict[str, Any]) -> str:
        """Parse predicate expression to natural language."""
        if expr.get('expression_type') == 'predicate':
            predicate = expr.get('predicate', {})
            name = predicate.get('name', '')
            modal = predicate.get('modal', '')
            args = predicate.get('args', [])
            
            # Infer verb dynamically from type bindings
            text = self._infer_verb_from_types(name, args)
            
            # Apply modal operators
            if modal == 'oblig':
                if len(args) >= 1:
                    return f"'{args[0]}' queda obligado a {text.replace(f"'{args[0]}'", '', 1).strip()}"
                else:
                    return f"se obliga a {text}"
            elif modal == 'claim':
                if len(args) >= 3:
                    return f"'{args[2]}' tiene el derecho de exigir que {text}"
                else:
                    return f"tiene derecho a {text}"
            elif modal == 'forbid':
                return f"se prohíbe {text}"
            else:
                return f"se realiza el acto donde {text}"
        
        return ""
    
    def _improve_drafting_with_api(self, text: str) -> str:
        """Use Anthropic API to improve legal drafting quality."""
        if not self.use_api_improvement:
            return text
        
        prompt = f"""
        Improve the legal drafting quality of this contract text while preserving all content, structure, and legal logic:
        
        {text}
        
        Requirements:
        - Use professional Mexican legal terminology
        - Improve sentence structure and flow
        - Maintain all party names, object names, and clause numbers
        - Keep the same contract structure and formatting
        - Use formal legal language appropriate for Mexican contracts
        - Preserve all legal obligations, claims, and conditions exactly
        - Only improve the language quality, not the content
        """
        
        try:
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return response.content[0].text
        except Exception as e:
            print(f"API improvement failed: {e}")
            return text  # Return original text if API fails
    
    def _improve_clause_drafting(self, clause: Dict[str, Any]) -> Dict[str, Any]:
        """Improve drafting for a single clause."""
        if not self.use_api_improvement:
            return clause
        
        clause_text = f"Cláusula {clause.get('id', '')}.- {clause.get('title', '')}.- {clause.get('content', '')}"
        improved_text = self._improve_drafting_with_api(clause_text)
        
        # Parse the improved text back into clause structure
        # This is a simplified approach - you might want more sophisticated parsing
        return {
            "id": clause.get('id', ''),
            "title": clause.get('title', ''),
            "content": improved_text.split('.- ', 2)[-1] if '.- ' in improved_text else clause.get('content', '')
        }

    def render_contract(self) -> str:
        """Render the contract to natural language."""
        contract = self.contract
        
        # Header
        output = []
        output.append(contract["metadata"]["title"])
        output.append("")
        
        # Normativa
        if "normativa" in contract["metadata"]:
            output.append("Normativa: " + "; ".join(contract["metadata"]["normativa"]))
            output.append("")
        
        # Supuesto
        parties = contract["parties_block"]["parties"]
        party_names = [p["role"] for p in parties]
        supuesto = f"Contrato de {contract['metadata']['title'].split()[-1].lower()} entre {', '.join(party_names)}."
        output.append(f"Supuesto: {supuesto}")
        output.append("")
        
        # Preamble
        preamble = f"CONTRATO QUE CONSTITUYEN {', '.join([p['predicate'].upper() for p in parties])}, SUJETÁNDOSE PARA ELLO LA TENOR DE LAS SIGUIENTES DECLARACIONES Y CLÁUSULAS:"
        output.append(preamble)
        output.append("")
        
        # Objects section
        if "objects_section" in contract and contract["objects_section"]["objects"]:
            output.append("OBJETOS")
            objects = contract["objects_section"]["objects"]
            for obj in objects:
                roman_numeral = obj.get('roman_numeral', 'I')
                output.append(f"{roman_numeral}.- {obj['name'].upper()}.- {obj['description']}.")
            output.append("")
        
        # Declarations
        output.append("DECLARACIONES")
        declarations = contract["declarations_section"]["declarations"]
        
        for i, declaration in enumerate(declarations):
            roman_numeral = self._int_to_roman(i + 1)
            if declaration.get("type") == "mutual":
                output.append(f"{roman_numeral}.-- Declaran ambas partes:")
            else:
                output.append(f"{roman_numeral}.-- Declara \"{declaration['party']}\":")
            
            for j, item in enumerate(declaration["items"]):
                output.append(f"{chr(97 + j)}. {item}")
            output.append("")
        
        # Clauses
        output.append("CLÁUSULAS")
        clauses = contract["clauses_section"]
        
        for clause in clauses:
            output.append(f"{clause['id']}.- {clause['title']}.- {clause['content']}")
            output.append("")
        
        # Final section
        if "final_section" in contract:
            final_clauses = contract["final_section"]["clauses"]
            for clause in final_clauses:
                output.append(f"{clause['id']}.- {clause['title']}.- {clause['content']}")
                output.append("")
            
            # Signatures
            signatures = contract["final_section"]["signatures"]
            output.append(signatures["text"])
            output.append("")
            
            for party in signatures["parties"]:
                output.append(f"EL {party.upper()}")
                output.append("")
        
        # Join the output
        contract_text = "\n".join(output)
        
        # Apply API improvement if enabled
        if self.use_api_improvement:
            contract_text = self._improve_drafting_with_api(contract_text)
        
        return contract_text

    def render_contract_html(self) -> str:
        """Render the contract to HTML format."""
        contract = self.contract
        
        # Start HTML document
        html_parts = []
        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html lang='es'>")
        html_parts.append("<head>")
        html_parts.append("    <meta charset='UTF-8'>")
        html_parts.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html_parts.append("    <title>Contrato Legal</title>")
        html_parts.append("    <style>")
        html_parts.append("        body { font-family: 'Times New Roman', serif; line-height: 1.6; margin: 40px; }")
        html_parts.append("        .contract-title { text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 30px; }")
        html_parts.append("        .section-title { font-size: 18px; font-weight: bold; margin-top: 30px; margin-bottom: 15px; text-transform: uppercase; }")
        html_parts.append("        .clause { margin-bottom: 15px; }")
        html_parts.append("        .clause-id { font-weight: bold; }")
        html_parts.append("        .declaration { margin-bottom: 20px; }")
        html_parts.append("        .declaration-title { font-weight: bold; margin-bottom: 10px; }")
        html_parts.append("        .declaration-item { margin-left: 20px; margin-bottom: 5px; }")
        html_parts.append("        .object-item { margin-bottom: 10px; }")
        html_parts.append("        .signature-section { margin-top: 40px; text-align: center; }")
        html_parts.append("        .signature-line { margin: 20px 0; }")
        html_parts.append("    </style>")
        html_parts.append("</head>")
        html_parts.append("<body>")
        
        # Contract title
        html_parts.append(f"    <div class='contract-title'>{contract['metadata']['title']}</div>")
        
        # Normativa
        if "normativa" in contract["metadata"]:
            html_parts.append(f"    <p><strong>Normativa:</strong> {'; '.join(contract['metadata']['normativa'])}</p>")
        
        # Supuesto
        parties = contract["parties_block"]["parties"]
        party_names = [p["role"] for p in parties]
        supuesto = f"Contrato de {contract['metadata']['title'].split()[-1].lower()} entre {', '.join(party_names)}."
        html_parts.append(f"    <p><strong>Supuesto:</strong> {supuesto}</p>")
        
        # Preamble
        preamble = f"CONTRATO QUE CONSTITUYEN {', '.join([p['predicate'].upper() for p in parties])}, SUJETÁNDOSE PARA ELLO LA TENOR DE LAS SIGUIENTES DECLARACIONES Y CLÁUSULAS:"
        html_parts.append(f"    <p>{preamble}</p>")
        
        # Objects section
        if "objects_section" in contract and contract["objects_section"]["objects"]:
            html_parts.append("    <div class='section-title'>OBJETOS</div>")
            objects = contract["objects_section"]["objects"]
            for obj in objects:
                roman_numeral = obj.get('roman_numeral', 'I')
                html_parts.append(f"    <div class='object-item'>{roman_numeral}.- <strong>{obj['name'].upper()}</strong>.- {obj['description']}.</div>")
        
        # Declarations
        html_parts.append("    <div class='section-title'>DECLARACIONES</div>")
        declarations = contract["declarations_section"]["declarations"]
        
        for i, declaration in enumerate(declarations):
            roman_numeral = self._int_to_roman(i + 1)
            html_parts.append("    <div class='declaration'>")
            
            if declaration.get("type") == "mutual":
                html_parts.append(f"        <div class='declaration-title'>{roman_numeral}.-- Declaran ambas partes:</div>")
            else:
                html_parts.append(f"        <div class='declaration-title'>{roman_numeral}.-- Declara \"{declaration['party']}\":</div>")
            
            for j, item in enumerate(declaration["items"]):
                html_parts.append(f"        <div class='declaration-item'>{chr(97 + j)}. {item}</div>")
            
            html_parts.append("    </div>")
        
        # Clauses
        html_parts.append("    <div class='section-title'>CLÁUSULAS</div>")
        clauses = contract["clauses_section"]
        
        for clause in clauses:
            html_parts.append(f"    <div class='clause'>")
            html_parts.append(f"        <span class='clause-id'>{clause['id']}.- {clause['title']}.-</span> {clause['content']}")
            html_parts.append(f"    </div>")
        
        # Final section
        if "final_section" in contract and contract["final_section"]:
            final_section = contract["final_section"]
            
            for clause in final_section.get("clauses", []):
                html_parts.append(f"    <div class='clause'>")
                html_parts.append(f"        <span class='clause-id'>{clause['id']}.- {clause['title']}.-</span> {clause['content']}")
                html_parts.append(f"    </div>")
            
            # Signatures
            if "signatures" in final_section:
                signatures = final_section["signatures"]
                html_parts.append("    <div class='signature-section'>")
                html_parts.append(f"        <p>{signatures.get('text', '')}</p>")
                html_parts.append("        <br>")
                
                for party in signatures["parties"]:
                    html_parts.append(f"        <div class='signature-line'>EL {party.upper()}</div>")
                    html_parts.append("        <br>")
                
                html_parts.append("    </div>")
        
        # Close HTML
        html_parts.append("</body>")
        html_parts.append("</html>")
        
        # Join the HTML
        html_content = "\n".join(html_parts)
        
        # Apply API improvement if enabled
        if self.use_api_improvement:
            html_content = self._improve_drafting_with_api(html_content)
        
        return html_content

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: python ast_contract_parser.py <ast_file> [--api-improvement] [--html]")
        sys.exit(1)
    
    ast_file = sys.argv[1]
    use_api_improvement = "--api-improvement" in sys.argv
    use_html = "--html" in sys.argv
    
    parser = ASTContractParser(ast_file, use_api_improvement=use_api_improvement)
    
    # Parse contract
    contract = parser.parse_contract()
    
    # Render to output format
    if use_html:
        output = parser.render_contract_html()
        # Save HTML to file
        output_file = "contract.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"HTML contract saved to: {output_file}")
    else:
        output = parser.render_contract()
        print(output)

if __name__ == "__main__":
    main()
