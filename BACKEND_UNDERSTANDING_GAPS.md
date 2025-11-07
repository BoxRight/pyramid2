# Critical Understanding Gaps in Backend Implementation

## Issues I've Identified

### 1. **Multiple `.valid()` Calls - lamlc Generates Multiple JSON Files**

**Problem**: A single LAML contract file can have multiple `.valid()` calls:
- `core_lease_component.valid()` → `laml_results_core_lease_component.json`
- `simple_solar_contract.valid()` → `laml_results_simple_solar_contract.json`

**Current Implementation**: My backend just grabs the "most recent" file, losing other results.

**Questions**:
- Which `.valid()` result is the "main" contract? (Likely the last one)
- Should I store ALL component results or just the final contract?
- How do component results relate to the final contract analysis?
- Does `directObject()` extraction affect which results matter?

### 2. **LAML Composition Pattern - `directObject()`**

**Pattern I see**:
```laml
# Create component and extract claims
core_lease_component :- core_lease_law(...)
core_lease_claims = core_lease_component.directObject()
core_lease_component.valid()  # Validate component

# Use claims in main contract
simple_solar_lease(..., core_claims) = institution(...) {
    # Uses core_lease_claims
}
simple_solar_contract.valid()  # Validate final contract
```

**Questions**:
- What does `directObject()` actually extract? (Claims, obligations, predicates?)
- How does this affect the solution space?
- Should component validation happen before or after main contract?
- Are component results needed for analysis, or just the final contract?

### 3. **lamlc Output File Naming**

**Current Behavior**: 
- lamlc generates `laml_results_{institution_name}.json` for each `.valid()` call
- Files are written to project root, not specified output location
- `-o` flag might not work as expected

**Questions**:
- How do I reliably identify which JSON file corresponds to the final contract?
- Should I parse the LAML file to find the last `.valid()` call?
- Or should I look for the largest/most complex solution set?
- How do I handle contracts with custom names?

### 4. **Python Script Integration**

**Current Understanding**:
- `violation_analysis.py` reads ONE JSON file and analyzes solutions
- `ast_contract_parser.py` reads ONE JSON file to generate HTML

**Questions**:
- Can these scripts handle multiple JSON files?
- Do they need to merge component + final contract data?
- Should analysis be done on components, final contract, or both?
- How does `directObject()` composition affect the solution vectors?

### 5. **User Workflow Integration**

**Current Flow**:
1. User generates/loads LAML
2. Compile → Get ONE JSON file
3. Analyze → Analyze that ONE file
4. Query → Query that ONE file

**Questions**:
- Should users see component analysis separately?
- Or only the final composed contract?
- How does the UI show multi-component contracts?
- Should compilation show progress for each component?

## What I Need to Understand

### A. lamlc Compilation Behavior
1. **File Generation**: Does lamlc ALWAYS generate separate files for each `.valid()`?
2. **Output Control**: Can I control where/which files are generated?
3. **File Naming**: How to identify the "main" contract file?
4. **Dependencies**: Are component files needed for final contract analysis?

### B. LAML Composition Semantics
1. **directObject()**: What exactly does this extract and how?
2. **Component vs Final**: What's the relationship between component and final solutions?
3. **Claim Passing**: How do extracted claims affect the final contract's solution space?
4. **Analysis Scope**: Should I analyze components separately or only the final contract?

### C. Python Script Behavior
1. **Multi-file Support**: Can `violation_analysis.py` handle multiple JSON files?
2. **Data Merging**: Should I merge component + final contract data?
3. **Solution Space**: Are component solutions subsets of final solutions?
4. **AST Parsing**: Does `ast_contract_parser.py` need component data too?

### D. Backend Architecture
1. **Storage**: Should I store all component results or just final?
2. **API Design**: Do endpoints need to handle component queries?
3. **Workflow**: Should compilation be multi-step (components → final)?
4. **Analysis**: Should analysis include component breakdown?

## Proposed Solution (Need Your Input)

### Option 1: Store Only Final Contract
- Find the last `.valid()` call in LAML
- Only store/analyze that result
- Ignore component results

### Option 2: Store All Results, Analyze Final
- Store all component JSON files
- Analyze only the final contract
- Keep component results for reference

### Option 3: Full Multi-Component Support
- Store all component results
- Analyze each component separately
- Also analyze final composed contract
- Provide API endpoints for component queries

**Which approach matches your intended workflow?**

## Questions for You

1. **What is the intended user workflow?**
   - Do users care about component analysis?
   - Or only the final composed contract?

2. **How should `directObject()` work?**
   - What does it extract?
   - How does it affect solutions?

3. **What should the backend store?**
   - All component results?
   - Just the final contract?
   - Both with relationships?

4. **How should analysis work?**
   - Component-by-component?
   - Final contract only?
   - Both with comparison?

5. **How should the UI present this?**
   - Show component breakdown?
   - Show only final contract?
   - Allow drilling into components?

Please help me understand these aspects so I can fix the backend implementation correctly!

