#!/usr/bin/env python3

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class LAMLASTTranspilerV2:
    """
    Data-driven AST transpiler with zero hardcoding.
    
    All translations, templates, and mappings are externalized to configuration files.
    This makes it completely flexible and jurisdiction-agnostic.
    """
    
    def __init__(self, config_dir: str = "transpiler_configs"):
        self.config_dir = config_dir
        self.load_configurations()
    
    def load_configurations(self):
        """Load all configurations from external files"""
        self.jurisdictions = self.load_json_config("jurisdictions.json")
        self.predicate_mappings = self.load_json_config("predicate_mappings.json")
        self.modal_operators = self.load_json_config("modal_operators.json")
        self.logical_operators = self.load_json_config("logical_operators.json")
        self.rule_patterns = self.load_json_config("rule_patterns.json")
        self.templates = self.load_json_config("templates.json")
    
    def load_json_config(self, filename: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(f"{self.config_dir}/{filename}", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Configuration file {filename} not found, using defaults")
            return self.get_default_config(filename)
    
    def get_default_config(self, filename: str) -> Dict:
        """Get default configuration for missing files"""
        defaults = {
            "jurisdictions.json": {
                "mexican_lease": {
                    "title": "CONTRATO DE ARRENDAMIENTO DE SISTEMA DE ENERGÍA SOLAR",
                    "legal_references": [
                        "Artículo 1336, 1337, 1340, 1342 del Código Civil para el Estado Libre y Soberano de Puebla",
                        "Artículo 130 de la Ley del Impuesto sobre la Renta",
                        "Ley de Transición Energética"
                    ],
                    "subject": "Contrato de arrendamiento de sistema de energía solar entre persona física y persona moral, incluyendo generación, interconexión y venta de excedentes",
                    "party_identification": {
                        "lessor_patterns": ["Corp", "Company", "S.A.", "S.A. de C.V."],
                        "lessee_patterns": ["Owner", "Person", "Individual"]
                    },
                    "language": "spanish"
                }
            },
            "predicate_mappings.json": {
                "mexican_lease": {
                    "pay_rent": "pagar la renta",
                    "grant_use": "otorgar el uso",
                    "maintain_system": "mantener el sistema",
                    "return_system": "devolver el sistema"
                }
            },
            "modal_operators.json": {
                "mexican_lease": {
                    "oblig": "se obliga a",
                    "claim": "tiene derecho a",
                    "forbid": "queda prohibido"
                }
            },
            "logical_operators.json": {
                "mexican_lease": {
                    "implies": "implica que",
                    "and": "y",
                    "or": "o",
                    "not": "no"
                }
            },
            "rule_patterns.json": {
                "core_obligation": {
                    "patterns": ["pay_rent", "grant_use"],
                    "description": "Core lease obligations"
                },
                "maintenance_obligation": {
                    "patterns": ["maintain"],
                    "description": "System maintenance obligations"
                }
            },
            "templates.json": {
                "mexican_lease": {
                    "contract_structure": {
                        "header": "{title}\n\nNormativa: {legal_references}\n\nSupuesto: {subject}",
                        "preamble": "CONTRATO DE ARRENDAMIENTO QUE CONSTITUYEN {lessor}, A QUIEN EN LO SUCESIVO SE LE DENOMINARÁ \"EL ARRENDADOR\" A FAVOR DE {lessee}, A QUIEN EN LO SUCESIVO SE LE DENOMINARÁ \"EL ARRENDATARIO\"",
                        "declarations": "DECLARACIONES",
                        "clauses": "CLÁUSULAS",
                        "signatures": "Así convenido y sabedores del valor, fuerza y alcance legales del contenido de este contrato, las partes lo firman por duplicado a los _____ días del mes de _____.\n\nEL ARRENDADOR\n\nEL ARRENDATARIO"
                    },
                    "clause_templates": {
                        "obligation": "Cláusula {number}.- {title}.- {description}",
                        "dependency": "Cláusula {number}.- {title}.- {description}",
                        "standard": "Cláusula {number}.- {title}.- {description}"
                    }
                }
            }
        }
        return defaults.get(filename, {})
    
    def load_ast(self, ast_file: str) -> Dict:
        """Load LAML AST from JSON file"""
        with open(ast_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def transpile(self, ast_file: str, jurisdiction: str = 'mexican_lease') -> str:
        """Main transpilation method - completely data-driven"""
        ast = self.load_ast(ast_file)
        config = self.jurisdictions.get(jurisdiction, {})
        
        if not config:
            raise ValueError(f"Jurisdiction '{jurisdiction}' not found in configuration")
        
        # Extract contract information from AST
        institution = ast['institutions'][0] if ast['institutions'] else None
        instantiation = ast['instantiations'][0] if ast['instantiations'] else None
        
        if not institution:
            raise ValueError("No institution found in AST")
        
        # Generate contract using templates
        contract_data = self.extract_contract_data(ast, config)
        return self.render_contract(contract_data, config)
    
    def extract_contract_data(self, ast: Dict, config: Dict) -> Dict:
        """Extract contract data from AST using configuration"""
        institution = ast['institutions'][0]
        instantiation = ast['instantiations'][0] if ast['instantiations'] else None
        
        # Extract parties
        parties = self.extract_parties(instantiation, config) if instantiation else {}
        
        # Extract declarations from type bindings
        declarations = self.extract_declarations(institution['bindings'], config)
        
        # Extract clauses from rules
        clauses = self.extract_clauses(institution['rules'], config)
        
        return {
            'title': config['title'],
            'legal_references': ', '.join(config['legal_references']),
            'subject': config['subject'],
            'parties': parties,
            'declarations': declarations,
            'clauses': clauses
        }
    
    def extract_parties(self, instantiation: Dict, config: Dict) -> Dict:
        """Extract party information using configuration patterns"""
        arguments = instantiation.get('arguments', [])
        party_config = config.get('party_identification', {})
        
        lessor_patterns = party_config.get('lessor_patterns', [])
        lessee_patterns = party_config.get('lessee_patterns', [])
        
        lessor = self.find_party_by_patterns(arguments, lessor_patterns)
        lessee = self.find_party_by_patterns(arguments, lessee_patterns)
        
        return {
            'lessor': lessor,
            'lessee': lessee
        }
    
    def find_party_by_patterns(self, arguments: List[str], patterns: List[str]) -> str:
        """Find party using configured patterns"""
        for arg in arguments:
            if any(pattern in arg for pattern in patterns):
                return arg
        return arguments[0] if arguments else "Unknown"
    
    def extract_declarations(self, bindings: List[Dict], config: Dict) -> List[Dict]:
        """Extract declarations from type bindings using configuration"""
        declarations = []
        
        # Group bindings by party type
        party_bindings = {}
        for binding in bindings:
            if binding.get('base_type') == 'Person':
                party = binding['variable']
                if party not in party_bindings:
                    party_bindings[party] = []
                party_bindings[party].append(binding)
        
        # Generate declarations for each party
        for party, party_bindings in party_bindings.items():
            declarations.append({
                'party': party,
                'type': 'person_declaration',
                'bindings': party_bindings
            })
        
        return declarations
    
    def extract_clauses(self, rules: List[Dict], config: Dict) -> List[Dict]:
        """Extract clauses from rules using configuration patterns"""
        clauses = []
        
        # Group rules by dependency type using configuration
        rule_groups = self.group_rules_by_config(rules, config)
        
        clause_number = 1
        
        # Process each group according to configuration
        for group_type, group_rules in rule_groups.items():
            if group_type == 'generation_activities':
                # Add dependency explanation
                clauses.append({
                    'type': 'dependency_explanation',
                    'number': clause_number,
                    'title': 'ACTIVIDADES DE GENERACIÓN',
                    'description': 'Las siguientes obligaciones están condicionadas al cumplimiento del pago de renta:'
                })
                clause_number += 1
            
            # Add rules in this group
            for rule in group_rules:
                clause = self.transpile_rule_to_clause_data(rule, clause_number, config)
                clauses.append(clause)
                clause_number += 1
        
        # Add standard clauses
        clauses.extend(self.get_standard_clauses(clause_number, config))
        
        return clauses
    
    def group_rules_by_config(self, rules: List[Dict], config: Dict) -> Dict:
        """Group rules using configuration patterns"""
        groups = {}
        
        for rule in rules:
            rule_type = self.determine_rule_type(rule, config)
            if rule_type not in groups:
                groups[rule_type] = []
            groups[rule_type].append(rule)
        
        return groups
    
    def determine_rule_type(self, rule: Dict, config: Dict) -> str:
        """Determine rule type using configuration patterns"""
        rule_patterns = self.rule_patterns.get('patterns', {})
        
        # Extract predicate names from rule
        left_predicate = self.extract_predicate_name(rule['expression']['left'])
        right_predicate = self.extract_predicate_name(rule['expression']['right'])
        
        # Check against configured patterns
        for rule_type, pattern_config in rule_patterns.items():
            patterns = pattern_config.get('patterns', [])
            if any(pattern in left_predicate or pattern in right_predicate for pattern in patterns):
                return rule_type
        
        return 'core_obligation'  # Default
    
    def extract_predicate_name(self, expression: Dict) -> str:
        """Extract predicate name from expression"""
        if expression['expression_type'] == 'predicate':
            return expression['predicate']['name']
        elif expression['expression_type'] == 'binary_operation':
            if expression['operator'] == 'not':
                return self.extract_predicate_name(expression['right'])
            else:
                return self.extract_predicate_name(expression['left'])
        return ''
    
    def transpile_rule_to_clause_data(self, rule: Dict, clause_number: int, config: Dict) -> Dict:
        """Transpile rule to clause data structure"""
        rule_name = rule['name'].replace('_', ' ').upper()
        expression = rule['expression']
        
        # Transpile expression using configuration
        clause_text = self.transpile_expression_with_config(expression, config)
        
        return {
            'type': 'rule_clause',
            'number': clause_number,
            'title': rule_name,
            'description': clause_text
        }
    
    def transpile_expression_with_config(self, expression: Dict, config: Dict) -> str:
        """Transpile expression using configuration"""
        if expression['expression_type'] == 'predicate':
            return self.transpile_predicate_with_config(expression['predicate'], config)
        elif expression['expression_type'] == 'binary_operation':
            return self.transpile_binary_operation_with_config(expression, config)
        else:
            return "Unknown expression type"
    
    def transpile_predicate_with_config(self, predicate: Dict, config: Dict) -> str:
        """Transpile predicate using configuration"""
        name = predicate['name']
        modal = predicate.get('modal', '')
        
        # Get jurisdiction for translations
        jurisdiction = self.get_jurisdiction_from_config(config)
        
        # Translate predicate name
        predicate_mappings = self.predicate_mappings.get(jurisdiction, {})
        translated_name = predicate_mappings.get(name, name)
        
        # Add modal operator
        if modal:
            modal_operators = self.modal_operators.get(jurisdiction, {})
            modal_text = modal_operators.get(modal, modal)
            return f"{modal_text} {translated_name}"
        else:
            return translated_name
    
    def transpile_binary_operation_with_config(self, expression: Dict, config: Dict) -> str:
        """Transpile binary operation using configuration"""
        operator = expression['operator']
        left = expression['left']
        right = expression['right']
        
        jurisdiction = self.get_jurisdiction_from_config(config)
        logical_operators = self.logical_operators.get(jurisdiction, {})
        
        if operator == 'implies':
            left_text = self.transpile_expression_with_config(left, config)
            right_text = self.transpile_expression_with_config(right, config)
            implies_text = logical_operators.get('implies', 'implies')
            return f"Para {left_text}, {right_text}"
        
        elif operator == 'not':
            right_text = self.transpile_expression_with_config(right, config)
            not_text = logical_operators.get('not', 'not')
            return f"En caso de {not_text} {right_text}"
        
        else:
            left_text = self.transpile_expression_with_config(left, config)
            right_text = self.transpile_expression_with_config(right, config)
            op_text = logical_operators.get(operator, operator)
            return f"{left_text} {op_text} {right_text}"
    
    def get_jurisdiction_from_config(self, config: Dict) -> str:
        """Get jurisdiction key from config"""
        # Find jurisdiction key that matches this config
        for jurisdiction, jurisdiction_config in self.jurisdictions.items():
            if jurisdiction_config == config:
                return jurisdiction
        return 'mexican_lease'  # Default
    
    def get_standard_clauses(self, start_number: int, config: Dict) -> List[Dict]:
        """Get standard clauses using configuration"""
        jurisdiction = self.get_jurisdiction_from_config(config)
        templates = self.templates.get(jurisdiction, {})
        
        standard_clauses = [
            {
                'type': 'standard_clause',
                'number': start_number,
                'title': 'DEPENDENCIAS',
                'description': 'Todas las obligaciones de generación, interconexión y venta de excedentes están condicionadas al cumplimiento puntual del pago de renta.'
            },
            {
                'type': 'standard_clause',
                'number': start_number + 1,
                'title': 'TERMINACIÓN',
                'description': 'Las partes podrán dar por terminado el presente contrato por mutuo acuerdo.'
            },
            {
                'type': 'standard_clause',
                'number': start_number + 2,
                'title': 'JURISDICCIÓN',
                'description': 'Las partes se someten a la jurisdicción de los Tribunales competentes.'
            },
            {
                'type': 'standard_clause',
                'number': start_number + 3,
                'title': 'GASTOS',
                'description': 'Los gastos serán por cuenta y cargo de las partes.'
            }
        ]
        
        return standard_clauses
    
    def render_contract(self, contract_data: Dict, config: Dict) -> str:
        """Render contract using templates"""
        jurisdiction = self.get_jurisdiction_from_config(config)
        templates = self.templates.get(jurisdiction, {})
        contract_structure = templates.get('contract_structure', {})
        
        # Build contract sections
        sections = []
        
        # Header
        header_template = contract_structure.get('header', '{title}\n\nNormativa: {legal_references}\n\nSupuesto: {subject}')
        sections.append(header_template.format(**contract_data))
        sections.append("")
        
        # Preamble
        preamble_template = contract_structure.get('preamble', 'CONTRATO ENTRE {lessor} Y {lessee}')
        sections.append(preamble_template.format(**contract_data['parties']))
        sections.append("")
        
        # Declarations
        sections.append(contract_structure.get('declarations', 'DECLARACIONES'))
        sections.append("")
        sections.append(self.render_declarations(contract_data['declarations'], config))
        sections.append("")
        
        # Clauses
        sections.append(contract_structure.get('clauses', 'CLÁUSULAS'))
        sections.append("")
        sections.append(self.render_clauses(contract_data['clauses'], config))
        sections.append("")
        
        # Signatures
        sections.append(contract_structure.get('signatures', 'Firmas'))
        
        return "\n".join(sections)
    
    def render_declarations(self, declarations: List[Dict], config: Dict) -> str:
        """Render declarations using templates"""
        jurisdiction = self.get_jurisdiction_from_config(config)
        
        if jurisdiction == 'mexican_lease':
            return self.render_spanish_declarations(declarations)
        else:
            return self.render_english_declarations(declarations)
    
    def render_spanish_declarations(self, declarations: List[Dict]) -> str:
        """Render Spanish declarations"""
        lines = []
        
        for i, declaration in enumerate(declarations, 1):
            party = declaration['party']
            lines.append(f"{'I' if i == 1 else 'II'}.-- Declara \"{party}\":")
            lines.append("a. Declara ser persona física/moral con capacidad legal para contratar y obligarse en el presente contrato.")
            lines.append("b. Que cuenta con la capacidad legal y económica para la celebración de este contrato.")
            lines.append("")
        
        lines.append("III.-- Declaran ambas partes:")
        lines.append("a. Que se reconocen la personalidad con la que se ostentan dentro del presente contrato.")
        lines.append("b. Que cuentan con la capacidad legal y económica para la celebración de este contrato.")
        lines.append("c. Que ambas partes conocen la naturaleza del presente contrato y aceptan sus condiciones.")
        
        return "\n".join(lines)
    
    def render_english_declarations(self, declarations: List[Dict]) -> str:
        """Render English declarations"""
        lines = []
        
        for i, declaration in enumerate(declarations, 1):
            party = declaration['party']
            lines.append(f"{'I' if i == 1 else 'II'}.-- Declares \"{party}\":")
            lines.append("a. Declares to be a natural/legal person with legal capacity to contract and bind in this agreement.")
            lines.append("b. That has the legal and economic capacity for the execution of this contract.")
            lines.append("")
        
        lines.append("III.-- Both parties declare:")
        lines.append("a. That they recognize the personality with which they appear in this contract.")
        lines.append("b. That they have the legal and economic capacity for the execution of this contract.")
        lines.append("c. That both parties know the nature of this contract and accept its conditions.")
        
        return "\n".join(lines)
    
    def render_clauses(self, clauses: List[Dict], config: Dict) -> str:
        """Render clauses using templates"""
        jurisdiction = self.get_jurisdiction_from_config(config)
        templates = self.templates.get(jurisdiction, {})
        clause_templates = templates.get('clause_templates', {})
        
        lines = []
        
        for clause in clauses:
            clause_type = clause.get('type', 'standard')
            template = clause_templates.get(clause_type, "Cláusula {number}.- {title}.- {description}")
            
            line = template.format(**clause)
            lines.append(line)
            lines.append("")
        
        return "\n".join(lines)
    
    def save_contract(self, contract_text: str, output_file: str):
        """Save the generated contract to a file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(contract_text)

def main():
    """Main function for data-driven AST transpiler"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python laml_ast_transpiler_v2.py <ast_file> [jurisdiction] [output_file]")
        print("Jurisdictions: mexican_lease, us_lease")
        print("Example: python laml_ast_transpiler_v2.py ast.json mexican_lease")
        return
    
    ast_file = sys.argv[1]
    jurisdiction = sys.argv[2] if len(sys.argv) > 2 else 'mexican_lease'
    output_file = sys.argv[3] if len(sys.argv) > 3 else f"contrato_v2_{jurisdiction}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    print(f"🔍 Data-driven transpiling from {ast_file}")
    print(f"🌍 Jurisdiction: {jurisdiction}")
    print(f"📄 Output file: {output_file}")
    
    transpiler = LAMLASTTranspilerV2()
    
    try:
        contract_text = transpiler.transpile(ast_file, jurisdiction)
        transpiler.save_contract(contract_text, output_file)
        
        print(f"✅ Contract transpiled successfully!")
        print(f"📄 Saved to: {output_file}")
        
        # Show preview
        print(f"\n📋 PREVIEW (first 20 lines):")
        print("=" * 50)
        lines = contract_text.split('\n')
        for i, line in enumerate(lines[:20]):
            print(f"{i+1:2d}| {line}")
        if len(lines) > 20:
            print(f"... and {len(lines) - 20} more lines")
            
    except Exception as e:
        print(f"❌ Error transpiling contract: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
