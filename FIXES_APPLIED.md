# Fixes Applied for Contract Document and Analysis Display

## Issues Fixed

### 1. Contract Document Not Displaying
**Problem**: `parsed_contract` was not being returned correctly from compile endpoint.

**Fix Applied**:
- Improved AST file path handling (handles both absolute and relative paths)
- Added better error logging to debug parsing issues
- AST file path is now correctly resolved from storage

**What to check**:
- Backend logs should show: `✅ Successfully parsed contract: X clauses`
- If parsing fails, you'll see: `❌ Warning: Could not parse contract: ...`

### 2. Analysis Results Seem Hardcoded
**Problem**: Frontend might still be using mock data even though `.env` is set.

**Fix Applied**:
- Verified `.env` file exists with `VITE_USE_MOCK_DATA=false`
- Analysis endpoint returns real data (verified with curl)

**What to check**:
1. **Restart frontend** - `.env` changes require restart
2. Check browser console - should show API calls, not "using mock data"
3. Check network tab - should see requests to `/api/contracts/.../analysis`

## Next Steps

### To Fix Contract Document Display:
1. **Restart backend** (to apply AST path fixes)
2. **Try compiling a contract again**
3. **Check backend logs** for parsing messages
4. **Check browser console** for any errors

### To Fix Analysis Display:
1. **Restart frontend dev server** (to apply `.env` changes)
2. **Check browser console** - should NOT see "using mock data" warnings
3. **Check network tab** - verify API calls are being made
4. **Compare analysis results** - real data should match backend logs

## Verification

### Contract Document:
- Backend should log: `✅ Successfully parsed contract: X clauses`
- Frontend should display: Contract document with metadata, parties, clauses

### Analysis Results:
- Backend logs show: Real analysis with predicates like `return_system`, `pay_rent`, etc.
- Frontend should show: Same predicates and violation/fulfillment counts
- Should NOT show: Mock data indicators or hardcoded values

## Debugging

If contract document still doesn't display:
```bash
# Check backend logs for parsing errors
# Look for: "❌ Warning: Could not parse contract"

# Check if AST file exists
ls -la data/compiled/ast/*.json

# Test parsing directly
python3 -c "from backend.lib.ast_contract_parser import ASTContractParser; parser = ASTContractParser('data/compiled/ast/YOUR_CONTRACT_ID.json'); print(parser.parse_contract())"
```

If analysis still seems hardcoded:
```bash
# Check frontend .env
cat frontend/.env

# Restart frontend
cd frontend && npm run dev

# Check browser console for API calls
# Open DevTools → Network tab → Look for /api/contracts/.../analysis
```

