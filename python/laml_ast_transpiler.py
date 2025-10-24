#!/usr/bin/env python3

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class LAMLASTTranspiler:
    """
    AST-based transpiler that converts LAML AST to natural language contracts.
    
    This approach is superior because:
    1. Uses structured AST data instead of parsing JSON output
    2. Preserves semantic relationships and dependencies
    3. Enables precise mapping from LAML constructs to natural language
    4. Supports multiple jurisdictions through templates
    """
    
    def __init__(self):
        self.jurisdiction_templates = {
            'mexican_lease': {
                'title': 'CONTRATO DE ARRENDAMIENTO DE SISTEMA DE ENERGÍA SOLAR',
                'legal_references': [
                    'Artículo 1336, 1337, 1340, 1342 del Código Civil para el Estado Libre y Soberano de Puebla',
                    'Artículo 130 de la Ley del Impuesto sobre la Renta',
                    'Ley de Transición Energética'
                ],
                'subject': 'Contrato de arrendamiento de sistema de energía solar entre persona física y persona moral, incluyendo generación, interconexión y venta de excedentes',
                'party_identification': {
                    'lessor_patterns': ['Corp', 'Company', 'S.A.', 'S.A. de C.V.'],
                    'lessee_patterns': ['Owner', 'Person', 'Individual']
                },
                'language': 'spanish'
            },
            'us_lease': {
                'title': 'SOLAR ENERGY SYSTEM LEASE AGREEMENT',
                'legal_references': [
                    'Uniform Commercial Code Article 2A',
                    'Internal Revenue Code Section 48',
                    'Public Utility Regulatory Policies Act'
                ],
                'subject': 'Lease agreement for solar energy system between individual and corporate entity, including generation, interconnection, and surplus sales',
                'party_identification': {
                    'lessor_patterns': ['Corp', 'Company', 'LLC', 'Inc.'],
                    'lessee_patterns': ['Owner', 'Person', 'Individual']
                },
                'language': 'english'
            }
        }
        
        self.predicate_translations = {
            'mexican_lease': {
                'pay_rent': 'pagar la renta',
                'grant_use': 'otorgar el uso',
                'maintain_system': 'mantener el sistema',
                'return_system': 'devolver el sistema',
                'guarantee_peaceful_use': 'garantizar el uso pacífico',
                'deliver_system': 'entregar el sistema',
                'get_representation_permit': 'obtener el permiso de representación',
                'interconnect': 'interconectar',
                'sell_surplus': 'vender excedentes'
            },
            'us_lease': {
                'pay_rent': 'pay rent',
                'grant_use': 'grant use',
                'maintain_system': 'maintain system',
                'return_system': 'return system',
                'guarantee_peaceful_use': 'guarantee peaceful use',
                'deliver_system': 'deliver system',
                'get_representation_permit': 'obtain representation permit',
                'interconnect': 'interconnect',
                'sell_surplus': 'sell surplus'
            }
        }
        
        self.modal_translations = {
            'mexican_lease': {
                'oblig': 'se obliga a',
                'claim': 'tiene derecho a',
                'forbid': 'queda prohibido'
            },
            'us_lease': {
                'oblig': 'is obligated to',
                'claim': 'has the right to',
                'forbid': 'is prohibited from'
            }
        }
        
        self.logical_operators = {
            'mexican_lease': {
                'implies': 'implica que',
                'and': 'y',
                'or': 'o',
                'not': 'no'
            },
            'us_lease': {
                'implies': 'implies that',
                'and': 'and',
                'or': 'or',
                'not': 'not'
            }
        }
    
    def load_ast(self, ast_file: str) -> Dict:
        """Load LAML AST from JSON file"""
        with open(ast_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def transpile(self, ast_file: str, jurisdiction: str = 'mexican_lease') -> str:
        """Main transpilation method"""
        ast = self.load_ast(ast_file)
        template = self.jurisdiction_templates[jurisdiction]
        
        # Extract main contract institution
        institution = ast['institutions'][0] if ast['institutions'] else None
        instantiation = ast['instantiations'][0] if ast['instantiations'] else None
        
        if not institution:
            raise ValueError("No institution found in AST")
        
        # Generate contract sections
        contract_parts = []
        
        # Header
        contract_parts.append(template['title'])
        contract_parts.append("")
        contract_parts.append(f"Normativa: {', '.join(template['legal_references'])}")
        contract_parts.append("")
        contract_parts.append(f"Supuesto: {template['subject']}")
        contract_parts.append("")
        
        # Parties section
        if instantiation:
            parties = self.identify_parties(instantiation['arguments'], template)
            contract_parts.append(self.generate_preamble(parties, template))
            contract_parts.append("")
        
        # Declarations
        contract_parts.append(self.transpile_declarations(institution['bindings'], template))
        contract_parts.append("")
        
        # Clauses
        contract_parts.append(self.transpile_clauses(institution['rules'], template))
        contract_parts.append("")
        
        # Signatures
        contract_parts.append(self.generate_signatures(template))
        
        return "\n".join(contract_parts)
    
    def identify_parties(self, arguments: List[str], template: Dict) -> tuple:
        """Identify lessor and lessee from instantiation arguments"""
        lessor_patterns = template['party_identification']['lessor_patterns']
        lessee_patterns = template['party_identification']['lessee_patterns']
        
        lessor = next((arg for arg in arguments if any(pattern in arg for pattern in lessor_patterns)), arguments[0])
        lessee = next((arg for arg in arguments if any(pattern in arg for pattern in lessee_patterns)), arguments[1])
        
        return lessor, lessee
    
    def generate_preamble(self, parties: tuple, template: Dict) -> str:
        """Generate contract preamble with party identification"""
        lessor, lessee = parties
        
        if template['language'] == 'spanish':
            return f"CONTRATO DE ARRENDAMIENTO QUE CONSTITUYEN {lessor}, A QUIEN EN LO SUCESIVO SE LE DENOMINARÁ \"EL ARRENDADOR\" A FAVOR DE {lessee}, A QUIEN EN LO SUCESIVO SE LE DENOMINARÁ \"EL ARRENDATARIO\" SUJETÁNDOSE PARA ELLO LA TENOR DE LAS SIGUIENTES DECLARACIONES Y CLÁUSULAS:"
        else:
            return f"LEASE AGREEMENT BETWEEN {lessor}, HEREINAFTER REFERRED TO AS \"THE LESSOR\" AND {lessee}, HEREINAFTER REFERRED TO AS \"THE LESSEE\" SUBJECT TO THE FOLLOWING DECLARATIONS AND CLAUSES:"
    
    def transpile_declarations(self, bindings: List[Dict], template: Dict) -> str:
        """Transpile type bindings to declarations"""
        declarations = []
        
        if template['language'] == 'spanish':
            declarations.append("DECLARACIONES")
            declarations.append("")
            
            # Group bindings by party
            parties = {}
            for binding in bindings:
                if binding['base_type'] == 'Person':
                    party = binding['variable']
                    if party not in parties:
                        parties[party] = []
                    parties[party].append(binding)
            
            # Generate declarations for each party
            for i, (party, party_bindings) in enumerate(parties.items(), 1):
                declarations.append(f"{'I' if i == 1 else 'II'}.-- Declara \"{party}\":")
                declarations.append("a. Declara ser persona física/moral con capacidad legal para contratar y obligarse en el presente contrato.")
                declarations.append("b. Que cuenta con la capacidad legal y económica para la celebración de este contrato.")
                declarations.append("")
            
            declarations.append("III.-- Declaran ambas partes:")
            declarations.append("a. Que se reconocen la personalidad con la que se ostentan dentro del presente contrato.")
            declarations.append("b. Que cuentan con la capacidad legal y económica para la celebración de este contrato.")
            declarations.append("c. Que ambas partes conocen la naturaleza del presente contrato y aceptan sus condiciones.")
        
        else:  # English
            declarations.append("DECLARATIONS")
            declarations.append("")
            
            # Group bindings by party
            parties = {}
            for binding in bindings:
                if binding['base_type'] == 'Person':
                    party = binding['variable']
                    if party not in parties:
                        parties[party] = []
                    parties[party].append(binding)
            
            # Generate declarations for each party
            for i, (party, party_bindings) in enumerate(parties.items(), 1):
                declarations.append(f"{'I' if i == 1 else 'II'}.-- Declares \"{party}\":")
                declarations.append("a. Declares to be a natural/legal person with legal capacity to contract and bind in this agreement.")
                declarations.append("b. That has the legal and economic capacity for the execution of this contract.")
                declarations.append("")
            
            declarations.append("III.-- Both parties declare:")
            declarations.append("a. That they recognize the personality with which they appear in this contract.")
            declarations.append("b. That they have the legal and economic capacity for the execution of this contract.")
            declarations.append("c. That both parties know the nature of this contract and accept its conditions.")
        
        return "\n".join(declarations)
    
    def transpile_clauses(self, rules: List[Dict], template: Dict) -> str:
        """Transpile rules to clauses with proper dependencies"""
        clauses = []
        
        if template['language'] == 'spanish':
            clauses.append("CLÁUSULAS")
        else:
            clauses.append("CLAUSES")
        clauses.append("")
        
        clause_number = 1
        
        # Group rules by dependency type
        rule_groups = self.group_rules_by_dependency(rules, template)
        
        # Core obligations first
        for rule in rule_groups.get('core_obligation', []):
            clause = self.transpile_rule_to_clause(rule, clause_number, template)
            clauses.append(clause)
            clauses.append("")
            clause_number += 1
        
        # Maintenance and return obligations
        for rule in rule_groups.get('maintenance_obligation', []) + rule_groups.get('return_obligation', []):
            clause = self.transpile_rule_to_clause(rule, clause_number, template)
            clauses.append(clause)
            clauses.append("")
            clause_number += 1
        
        # Generation obligations (with dependency explanation)
        generation_rules = (rule_groups.get('generation_obligation', []) + 
                           rule_groups.get('interconnection_obligation', []) + 
                           rule_groups.get('sales_obligation', []))
        
        if generation_rules:
            if template['language'] == 'spanish':
                clauses.append(f"Cláusula {clause_number}.- ACTIVIDADES DE GENERACIÓN.- Las siguientes obligaciones están condicionadas al cumplimiento del pago de renta:")
            else:
                clauses.append(f"Clause {clause_number}.- GENERATION ACTIVITIES.- The following obligations are conditional upon payment of rent:")
            clauses.append("")
            clause_number += 1
            
            for rule in generation_rules:
                clause = self.transpile_rule_to_clause(rule, clause_number, template)
                clauses.append(clause)
                clauses.append("")
                clause_number += 1
        
        # Rights and delivery obligations
        for rule in rule_groups.get('rights_obligation', []) + rule_groups.get('delivery_obligation', []):
            clause = self.transpile_rule_to_clause(rule, clause_number, template)
            clauses.append(clause)
            clauses.append("")
            clause_number += 1
        
        # Add dependency clause
        if template['language'] == 'spanish':
            clauses.append(f"Cláusula {clause_number}.- DEPENDENCIAS.- Todas las obligaciones de generación, interconexión y venta de excedentes están condicionadas al cumplimiento puntual del pago de renta. En caso de incumplimiento, se suspenderán automáticamente todos los derechos de generación.")
        else:
            clauses.append(f"Clause {clause_number}.- DEPENDENCIES.- All generation, interconnection, and surplus sales obligations are conditional upon timely payment of rent. In case of default, all generation rights will be automatically suspended.")
        clauses.append("")
        clause_number += 1
        
        # Standard clauses
        if template['language'] == 'spanish':
            clauses.append(f"Cláusula {clause_number}.- TERMINACIÓN.- Las partes podrán dar por terminado el presente contrato por mutuo acuerdo, el cual deberá constar por escrito.")
            clauses.append("")
            clause_number += 1
            
            clauses.append(f"Cláusula {clause_number}.- JURISDICCIÓN.- Las partes se someten a la jurisdicción de los Tribunales competentes para la interpretación y ejecución de los pactos que anteceden.")
            clauses.append("")
            clause_number += 1
            
            clauses.append(f"Cláusula {clause_number}.- GASTOS.- Las partes convienen en que los gastos, derechos y honorarios que devengue el otorgamiento respectivo, serán por cuenta y cargo de las partes.")
        else:
            clauses.append(f"Clause {clause_number}.- TERMINATION.- The parties may terminate this contract by mutual agreement, which must be in writing.")
            clauses.append("")
            clause_number += 1
            
            clauses.append(f"Clause {clause_number}.- JURISDICTION.- The parties submit to the jurisdiction of competent courts for the interpretation and execution of the foregoing agreements.")
            clauses.append("")
            clause_number += 1
            
            clauses.append(f"Clause {clause_number}.- EXPENSES.- The parties agree that the expenses, fees and honoraria arising from the respective granting will be borne by the parties.")
        
        return "\n".join(clauses)
    
    def group_rules_by_dependency(self, rules: List[Dict], template: Dict) -> Dict:
        """Group rules by their dependency type based on predicate analysis"""
        groups = {
            'core_obligation': [],
            'maintenance_obligation': [],
            'return_obligation': [],
            'generation_obligation': [],
            'interconnection_obligation': [],
            'sales_obligation': [],
            'rights_obligation': [],
            'delivery_obligation': []
        }
        
        for rule in rules:
            # Analyze the rule to determine its type
            rule_type = self.analyze_rule_type(rule)
            if rule_type in groups:
                groups[rule_type].append(rule)
        
        return groups
    
    def analyze_rule_type(self, rule: Dict) -> str:
        """Analyze rule to determine its dependency type"""
        # Extract predicate names from rule
        left_predicate = self.extract_predicate_name(rule['expression']['left'])
        right_predicate = self.extract_predicate_name(rule['expression']['right'])
        
        # Determine rule type based on predicates
        if 'pay_rent' in left_predicate and 'grant_use' in right_predicate:
            return 'core_obligation'
        elif 'maintain' in right_predicate:
            return 'maintenance_obligation'
        elif 'return' in right_predicate:
            return 'return_obligation'
        elif 'permit' in right_predicate:
            return 'generation_obligation'
        elif 'interconnect' in right_predicate:
            return 'interconnection_obligation'
        elif 'sell' in right_predicate:
            return 'sales_obligation'
        elif 'guarantee' in right_predicate:
            return 'rights_obligation'
        elif 'deliver' in right_predicate:
            return 'delivery_obligation'
        else:
            return 'core_obligation'
    
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
    
    def transpile_rule_to_clause(self, rule: Dict, clause_number: int, template: Dict) -> str:
        """Transpile a single rule to a clause"""
        rule_name = rule['name'].replace('_', ' ').upper()
        expression = rule['expression']
        
        # Transpile the rule expression
        clause_text = self.transpile_expression(expression, template)
        
        if template['language'] == 'spanish':
            return f"Cláusula {clause_number}.- {rule_name}.- {clause_text}"
        else:
            return f"Clause {clause_number}.- {rule_name}.- {clause_text}"
    
    def transpile_expression(self, expression: Dict, template: Dict) -> str:
        """Transpile rule expression to natural language"""
        if expression['expression_type'] == 'predicate':
            return self.transpile_predicate(expression['predicate'], template)
        elif expression['expression_type'] == 'binary_operation':
            return self.transpile_binary_operation(expression, template)
        else:
            return "Unknown expression type"
    
    def transpile_predicate(self, predicate: Dict, template: Dict) -> str:
        """Transpile predicate to natural language"""
        name = predicate['name']
        modal = predicate.get('modal', '')
        
        # Translate predicate name
        jurisdiction = 'mexican_lease' if template['language'] == 'spanish' else 'us_lease'
        translated_name = self.predicate_translations[jurisdiction].get(name, name)
        
        # Add modal operator
        if modal:
            modal_text = self.modal_translations[jurisdiction].get(modal, modal)
            return f"{modal_text} {translated_name}"
        else:
            return translated_name
    
    def transpile_binary_operation(self, expression: Dict, template: Dict) -> str:
        """Transpile binary operation to natural language"""
        operator = expression['operator']
        left = expression['left']
        right = expression['right']
        
        if operator == 'implies':
            left_text = self.transpile_expression(left, template)
            right_text = self.transpile_expression(right, template)
            
            if template['language'] == 'spanish':
                return f"Para {left_text}, {right_text}"
            else:
                return f"For {left_text}, {right_text}"
        
        elif operator == 'not':
            right_text = self.transpile_expression(right, template)
            jurisdiction = 'mexican_lease' if template['language'] == 'spanish' else 'us_lease'
            not_text = self.logical_operators[jurisdiction]['not']
            
            if template['language'] == 'spanish':
                return f"En caso de {not_text} {right_text}"
            else:
                return f"In case of {not_text} {right_text}"
        
        else:
            left_text = self.transpile_expression(left, template)
            right_text = self.transpile_expression(right, template)
            jurisdiction = 'mexican_lease' if template['language'] == 'spanish' else 'us_lease'
            op_text = self.logical_operators[jurisdiction].get(operator, operator)
            return f"{left_text} {op_text} {right_text}"
    
    def generate_signatures(self, template: Dict) -> str:
        """Generate contract signatures"""
        if template['language'] == 'spanish':
            return """Así convenido y sabedores del valor, fuerza y alcance legales del contenido de este contrato, las partes lo firman por duplicado a los _____ días del mes de _____.

EL ARRENDADOR

EL ARRENDATARIO"""
        else:
            return """So agreed and knowing the value, force and legal scope of the content of this contract, the parties sign it in duplicate on the _____ day of the month of _____.

THE LESSOR

THE LESSEE"""
    
    def save_contract(self, contract_text: str, output_file: str):
        """Save the generated contract to a file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(contract_text)

def main():
    """Main function for AST transpiler"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python laml_ast_transpiler.py <ast_file> [jurisdiction] [output_file]")
        print("Jurisdictions: mexican_lease, us_lease")
        print("Example: python laml_ast_transpiler.py ast.json mexican_lease")
        return
    
    ast_file = sys.argv[1]
    jurisdiction = sys.argv[2] if len(sys.argv) > 2 else 'mexican_lease'
    output_file = sys.argv[3] if len(sys.argv) > 3 else f"contrato_ast_{jurisdiction}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    print(f"🔍 Transpiling LAML AST from {ast_file}")
    print(f"🌍 Jurisdiction: {jurisdiction}")
    print(f"📄 Output file: {output_file}")
    
    transpiler = LAMLASTTranspiler()
    
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
