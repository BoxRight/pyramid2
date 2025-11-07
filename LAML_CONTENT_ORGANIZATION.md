# LAML Content Organization Analysis

## Current Structure

```
Pyramid2/
├── contracts/     # User-generated contracts (instances)
├── laws/          # Legal framework libraries (reusable)
└── principles/    # Legal principle libraries (reusable)
```

**Import patterns**:
- Contracts: `import "../laws/ccf_core_lease.laml"`
- Contracts: `import "../principles/conditional_claim.laml"`

## Analysis

### Current Location: Root Level

**Pros**:
- ✅ Simple, flat structure
- ✅ Clear separation of concerns
- ✅ Easy to understand at a glance
- ✅ Works with current relative imports
- ✅ Matches how lamlc resolves imports

**Cons**:
- ⚠️ Adds to root directory clutter
- ⚠️ Not grouped with other domain content
- ⚠️ No clear indication these are "content" vs "code"

### Key Considerations

1. **Import Resolution**
   - `lamlc` resolves imports relative to the contract file location
   - Current paths: `../laws/` and `../principles/` work because contracts are in `contracts/`
   - Moving would require updating all import paths

2. **Semantic Grouping**
   - These are **domain content** (legal knowledge), not application code
   - They're **reusable libraries** (laws/principles) vs **instances** (contracts)
   - They form a **legal knowledge base**

3. **Backend Usage**
   - Backend writes temporary contract files to `contracts/` directory
   - Imports must resolve correctly from that location
   - Current structure supports this

## Options

### Option 1: Keep at Root (Current) ✅ **RECOMMENDED**

**Structure**:
```
Pyramid2/
├── contracts/
├── laws/
├── principles/
├── backend/
├── frontend/
└── ...
```

**Pros**:
- ✅ Works with current imports (no changes needed)
- ✅ Simple and clear
- ✅ Each folder has distinct purpose
- ✅ Easy to navigate

**Cons**:
- ⚠️ Root level clutter (but acceptable for domain content)

**Verdict**: **Keep as-is** - The simplicity and functionality outweigh minor clutter concerns.

### Option 2: Group in `laml/` Directory

**Structure**:
```
Pyramid2/
├── laml/
│   ├── contracts/
│   ├── laws/
│   └── principles/
├── backend/
├── frontend/
└── ...
```

**Pros**:
- ✅ Groups all LAML content together
- ✅ Reduces root clutter
- ✅ Clear semantic grouping

**Cons**:
- ❌ Requires updating ALL import paths (breaking change)
- ❌ Contracts would need: `import "../laml/laws/..."` or `import "laws/..."`
- ❌ Backend would need updates to path resolution
- ❌ More nested paths

**Verdict**: **Not worth it** - Breaking change for minimal benefit.

### Option 3: Group in `content/` or `domain/`

**Structure**:
```
Pyramid2/
├── content/
│   ├── contracts/
│   ├── laws/
│   └── principles/
```

**Verdict**: Same issues as Option 2 - breaking changes.

### Option 4: Keep Laws/Principles Together, Separate Contracts

**Structure**:
```
Pyramid2/
├── contracts/          # User contracts (instances)
├── laml/              # LAML libraries
│   ├── laws/
│   └── principles/
```

**Pros**:
- ✅ Groups reusable libraries
- ✅ Contracts stay separate (they're instances)
- ⚠️ Still requires import path updates

**Verdict**: **Maybe** - But still requires breaking changes.

## Recommendation: **Keep Current Structure**

### Why Keep at Root?

1. **Functionality First**
   - Current structure works perfectly with lamlc
   - No import path issues
   - Backend integration is clean

2. **Clear Semantics**
   - `contracts/` = specific contract instances
   - `laws/` = reusable legal frameworks
   - `principles/` = reusable legal principles
   - Each has distinct purpose at root level

3. **Domain Content Deserves Visibility**
   - These aren't just code - they're the **legal knowledge base**
   - Having them at root makes them prominent and accessible
   - Similar to how `docs/` or `tests/` are often at root

4. **Minimal Clutter Impact**
   - Only 3 folders (vs potentially many root files)
   - Each has clear, distinct purpose
   - Better than grouping everything under one folder

### Alternative: If You Want to Reduce Root Clutter

**Option**: Keep structure but add a `laml/` symlink or alias for clarity:

```
Pyramid2/
├── contracts/    # Contract instances
├── laws/         # Legal frameworks
├── principles/   # Legal principles
└── laml -> .     # Symlink for semantic clarity (optional)
```

But this is unnecessary complexity.

## Comparison with Other Projects

### Similar Patterns:
- **Laravel**: `app/`, `config/`, `database/`, `routes/` at root
- **Django**: `manage.py`, `settings/`, `apps/` at root
- **Rails**: `app/`, `config/`, `db/`, `lib/` at root

**Pattern**: Domain-specific content folders at root are **common and acceptable**.

## Final Recommendation

✅ **Keep `contracts/`, `laws/`, and `principles/` at root level**

**Reasons**:
1. Works perfectly with current import system
2. Clear, distinct purposes
3. Domain content deserves visibility
4. Minimal clutter (only 3 folders)
5. Breaking changes not worth the minor organizational benefit

**If you still want to organize**:
- Consider moving OTHER root files (binaries, docs) first
- These three folders are well-organized already
- They're the core domain content, not clutter

