# Serverless Query Strategy - SQL to Serverless Migration

## Current State Analysis

### SQLite Queries (What They Did)

**Complex Operations**:
1. **Multi-table JOINs**: Contracts → Predicates → Solutions
2. **Set operations**: Find solutions where predicate is present/absent
3. **Aggregations**: COUNT, GROUP BY across solutions
4. **Cross-contract analysis**: Find predicates across multiple contracts
5. **Vector analysis**: Compare solution vectors (predicate presence/absence)

**Example SQL Pattern**:
```sql
WITH violation_solutions AS (
    SELECT DISTINCT s.solution_id
    FROM solutions s
    WHERE s.contract_id = ?
    AND s.solution_id NOT IN (
        SELECT DISTINCT s2.solution_id
        FROM solutions s2
        JOIN predicates pred ON ...
        WHERE pred.predicate_name = ?
    )
),
predicate_counts AS (
    SELECT cp.id, COUNT(DISTINCT s.solution_id) as count
    FROM contract_predicates cp
    LEFT JOIN solutions s ON ...
    GROUP BY cp.id
)
SELECT * FROM predicate_counts WHERE count = total OR count = 0
```

### Current Python Approach (Working)

**In-Memory Processing**:
- Loads entire JSON file (solutions + mappings)
- Processes in Python memory
- No database needed
- Fast for single contracts

**Limitations**:
- ⚠️ All solutions must fit in Lambda memory
- ⚠️ No cross-contract queries
- ⚠️ Recomputes on every query

## Serverless Architecture Options

### Option 1: DynamoDB + In-Memory Processing ✅ **RECOMMENDED**

**Strategy**: Store data in DynamoDB, fetch all solutions, process in Lambda

**Architecture**:
```
DynamoDB Tables:
├── Contracts (PK: contract_id)
├── Predicates (PK: contract_id, SK: predicate_id, GSI: predicate_name)
├── Solutions (PK: contract_id, SK: solution_id)
└── AnalysisResults (PK: contract_id, SK: analysis_type#predicate_name)

S3:
└── compiled/results/{contract_id}_{instance}.json (full JSON backup)
```

**Query Flow**:
1. Query DynamoDB for contract solutions
2. Load all solutions into Lambda memory
3. Process using existing `violation_analysis.py` logic
4. Return results

**Pros**:
- ✅ Simple migration (already have handler)
- ✅ Fast for contracts with <1000 solutions
- ✅ No new services needed
- ✅ Works with existing Python code

**Cons**:
- ⚠️ Limited by Lambda memory (3GB max)
- ⚠️ Slower for huge contracts (1000+ solutions)
- ⚠️ No cross-contract queries

**When to Use**: Contracts with <1000 solutions, single-contract queries

### Option 2: S3 + Pre-computed Analysis ✅ **BEST FOR PRODUCTION**

**Strategy**: Pre-compute analysis during compilation, store results

**Architecture**:
```
Compilation → Analysis → Store Results
├── DynamoDB: AnalysisResults table
└── S3: Full analysis JSON (backup)
```

**Query Flow**:
1. Query DynamoDB AnalysisResults table
2. Return pre-computed results
3. No computation needed

**Pros**:
- ✅ **Fastest queries** (no computation)
- ✅ **Scalable** (works for any contract size)
- ✅ **Cost-effective** (compute once, query many times)
- ✅ **No memory limits**

**Cons**:
- ⚠️ Need to recompute when contract changes
- ⚠️ More storage (but minimal cost)

**When to Use**: Production systems, frequent queries

### Option 3: DynamoDB + S3 Hybrid ✅ **BALANCED**

**Strategy**: Store metadata in DynamoDB, full data in S3, use both

**Architecture**:
```
DynamoDB:
├── Contracts (metadata)
├── Predicates (metadata)
└── AnalysisResults (pre-computed)

S3:
├── compiled/results/{contract_id}.json (full solution data)
└── analysis/results/{contract_id}.json (pre-computed analysis)
```

**Query Flow**:
- **Simple queries**: Return from AnalysisResults table
- **Complex queries**: Load from S3, process in Lambda
- **Cache**: Store in DynamoDB for future queries

**Pros**:
- ✅ Flexible (simple = fast, complex = possible)
- ✅ Cost-effective (S3 storage is cheap)
- ✅ Can scale to large contracts

**Cons**:
- ⚠️ More complex logic
- ⚠️ S3 reads add latency (~100ms)

**When to Use**: Mixed query patterns, varying contract sizes

### Option 4: Amazon Athena (SQL on S3) ⚠️ **OVERKILL**

**Strategy**: Store JSON in S3, query with SQL via Athena

**Pros**:
- ✅ SQL-like queries
- ✅ Scales to any size
- ✅ No Lambda memory limits

**Cons**:
- ❌ **Expensive** ($5/TB scanned)
- ❌ **Slow** (seconds, not milliseconds)
- ❌ **Overkill** for this use case
- ❌ Complex setup

**When to Use**: Only if you need true SQL queries across huge datasets

## Recommendation: **Hybrid Approach (Option 3)**

### Phase 1: Current Approach (DynamoDB + In-Memory)
- ✅ Use existing DynamoDB schema
- ✅ Load solutions into Lambda memory
- ✅ Process with existing Python code
- ✅ Works for contracts <1000 solutions

### Phase 2: Pre-compute Analysis (Add Caching)
- ✅ During compilation, run analysis
- ✅ Store results in DynamoDB `AnalysisResults` table
- ✅ Query returns cached results (fast)
- ✅ Recompute only when contract changes

### Phase 3: S3 Backup (Scale)
- ✅ Store full JSON in S3 as backup
- ✅ Use for large contracts that don't fit in memory
- ✅ Stream processing for huge contracts

## Implementation Strategy

### Current Backend (Already Works)
```python
# Uses JSON files directly
analyzer = LAMLViolationAnalyzer('laml_results_*.json')
result = analyzer.analyze_violation_consequences('pay_rent')
```

### Serverless Handler (Needs Update)
```python
# Current: DynamoDB + In-Memory
def analyze_violation(contract_id, predicate_name):
    # 1. Get all solutions from DynamoDB
    solutions = SOLUTIONS_TABLE.query(...)
    
    # 2. Check if analysis is cached
    cached = ANALYSIS_TABLE.get(...)
    if cached:
        return cached['results']
    
    # 3. Process in Lambda (like current Python code)
    analyzer = LAMLViolationAnalyzer(solutions)
    result = analyzer.analyze_violation_consequences(predicate_name)
    
    # 4. Cache results
    ANALYSIS_TABLE.put(...)
    
    return result
```

### Enhanced: Pre-compute During Compilation
```python
# In contract_compiler Lambda
async def compile_laml_contract(...):
    # ... compile contract ...
    
    # Pre-compute analysis for all predicates
    analyzer = LAMLViolationAnalyzer(results_data)
    for predicate in predicates:
        violation = analyzer.analyze_violation_consequences(predicate)
        fulfillment = analyzer.analyze_fulfillment_consequences(predicate)
        
        # Store in DynamoDB
        ANALYSIS_TABLE.put_item(
            Item={
                'contract_id': contract_id,
                'analysis_key': f'violation#{predicate}',
                'results': violation,
                'computed_at': datetime.utcnow().isoformat()
            }
        )
```

## Query Patterns Comparison

| Query Type | SQLite | DynamoDB | S3 + Pre-compute |
|------------|--------|----------|------------------|
| **Single contract, single predicate** | ✅ Fast | ✅ Fast | ✅✅ Fastest |
| **Cross-contract queries** | ✅ Possible | ❌ Hard | ❌ Not supported |
| **Large contracts (1000+ solutions)** | ✅ Fast | ⚠️ Memory limit | ✅✅ Fast |
| **Complex aggregations** | ✅ Easy | ⚠️ In Lambda | ✅ Pre-computed |
| **Cost** | Low | Medium | Low (S3) + Low (compute once) |

## Migration Path

### Step 1: Keep Current Approach ✅
- Use DynamoDB + in-memory processing
- Works for most contracts
- Already implemented

### Step 2: Add Pre-computation ✅
- Compute analysis during compilation
- Store in `AnalysisResults` table
- Query returns cached results

### Step 3: Add S3 Backup (if needed)
- Store full JSON in S3
- Use for contracts that exceed Lambda memory
- Stream processing for huge datasets

## Answer to Your Question

**"SQL was adequate for optimized queries, but now that we plan serverless what should we do?"**

### Short Answer: **Pre-compute Analysis + DynamoDB**

**Why**:
1. **SQL's strength**: Complex queries with JOINs and aggregations
2. **Serverless reality**: Lambda has memory limits, DynamoDB has query limitations
3. **Solution**: Pre-compute analysis during compilation (like SQL does once), store results, query instantly

### Key Insight

**SQL advantage**: Could do complex queries on-demand
**Serverless approach**: Do complex computation once (during compilation), query results many times

**Trade-off**: 
- SQL: Compute on-demand (flexible, but slower per query)
- Serverless: Pre-compute once (fast queries, but need to recompute on changes)

### Recommended Architecture

```
Compilation Flow:
1. Compile contract → Generate JSON
2. Analyze contract → Pre-compute violations/fulfillments
3. Store in DynamoDB AnalysisResults table
4. Store full JSON in S3 (backup)

Query Flow:
1. Query DynamoDB AnalysisResults (instant)
2. If not found, compute on-demand (fallback)
3. Cache result for future queries
```

This gives you:
- ✅ **Fast queries** (pre-computed)
- ✅ **Scalable** (no memory limits for queries)
- ✅ **Cost-effective** (compute once, query many times)
- ✅ **Serverless-ready** (DynamoDB + S3)

