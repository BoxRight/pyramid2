# Backend Architecture - Corrected Understanding

## LAML Compilation Workflow (Kelsen's Pyramid)

### 1. **lamlc Compilation Process**

```
LAML File → lamlc → Multiple JSON Files
```

**Key Points**:
- Compiler processes ALL `.valid()` calls **sequentially** in file order
- Each `.valid()` call creates a **separate clause model**
- Each generates **unique file**: `laml_results_{instance_name}.json`
- Each calls solver **independently**
- Each produces **separate solution sets**
- Temporary solver files are deleted
- Only final JSON results remain

### 2. **Component vs Final Contract**

**Components** (Prerequisites):
- Validated **in isolation** before final contract
- Claims extracted via `directObject()` → `Thing(movable)` (collection of enforceable claims)
- Results stored as `laml_results_{component_name}.json`
- Can be queried independently

**Final Contract** (Authoritative):
- Last `.valid()` call in file (typically the composite)
- Contains **complete solution space** with all composed rules
- Validates the **composite** with all rules and constraints
- Results stored as `laml_results_{final_instance_name}.json`
- This is the **authoritative solution space**

### 3. **directObject() Semantics**

**What it extracts**:
- All **explicit claims**
- **Correlative claims** from obligations
- **Negation claims** from prohibitions

**Return type**: `Thing(movable)` - a collection of enforceable claims

**Purpose**: Pass extracted claims from components to final contract as parameters

### 4. **Backend Implementation**

#### Compilation Service (`contract_compiler.py`)

**Behavior**:
1. Execute lamlc (generates multiple files)
2. Find ALL `laml_results_*.json` files
3. Sort by modification time (execution order)
4. Load all component + final contract results
5. Identify final contract (last file = authoritative)
6. Store final contract AST (authoritative)
7. Store component results metadata (for querying)

**Returns**:
```python
{
    "contract_id": "...",
    "ast_file": "...",  # Final contract (authoritative)
    "final_instance_name": "simple_solar_contract",
    "num_solutions": 4,  # Final contract solutions
    "satisfiable": true,
    "components": {
        "core_lease_component": {
            "instance_name": "core_lease_component",
            "num_solutions": 810,
            "satisfiable": true
        }
    }
}
```

#### Analysis Service (`contract_analyzer.py`)

**Default Behavior**:
- Analyzes **final contract** (authoritative solution space)
- Uses `backend.lib.violation_analysis` (LAMLViolationAnalyzer) on final contract results JSON

**Component Analysis**:
- Can analyze specific component by passing `instance_name`
- Components analyzed separately (in isolation)
- Useful for understanding component behavior

#### Query Service (`contract_query.py`)

**Default Behavior**:
- Queries **final contract** (authoritative)
- Returns consequences from authoritative solution space

**Component Query**:
- Can query specific component by passing `instance_name`
- Useful for component-level investigation

#### Storage (`local_storage.py`)

**Stores**:
- Final contract AST (authoritative) → `data/compiled/ast/{contract_id}.json`
- Component results metadata → `contracts_metadata.json`
- Component JSON files → Referenced by file path (in project root for now)

**Methods**:
- `save_component_results()` - Store component metadata
- `get_component_result()` - Retrieve specific component data

## API Endpoints

### Compilation
```
POST /contracts/compile
→ Returns: final contract + component metadata
```

### Analysis
```
GET /contracts/{contract_id}/analysis
→ Analyzes final contract (authoritative)

GET /contracts/{contract_id}/analysis?instance_name=core_lease_component
→ Analyzes specific component
```

### Query
```
POST /contracts/query
{
    "contract_id": "...",
    "predicate_name": "pay_rent",
    "query_type": "violation",
    "instance_name": null  // null = final contract, name = component
}
```

## User Workflow

1. **Generate/Load Contract** → LAML with multiple `.valid()` calls
2. **Compile** → All components + final contract compiled
   - Components validated in isolation
   - Claims extracted via `directObject()`
   - Final contract validated with all rules
3. **Analyze** → Final contract analyzed (authoritative)
   - Can also analyze components separately
4. **Query** → Query final contract (authoritative)
   - Can also query components

## Kelsen's Pyramid Analogy

- **Base Layer**: Legal principles (`principles/`)
- **Middle Layer**: Legal frameworks (`laws/`)
- **Component Layer**: Validated components (prerequisites)
- **Top Layer**: Final composite contract (authoritative)
  - Contains all composed rules
  - Authoritative solution space
  - Complete legal framework

## Key Takeaways

1. ✅ **Final contract is authoritative** - Contains complete solution space
2. ✅ **Components are prerequisites** - Validated first, claims extracted
3. ✅ **All results stored** - Components can be queried independently
4. ✅ **directObject() extracts claims** - Passes enforceable claims to final contract
5. ✅ **Sequential execution** - Components before final contract
6. ✅ **Separate analysis** - Components in isolation, final with all rules

