# Serverless Query Strategy - Revised (User-Driven Queries)

## The Problem with Pre-computing Everything

**Issue**: Users request specific queries, we can't pre-compute all possible combinations

**Why pre-compute everything doesn't work**:
- ❌ Users query specific predicates
- ❌ Unknown query patterns
- ❌ Wasteful to compute unused queries
- ❌ Can't predict all user needs

## Better Strategy: **Compute on First Request + Cache**

### Recommended Architecture

```
┌─────────────────────────────────────────────────────────┐
│ User Query Request                                       │
├─────────────────────────────────────────────────────────┤
│ 1. Check DynamoDB AnalysisResults cache                   │
│    - Key: contract_id#violation#predicate_name           │
│    - If found → Return cached result (instant)           │
└─────────────────────────────────────────────────────────┘
                           ↓ (if not cached)
┌─────────────────────────────────────────────────────────┐
│ Compute Analysis (First Time)                           │
├─────────────────────────────────────────────────────────┤
│ 1. Load results JSON from S3                            │
│ 2. Process in Lambda memory                              │
│ 3. Compute violation/fulfillment analysis                │
│ 4. Store result in DynamoDB (cache)                       │
│ 5. Return result                                          │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Future Queries (Cached)                                  │
├─────────────────────────────────────────────────────────┤
│ 1. Query DynamoDB → Return cached result (instant)       │
│ 2. No computation needed                                  │
└─────────────────────────────────────────────────────────┘
```

## Implementation Strategy

### Option 1: Cache on First Query ✅ **RECOMMENDED**

**Strategy**: Compute when requested, cache for future

**Flow**:
```
User Query → Check Cache → If miss: Compute → Cache → Return
```

**Pros**:
- ✅ Only computes what users actually query
- ✅ Fast subsequent queries (cached)
- ✅ No wasted computation
- ✅ Flexible (handles any query)

**Cons**:
- ⚠️ First query slower (computes)
- ⚠️ Need to handle cache invalidation

**Implementation**:
```python
async def query_contract_predicate(contract_id, predicate_name, query_type, storage):
    # Check cache first
    cache_key = f"{contract_id}#{query_type}#{predicate_name}"
    cached = storage.get_analysis_cache(cache_key)
    
    if cached:
        return cached  # Instant return!
    
    # Cache miss - compute on demand
    results_data = storage.get_compiled_results(contract_id)
    analyzer = LAMLViolationAnalyzer(results_data)
    
    if query_type == "violation":
        result = analyzer.analyze_violation_consequences(predicate_name)
    else:
        result = analyzer.analyze_fulfillment_consequences(predicate_name)
    
    # Cache for future queries
    storage.save_analysis_cache(cache_key, result)
    
    return result
```

### Option 2: Smart Pre-computation (Optional)

**Strategy**: Pre-compute most common queries, cache others on-demand

**When to Pre-compute**:
- During compilation: Pre-compute for top 5-10 most common predicates
- Common patterns: `pay_rent`, `grant_use`, `return_system`, etc.
- Based on contract type: Different predicates for solar vs lease

**Pros**:
- ✅ Common queries are instant
- ✅ Others computed on-demand

**Cons**:
- ⚠️ Need to identify "common" predicates
- ⚠️ More complex logic

### Option 3: Hybrid (Best for Production)

**Strategy**: 
1. Pre-compute common queries during compilation
2. Cache user queries on-demand
3. Store full JSON in S3 for large contracts

## DynamoDB Schema for Caching

### AnalysisResults Table (Cache)

```
PK: contract_id
SK: analysis_type#predicate_name
  - Example: "violation#pay_rent"
  - Example: "fulfillment#grant_use"

Attributes:
  - analysis_type: "violation" | "fulfillment"
  - predicate_name: "pay_rent"
  - results: { ... full analysis result ... }
  - computed_at: timestamp
  - ttl: expiration (optional, for cache invalidation)
```

### Query Pattern

```python
# Check cache
response = ANALYSIS_TABLE.get_item(
    Key={
        'contract_id': contract_id,
        'analysis_key': f'violation#{predicate_name}'
    }
)

if 'Item' in response:
    return response['Item']['results']  # Cached!

# Cache miss - compute
result = compute_analysis(...)

# Store in cache
ANALYSIS_TABLE.put_item(
    Item={
        'contract_id': contract_id,
        'analysis_key': f'violation#{predicate_name}',
        'results': result,
        'computed_at': datetime.utcnow().isoformat()
    }
)
```

## Storage Strategy

### S3 (Full Data)
```
s3://bucket/
├── compiled/results/{contract_id}_{instance}.json  # Full solution data
└── analysis/results/{contract_id}.json              # Full analysis (backup)
```

### DynamoDB (Cache)
```
AnalysisResults:
  - contract_id#violation#predicate_name → cached result
  - contract_id#fulfillment#predicate_name → cached result
```

## Cache Invalidation

**When to invalidate**:
- Contract recompiled → Invalidate all caches for that contract
- Contract updated → Invalidate caches
- TTL expiration → Auto-expire old caches

**Implementation**:
```python
# On contract recompilation
def invalidate_contract_cache(contract_id):
    # Delete all cached analyses for this contract
    ANALYSIS_TABLE.query(
        KeyConditionExpression='contract_id = :cid',
        ExpressionAttributeValues={':cid': contract_id}
    )
    # Delete all items (or use TTL)
```

## Cost Analysis

### Compute on First Request + Cache

**First Query** (cache miss):
- Lambda compute: ~500ms processing
- S3 read: ~100ms (load JSON)
- DynamoDB write: ~50ms (cache result)
- **Total**: ~650ms (one-time cost)

**Subsequent Queries** (cache hit):
- DynamoDB read: ~10ms
- **Total**: ~10ms (instant!)

**Cost**:
- First query: Lambda compute time + S3 read
- Cached queries: DynamoDB read only (cheap)
- **Break-even**: If query is requested 2+ times, caching saves money

## Recommended Implementation

### Step 1: Add Cache Check to Query Service

```python
# backend/services/contract_query.py
async def query_contract_predicate(...):
    # Check cache first
    cache_key = f"{contract_id}#{query_type}#{predicate_name}"
    cached = storage.get_analysis_cache(cache_key)
    
    if cached:
        return cached  # Instant return!
    
    # Cache miss - compute
    results_data = storage.get_compiled_results(contract_id, instance_name)
    analyzer = LAMLViolationAnalyzer(results_data)
    
    if query_type == "violation":
        result = analyzer.analyze_violation_consequences(predicate_name)
    else:
        result = analyzer.analyze_fulfillment_consequences(predicate_name)
    
    # Cache result
    storage.save_analysis_cache(cache_key, result)
    
    return result
```

### Step 2: Add Cache Storage Methods

```python
# backend/storage/local_storage.py
def get_analysis_cache(self, cache_key: str) -> Optional[Dict]:
    """Get cached analysis result"""
    # Check DynamoDB AnalysisResults table
    # For local: check analysis/results/{contract_id}.json
    
def save_analysis_cache(self, cache_key: str, result: Dict):
    """Save analysis result to cache"""
    # Store in DynamoDB AnalysisResults table
    # For local: merge into analysis/results/{contract_id}.json
```

### Step 3: Invalidate on Recompilation

```python
# backend/services/contract_compiler.py
async def compile_laml_contract(...):
    # ... compile ...
    
    # Invalidate old caches when contract is recompiled
    storage.invalidate_contract_cache(contract_id)
    
    # ... continue with compilation ...
```

## Summary

### Strategy: **Compute on First Request + Cache**

**Why**:
- ✅ Only computes what users actually query
- ✅ Caches results for instant future queries
- ✅ No wasted computation
- ✅ Flexible (handles any query pattern)

**Trade-off**:
- First query: Slower (computes)
- Subsequent queries: Fast (cached)

**This is better than**:
- ❌ Pre-computing everything (wasteful)
- ❌ Always computing (slow and expensive)
- ✅ Computing once, caching forever (optimal)

**Result**: 
- Users get fast responses (cached queries)
- Cost-effective (compute once per query)
- Scalable (DynamoDB handles cache lookups)

