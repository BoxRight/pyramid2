# SQL to Serverless Migration - Query Strategy

## The Problem

**SQLite was good for**:
- Complex JOINs across contracts, predicates, solutions
- Aggregations (COUNT, GROUP BY)
- Set operations (finding solutions where predicates are present/absent)
- Cross-contract queries

**Serverless constraints**:
- No SQL database
- Lambda memory limits (3GB max)
- DynamoDB has limited query capabilities (no JOINs, limited aggregations)
- Need to optimize for cost and speed

## Solution: **Pre-compute + Cache Strategy**

### Key Insight

**SQL Approach**: Compute queries on-demand (flexible, but slower)
**Serverless Approach**: Pre-compute analysis during compilation, query results (fast, but need to recompute on changes)

### Recommended Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Compilation Phase (contract_compiler Lambda)            │
├─────────────────────────────────────────────────────────┤
│ 1. Compile contract → Generate JSON                     │
│ 2. Analyze ALL predicates → Pre-compute violations/     │
│    fulfillments                                         │
│ 3. Store results in DynamoDB AnalysisResults table      │
│ 4. Store full JSON in S3 (backup)                       │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Query Phase (contract_query Lambda)                     │
├─────────────────────────────────────────────────────────┤
│ 1. Query DynamoDB AnalysisResults (instant)              │
│ 2. Return pre-computed results                          │
│ 3. No computation needed!                                │
└─────────────────────────────────────────────────────────┘
```

## Implementation

### Option A: Pre-compute During Compilation ✅ **RECOMMENDED**

**When**: During contract compilation

**What**:
- Run full analysis for all predicates
- Store results in DynamoDB `AnalysisResults` table
- Query returns cached results instantly

**Pros**:
- ✅ **Fastest queries** (no computation)
- ✅ **Cost-effective** (compute once, query many times)
- ✅ **No memory limits** for queries
- ✅ **Scalable** to any contract size

**Implementation**:
```python
# In contract_compiler.py (after compilation)
async def compile_laml_contract(...):
    # ... compile contract ...
    
    # Pre-compute analysis for all predicates
    from backend.lib.violation_analysis import LAMLViolationAnalyzer
    analyzer = LAMLViolationAnalyzer(final_results_data)
    
    for predicate_name in predicates:
        # Analyze violation
        violation_result = analyzer.analyze_violation_consequences(predicate_name)
        
        # Store in DynamoDB (or LocalStorage for now)
        storage.save_analysis_results(contract_id, {
            'analysis_type': 'violation',
            'predicate_name': predicate_name,
            'results': violation_result
        })
        
        # Analyze fulfillment
        fulfillment_result = analyzer.analyze_fulfillment_consequences(predicate_name)
        storage.save_analysis_results(contract_id, {
            'analysis_type': 'fulfillment',
            'predicate_name': predicate_name,
            'results': fulfillment_result
        })
```

### Option B: DynamoDB + In-Memory (Current Handler)

**When**: If analysis not pre-computed

**What**:
- Fetch all solutions from DynamoDB
- Load into Lambda memory
- Process using existing Python code

**Pros**:
- ✅ Works immediately
- ✅ No changes needed
- ✅ Handles single contracts well

**Cons**:
- ⚠️ Limited by Lambda memory (3GB)
- ⚠️ Slower than pre-computed
- ⚠️ Recomputes on every query

**Implementation** (already in handler):
```python
# Fetch all solutions
solutions = SOLUTIONS_TABLE.query(contract_id=contract_id)

# Process in memory
analyzer = LAMLViolationAnalyzer(solutions)
result = analyzer.analyze_violation_consequences(predicate_name)
```

### Option C: Hybrid (Best of Both)

**Strategy**:
1. Pre-compute during compilation (fast queries)
2. Fallback to in-memory if not cached (flexibility)
3. Store full JSON in S3 (backup for large contracts)

## Comparison: SQL vs Serverless

| Aspect | SQLite | DynamoDB + Pre-compute | DynamoDB + In-Memory |
|--------|--------|----------------------|---------------------|
| **Query Speed** | Fast | ⚡⚡⚡ Fastest | Fast |
| **Setup Complexity** | Simple | Medium | Simple |
| **Scalability** | Good | ✅✅ Excellent | ⚠️ Memory limited |
| **Cost** | Low | Low (compute once) | Medium (compute each time) |
| **Flexibility** | ✅ Any query | ⚠️ Pre-computed only | ✅ Flexible |
| **Cross-contract** | ✅ Possible | ❌ Not supported | ❌ Not supported |

## What SQL Did That We Need to Replace

### 1. **Complex JOINs** → Pre-compute during compilation
**SQL**: `SELECT * FROM solutions JOIN predicates WHERE...`
**Serverless**: Pre-compute during compilation, store results

### 2. **Aggregations** → Pre-compute aggregations
**SQL**: `COUNT(DISTINCT solution_id) GROUP BY predicate_id`
**Serverless**: Compute during compilation, store counts

### 3. **Set Operations** → In-memory processing
**SQL**: `solution_id NOT IN (SELECT ...)`
**Serverless**: Python set operations in Lambda (already working)

### 4. **Cross-Contract Queries** → Not supported (use separate queries)
**SQL**: Could query across multiple contracts
**Serverless**: Query each contract separately, combine results

## Recommendation

### **Use Pre-compute Strategy** ✅

**Why**:
1. **SQL's advantage**: Complex queries on-demand
2. **Serverless reality**: Lambda memory limits, DynamoDB query limits
3. **Solution**: Pre-compute analysis (like SQL does once), query results many times

**Implementation Steps**:
1. ✅ Add pre-computation to `contract_compiler.py`
2. ✅ Store results in `AnalysisResults` table
3. ✅ Update `contract_query.py` to check cache first
4. ✅ Fallback to in-memory if not cached

**Benefits**:
- ⚡ **Fast queries** (pre-computed)
- 💰 **Cost-effective** (compute once)
- 📈 **Scalable** (no memory limits for queries)
- 🚀 **Serverless-ready** (DynamoDB + S3)

## Migration Checklist

- [ ] Add pre-computation to compilation service
- [ ] Create `AnalysisResults` DynamoDB table
- [ ] Update query service to check cache first
- [ ] Add fallback to in-memory processing
- [ ] Store full JSON in S3 as backup
- [ ] Test with large contracts (1000+ solutions)
- [ ] Monitor Lambda memory usage
- [ ] Optimize DynamoDB GSI for query patterns

## Summary

**Answer**: **Pre-compute analysis during compilation** instead of computing on-demand like SQL.

**Trade-off**: 
- SQL: Flexible queries, but compute each time
- Serverless: Pre-compute once, fast cached queries

**Result**: Faster, cheaper, and more scalable for most use cases!

