# lamlc Flags Understanding

## Command Line Flags

```
./lamlc [-v] [-c] [-o output.json] [-s solver_path] [--ast-json ast.json] <input.laml>
```

### `-v` (Verbose)
- **Purpose**: Enable verbose output
- **Usage**: Shows detailed compilation steps
- **Backend**: Not currently used

### `-c, --cascade`
- **Purpose**: Include results from dependent institutions (via directObject)
- **Usage**: When components are composed, include component results in final output
- **Backend**: ✅ **Used** - Generates `laml_results_combined.json` with execution order metadata

### `-o output.json`
- **Purpose**: "Specify output JSON file (default: witness_export.json)"
- **Reality**: **Does NOT create the specified file**
- **Observation**: The flag is accepted but `witness_export.json` is not generated
- **Actual Behavior**: `laml_results_*.json` files are generated automatically regardless of `-o`
- **Conclusion**: This flag appears to be legacy or for a different mode
- **Backend**: **Should NOT use this flag** - it doesn't work as documented

### `-s solver_path`
- **Purpose**: Specify solver executable (default: ./tree_fold_cpp)
- **Usage**: Custom solver path
- **Backend**: Not currently used (uses default)

### `--ast-json ast.json`
- **Purpose**: Export hierarchical AST to JSON file
- **Usage**: Creates AST file at specified path
- **Backend**: ✅ **Uses this flag** to generate AST for contract parser

## Actual File Generation

### Files Created by lamlc

1. **AST File** (via `--ast-json`):
   - ✅ **Created**: At specified path
   - **Format**: Hierarchical structure (`type: "LAML_AST"`)
   - **Contains**: `institutions`, `statements`, `rules`, `bindings`
   - **Used by**: `ast_contract_parser.py`

2. **Results Files** (automatic):
   - ✅ **Created**: `laml_results_{instance_name}.json` in project root
   - **Format**: Solver output with solutions
   - **Contains**: `mappings`, `solutions`, `num_solutions`, `satisfiable`
   - **Used by**: `violation_analysis.py`
   - **Note**: Generated for **each** `.valid()` call

3. **Temporary Files** (deleted after compilation):
   - `witness_{instance_name}.json` - Temporary witness files
   - `solver_{instance_name}_{timestamp}.bin` - Solver binary files
   - `witness_export.json` - **NOT created** despite `-o` flag

## Backend Implementation

### Current Behavior (Correct)

```python
result = subprocess.run([
    str(LAMLC_BINARY),
    rel_laml_path,
    "--ast-json", rel_ast_path,  # ✅ Generates AST
    # "-o", rel_output_path,      # ❌ NOT USED - doesn't work
], cwd=str(PROJECT_ROOT), ...)
```

### Why `-o` is Not Used

1. **Doesn't create file**: The flag is ignored or doesn't work as documented
2. **Not needed**: `laml_results_*.json` files are automatically generated
3. **Multiple files**: `-o` suggests single output, but we have multiple results files
4. **Correct approach**: Find all `laml_results_*.json` files in project root

## File Discovery

### How Backend Finds Results

```python
# Find ALL generated result files (components + final contract)
result_files = list(PROJECT_ROOT.glob("laml_results_*.json"))

# Sort by modification time (execution order)
result_files.sort(key=lambda x: x.stat().st_mtime)

# Final contract = last file (authoritative)
final_contract_file = result_files[-1]
```

### Why This Works

- `lamlc` always writes `laml_results_*.json` to the **current working directory**
- Files are sorted by modification time = execution order
- Last file = final `.valid()` call = authoritative solution space

## Recommendations

1. ✅ **Keep using `--ast-json`** - Works correctly
2. ❌ **Don't use `-o` flag** - Doesn't work as documented
3. ✅ **Glob for `laml_results_*.json`** - Correct approach
4. ✅ **Sort by mtime** - Determines execution order
5. ✅ **Store AST separately** - Different format/purpose than results

## Summary

| Flag | Purpose | Works? | Backend Usage |
|------|---------|--------|---------------|
| `--ast-json` | Generate AST | ✅ Yes | ✅ Used |
| `-o` | Output file | ❌ No | ❌ Not used |
| `-v` | Verbose | ✅ Yes | ⚠️ Optional |
| `-c` | Cascade | ✅ Yes | ✅ Used |
| `-s` | Solver path | ✅ Yes | ⚠️ Default OK |

**Key Insight**: `laml_results_*.json` files are **always** generated automatically in the project root, regardless of any flags. The `-o` flag appears to be legacy or non-functional.

