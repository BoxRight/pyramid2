# Cascade Flag Analysis

## What `-c` / `--cascade` Does

### File Generation
When `-c` flag is used, lamlc generates an additional file:
- **`laml_results_combined.json`** - Metadata file tracking execution order

### Combined File Structure
```json
{
  "cascade": true,
  "executions": [
    {
      "instance": "simple_solar_contract",
      "results_file": "laml_results_simple_solar_contract.json"
    },
    {
      "instance": "core_lease_component",
      "results_file": "laml_results_core_lease_component.json"
    }
  ]
}
```

**Key Points**:
- ✅ Tracks execution order (important for dependency chain)
- ✅ Maps instance names to result files
- ✅ Confirms cascade mode was used
- ❌ Does NOT contain solution data (still in individual files)
- ❌ Does NOT combine solutions (each file still independent)

## Why Use Cascade Flag?

### Benefits

1. **Execution Order Tracking**
   - Verifies components executed before final contract
   - Documents dependency chain (directObject composition)
   - Helps identify which components were used

2. **Metadata for Analysis**
   - Provides structured relationship between components
   - Useful for UI display of component hierarchy
   - Can validate that component results exist

3. **Debugging**
   - Helps verify compilation order matches expected dependencies
   - Can identify missing component results
   - Useful for troubleshooting composition issues

### Current Backend Behavior

**Without Cascade**:
- ✅ Finds all `laml_results_*.json` files
- ✅ Sorts by modification time (execution order)
- ✅ Identifies final contract (last file)
- ⚠️ No explicit dependency tracking

**With Cascade**:
- ✅ All of the above PLUS
- ✅ Explicit execution order in `combined.json`
- ✅ Component-to-file mapping
- ✅ Dependency verification

## Recommendation: **YES, Use Cascade Flag**

### Reasons

1. **Better Metadata**: Provides structured execution order
2. **Dependency Verification**: Can verify component chain
3. **Future-Proof**: Enables better component analysis
4. **UI Support**: Can show component hierarchy to users
5. **No Downsides**: Doesn't change solution data, just adds metadata

### Implementation

```python
result = subprocess.run([
    str(LAMLC_BINARY),
    rel_laml_path,
    "--ast-json", rel_ast_path,
    "-c"  # ✅ Add cascade flag
], cwd=str(PROJECT_ROOT), ...)

# After compilation, check for combined.json
combined_file = PROJECT_ROOT / "laml_results_combined.json"
if combined_file.exists():
    with open(combined_file, 'r') as f:
        cascade_metadata = json.load(f)
    # Store execution order metadata
```

## Updated Backend Workflow

1. Execute lamlc with `-c` flag
2. Find all `laml_results_*.json` files (including `combined.json`)
3. Load `combined.json` if it exists (get execution order)
4. Sort result files by modification time OR use execution order from combined.json
5. Store cascade metadata in contract metadata
6. Use for component hierarchy display

## Storage

```python
{
    "contract_id": "...",
    "components": {
        "core_lease_component": {...},
        "simple_solar_contract": {...}
    },
    "cascade_metadata": {
        "cascade": true,
        "executions": [
            {"instance": "...", "results_file": "..."}
        ]
    },
    "execution_order": ["core_lease_component", "simple_solar_contract"]
}
```

## Conclusion

✅ **Use the cascade flag** - It provides valuable metadata without changing solution data
✅ **Store cascade metadata** - Useful for component analysis and UI
✅ **No performance impact** - Just adds one small metadata file
✅ **Better architecture** - Explicit dependency tracking

