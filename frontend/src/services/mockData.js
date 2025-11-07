// Mock data for simulating the full contract flow without backend

export const MOCK_LAML_CONTRACT = `# Simple Solar Lease Contract
# Basic solar lease with one law import and directObject composition

import "../laws/ccf_core_lease.laml"

# Create law component and extract claims
core_lease_component :- core_lease_law(SolarCorp, HomeOwner, SolarPanelSystem, USD_200_monthly)
core_lease_claims = core_lease_component.directObject()
core_lease_component.valid()

# Simple solar lease institution with directObject claims
simple_solar_lease(lessor, lessee, system, rent, core_claims) = 
institution(lessor, lessee, system, rent, core_claims) {
    
    # Type bindings
    Lessor(lessor) = Person(lessor, _)
    Lessee(lessee) = Person(lessee, _)
    System(system) = Thing(system, _)
    Rent(rent) = Thing(rent, movable)
    CoreClaims(core_claims) = Thing(core_claims, movable)
    
    # Basic lease acts using the passed claims
    grant_use(lessor, system, lessee) = Lessor(lessor), System(system), Lessee(lessee)
    pay_rent(lessee, rent, lessor) = Lessee(lessee), Rent(rent), Lessor(lessor)
    maintain_system(lessor, core_claims, lessee) = Lessor(lessor), CoreClaims(core_claims), Lessee(lessee)
    return_system(lessee, system, lessor) = Lessee(lessee), System(system), Lessor(lessor)
    
    # Basic lease rules
    rule_rent_obligation = grant_use(lessor, system, lessee) 
                          implies oblig(pay_rent(lessee, rent, lessor))
    
    rule_continued_possession = pay_rent(lessee, rent, lessor) 
                               implies claim(grant_use(lessor, system, lessee))
    
    rule_maintenance_obligation = pay_rent(lessee, rent, lessor) 
                                 implies oblig(maintain_system(lessor, core_claims, lessee))
    
    rule_return_obligation = not(pay_rent(lessee, rent, lessor)) 
                            implies oblig(return_system(lessee, system, lessor))
}

# Create the simple solar lease contract instance
simple_solar_contract :- simple_solar_lease(
    SolarCorp,          # lessor
    HomeOwner,         # lessee
    SolarPanelSystem,  # system
    USD_200_monthly,   # rent
    core_lease_claims  # core_claims
)

simple_solar_contract.valid()`

// Mock parsed contract document (from ast_contract_parser)
export const MOCK_PARSED_CONTRACT = {
  metadata: {
    title: 'CONTRATO DE SIMPLE_SOLAR_LEASE',
    normativa: ['../laws/ccf_core_lease.laml'],
    supuesto: 'Contrato de simple_solar_lease entre SolarCorp, HomeOwner.'
  },
  parties_block: {
    parties: [
      {
        name: 'SolarCorp',
        predicate: 'Lessor',
        role: 'lessor'
      },
      {
        name: 'HomeOwner',
        predicate: 'Lessee',
        role: 'lessee'
      }
    ]
  },
  objects_section: {
    objects: [
      {
        name: 'SYSTEM',
        description: 'objeto denominado system',
        base_type: 'Thing'
      },
      {
        name: 'RENT',
        description: 'bien mueble denominado rent',
        base_type: 'Thing',
        subtype: 'movable'
      },
      {
        name: 'CORE_CLAIMS',
        description: 'bien mueble denominado core_claims',
        base_type: 'Thing',
        subtype: 'movable'
      }
    ]
  },
  declarations_section: {
    declarations: [
      {
        party: 'lessor',
        items: [
          "Declara 'LESSOR', ser persona física con capacidad legal para contratar y obligarse en el presente contrato.",
          "Que cuenta con la capacidad legal y económica para la celebración de este contrato.",
          "Que desea adquirir los derechos de lessor en el presente contrato."
        ]
      },
      {
        party: 'lessee',
        items: [
          "Declara 'LESSEE', ser persona física con capacidad legal para contratar y obligarse en el presente contrato.",
          "Que cuenta con la capacidad legal y económica para la celebración de este contrato.",
          "Que desea adquirir los derechos de lessee en el presente contrato."
        ]
      },
      {
        party: 'ambas partes',
        items: [
          "Que se reconocen la personalidad con la que se ostentan dentro del presente contrato por lo que el mismo carece de vicios, dolo o mala fe.",
          "Que cuentan con la capacidad legal y económica para la celebración de este contrato.",
          "Que ambas partes conocen la naturaleza del presente contrato, saben y aceptan sus condiciones, así como el alcance de sus efectos respecto del cumplimiento o incumplimiento del mismo."
        ]
      }
    ]
  },
  clauses_section: [
    {
      title: 'ACTO DE GRANT USE',
      type: 'act',
      content: 'Las partes reconocen el acto jurídico que realiza lessor frente a lessee con objeto de system.'
    },
    {
      title: 'ACTO DE PAY RENT',
      type: 'act',
      content: 'Las partes reconocen el acto jurídico que realiza lessee frente a lessor con objeto de rent.'
    },
    {
      title: 'ACTO DE MAINTAIN SYSTEM',
      type: 'act',
      content: 'Las partes reconocen el acto jurídico que realiza lessor frente a lessee con objeto de core_claims.'
    },
    {
      title: 'ACTO DE RETURN SYSTEM',
      type: 'act',
      content: 'Las partes reconocen el acto jurídico que realiza lessee frente a lessor con objeto de system.'
    },
    {
      title: 'OBLIGACIÓN DE RENT_OBLIGATION',
      type: 'obligation',
      content: "En el supuesto de que se realiza el acto donde 'lessor' transfiere Grant use de 'system' a 'lessee', entonces 'lessee' queda obligado a transfiere Pay rent de 'rent' a 'lessor'"
    },
    {
      title: 'OBLIGACIÓN DE CONTINUED_POSSESSION',
      type: 'obligation',
      content: "En el supuesto de que se realiza el acto donde 'lessee' transfiere Pay rent de 'rent' a 'lessor', entonces 'lessee' tiene el derecho de exigir que 'lessor' transfiere Grant use de 'system' a 'lessee'"
    },
    {
      title: 'OBLIGACIÓN DE MAINTENANCE_OBLIGATION',
      type: 'obligation',
      content: "En el supuesto de que se realiza el acto donde 'lessee' transfiere Pay rent de 'rent' a 'lessor', entonces 'lessor' queda obligado a transfiere Maintain system de 'core_claims' a 'lessee'"
    },
    {
      title: 'OBLIGACIÓN DE RETURN_OBLIGATION',
      type: 'obligation',
      content: "En el supuesto de que no se cumpla con que se realiza el acto donde 'lessee' transfiere Pay rent de 'rent' a 'lessor', entonces 'lessee' queda obligado a transfiere Return system de 'system' a 'lessor'"
    }
  ],
  final_section: {
    clauses: [
      {
        title: 'TERMINACIÓN',
        content: 'Las partes podrán dar por terminado el presente contrato por mutuo acuerdo, el cual deberá constar por escrito.'
      },
      {
        title: 'JURISDICCIÓN',
        content: 'Las partes se someten a la jurisdicción de los Tribunales competentes para la interpretación y ejecución de los pactos que anteceden.'
      },
      {
        title: 'GASTOS',
        content: 'Las partes convienen en que los gastos, derechos y honorarios que devengue el otorgamiento respectivo, serán por cuenta y cargo de las partes.'
      }
    ],
    signatures: {
      text: 'Así convenido y sabedores del valor, fuerza y alcance legales del contenido de este contrato, las partes lo firman por duplicado a los _____ días del mes de _____.',
      parties: ['LESSOR', 'LESSEE']
    }
  }
}

export const MOCK_GENERATED_CONTRACT = {
  contract_id: 'contract-solar-lease-001',
  laml_content: MOCK_LAML_CONTRACT,
  parsed_contract: MOCK_PARSED_CONTRACT, // Add parsed contract document
  status: 'generated',
  contract_type: 'solar_lease',
  jurisdiction: 'Mexico',
  created_at: new Date().toISOString(),
  validation_errors: [],
  compilation_triggered: false
}

export const MOCK_ANALYSIS_RESULTS = {
  contract_id: 'contract-solar-lease-001',
  total_solutions: 4,
  num_predicates: 4,
  status: 'ready',
  satisfiable: true,
  predicates: [
    'grant_use',
    'pay_rent',
    'maintain_system',
    'return_system'
  ],
  violation_results: [
    {
      predicate: 'pay_rent',
      total_violation_scenarios: 2,
      total_fulfillment_scenarios: 2,
      consequences: [
        {
          predicate_name: 'return_system',
          predicate_type: 'act',
          full_expression: 'return_system(HomeOwner, SolarPanelSystem, SolarCorp)',
          consequence_type: 'always_present',
          count: 2,
          total: 2
        },
        {
          predicate_name: 'grant_use',
          predicate_type: 'act',
          full_expression: 'grant_use(SolarCorp, SolarPanelSystem, HomeOwner)',
          consequence_type: 'always_absent',
          count: 0,
          total: 2
        }
      ],
      num_consequences: 2
    },
    {
      predicate: 'grant_use',
      total_violation_scenarios: 0,
      total_fulfillment_scenarios: 2,
      consequences: [],
      num_consequences: 0,
      message: "Predicate 'grant_use' is present in all solutions"
    },
    {
      predicate: 'return_system',
      total_violation_scenarios: 2,
      total_fulfillment_scenarios: 2,
      consequences: [
        {
          predicate_name: 'pay_rent',
          predicate_type: 'act',
          full_expression: 'pay_rent(HomeOwner, USD_200_monthly, SolarCorp)',
          consequence_type: 'always_absent',
          count: 0,
          total: 2
        }
      ],
      num_consequences: 1
    },
    {
      predicate: 'maintain_system',
      total_violation_scenarios: 2,
      total_fulfillment_scenarios: 2,
      consequences: [
        {
          predicate_name: 'pay_rent',
          predicate_type: 'act',
          full_expression: 'pay_rent(HomeOwner, USD_200_monthly, SolarCorp)',
          consequence_type: 'always_present',
          count: 2,
          total: 2
        }
      ],
      num_consequences: 1
    }
  ],
  fulfillment_results: [
    {
      predicate: 'pay_rent',
      total_fulfillment_scenarios: 2,
      consequences: [
        {
          predicate_name: 'grant_use',
          predicate_type: 'act',
          full_expression: 'grant_use(SolarCorp, SolarPanelSystem, HomeOwner)',
          consequence_type: 'always_present',
          count: 2,
          total: 2
        },
        {
          predicate_name: 'maintain_system',
          predicate_type: 'act',
          full_expression: 'maintain_system(SolarCorp, core_lease_claims, HomeOwner)',
          consequence_type: 'always_present',
          count: 2,
          total: 2
        }
      ],
      num_consequences: 2
    },
    {
      predicate: 'grant_use',
      total_fulfillment_scenarios: 2,
      consequences: [
        {
          predicate_name: 'pay_rent',
          predicate_type: 'act',
          full_expression: 'pay_rent(HomeOwner, USD_200_monthly, SolarCorp)',
          consequence_type: 'always_present',
          count: 2,
          total: 2
        }
      ],
      num_consequences: 1
    }
  ]
}

export const MOCK_QUERY_RESULTS = {
  pay_rent_violation: {
    predicate: 'pay_rent',
    total_violation_scenarios: 2,
    total_fulfillment_scenarios: 2,
    consequences: [
      {
        predicate_name: 'return_system',
        predicate_type: 'act',
        full_expression: 'return_system(HomeOwner, SolarPanelSystem, SolarCorp)',
        consequence_type: 'always_present',
        count: 2,
        total: 2
      },
      {
        predicate_name: 'grant_use',
        predicate_type: 'act',
        full_expression: 'grant_use(SolarCorp, SolarPanelSystem, HomeOwner)',
        consequence_type: 'always_absent',
        count: 0,
        total: 2
      }
    ],
    num_consequences: 2
  },
  pay_rent_fulfillment: {
    predicate: 'pay_rent',
    total_fulfillment_scenarios: 2,
    consequences: [
      {
        predicate_name: 'grant_use',
        predicate_type: 'act',
        full_expression: 'grant_use(SolarCorp, SolarPanelSystem, HomeOwner)',
        consequence_type: 'always_present',
        count: 2,
        total: 2
      },
      {
        predicate_name: 'maintain_system',
        predicate_type: 'act',
        full_expression: 'maintain_system(SolarCorp, core_lease_claims, HomeOwner)',
        consequence_type: 'always_present',
        count: 2,
        total: 2
      }
    ],
    num_consequences: 2
  },
  return_system_violation: {
    predicate: 'return_system',
    total_violation_scenarios: 2,
    total_fulfillment_scenarios: 2,
    consequences: [
      {
        predicate_name: 'pay_rent',
        predicate_type: 'act',
        full_expression: 'pay_rent(HomeOwner, USD_200_monthly, SolarCorp)',
        consequence_type: 'always_absent',
        count: 0,
        total: 2
      }
    ],
    num_consequences: 1
  },
  grant_use_fulfillment: {
    predicate: 'grant_use',
    total_fulfillment_scenarios: 2,
    consequences: [
      {
        predicate_name: 'pay_rent',
        predicate_type: 'act',
        full_expression: 'pay_rent(HomeOwner, USD_200_monthly, SolarCorp)',
        consequence_type: 'always_present',
        count: 2,
        total: 2
      }
    ],
    num_consequences: 1
  }
}

// Simulate API delay
export const simulateDelay = (ms = 1000) => {
  return new Promise(resolve => setTimeout(resolve, ms))
}

