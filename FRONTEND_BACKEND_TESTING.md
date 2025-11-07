# Frontend-Backend Testing Readiness

## ✅ Ready to Test!

The backend is ready to test with the frontend. Here's what's configured:

## Configuration Summary

### Backend (FastAPI)
- ✅ **Port**: 8000
- ✅ **CORS**: Configured for `http://localhost:3000` and `http://127.0.0.1:3000`
- ✅ **All Endpoints**: Implemented and match frontend expectations
- ✅ **Query Caching**: Implemented (compute-on-first-request pattern)

### Frontend (Vite + React)
- ✅ **Port**: 3000 (configured in `vite.config.js`)
- ✅ **Proxy**: Configured to proxy `/api` → `http://localhost:8000`
- ✅ **API Client**: Uses `http://localhost:8000/api` (or env var)

### API Endpoints Mapping

| Frontend Call | Backend Endpoint | Status |
|--------------|------------------|--------|
| `POST /contracts/generate-from-nl` | `POST /contracts/generate-from-nl` | ✅ |
| `POST /contracts/compile` | `POST /contracts/compile` | ✅ |
| `GET /contracts/{id}/analysis` | `GET /contracts/{id}/analysis` | ✅ |
| `POST /contracts/query` | `POST /contracts/query` | ✅ |
| `GET /contracts/{id}/html` | `GET /contracts/{id}/html` | ✅ |
| `GET /contracts` | `GET /contracts` | ✅ |

## Quick Start

### 1. Start Backend

```bash
cd backend
python main.py
```

Or use the start script:
```bash
./backend/start.sh
```

Backend will be available at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 2. Start Frontend

```bash
cd frontend
npm install  # If not already done
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### 3. Configure Frontend (Optional)

Create `frontend/.env` file:
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_MOCK_DATA=false  # Set to false to use real backend
```

**Note**: With Vite proxy configured, the frontend can also use `/api` (relative URL) which will be proxied automatically.

## Testing Checklist

### ✅ Backend Health Check
- [ ] Visit `http://localhost:8000` - should return health check
- [ ] Visit `http://localhost:8000/docs` - should show API documentation

### ✅ Frontend Connection
- [ ] Start frontend - should connect to backend
- [ ] Check browser console - no CORS errors
- [ ] Mock data indicator should disappear (if backend is connected)

### ✅ Contract Workflow
- [ ] **Load Existing Contract**: Use contract from `contracts/` folder
- [ ] **Compile Contract**: Should compile successfully
- [ ] **Analyze Contract**: Should show violation/fulfillment analysis
- [ ] **Query Predicate**: Should return cached results on subsequent queries
- [ ] **View HTML**: Should render contract HTML
- [ ] **List Contracts**: Should show all contracts

### ✅ Query Caching
- [ ] First query: Should compute (slower)
- [ ] Second query (same predicate): Should return instantly from cache
- [ ] Recompile contract: Should invalidate cache

## Troubleshooting

### CORS Errors
**Problem**: CORS errors in browser console
**Solution**: 
- Check backend is running on port 8000
- Check frontend is using port 3000
- Verify CORS origins in `backend/main.py` match frontend URL

### API Connection Failed
**Problem**: Frontend can't connect to backend
**Solution**:
- Check backend is running: `curl http://localhost:8000`
- Check frontend proxy configuration in `vite.config.js`
- Try setting `VITE_API_BASE_URL=http://localhost:8000/api` in frontend `.env`

### Mock Data Still Showing
**Problem**: Frontend still uses mock data
**Solution**:
- Set `VITE_USE_MOCK_DATA=false` in `frontend/.env`
- Or remove `VITE_USE_MOCK_DATA` from `.env` (defaults to true if not set)
- Restart frontend dev server

### Query Returns Slow
**Problem**: First query is slow, subsequent are fast
**Solution**: This is expected! First query computes, subsequent queries use cache. This is the cache-aside pattern working correctly.

### Contract Not Found
**Problem**: `Contract {id} not compiled` error
**Solution**:
- Make sure contract is compiled first via `/contracts/compile` endpoint
- Check contract exists in `data/source/contracts/` directory

## What's Working

✅ **All API endpoints** are implemented
✅ **CORS** is configured correctly
✅ **Query caching** is implemented (compute-on-first-request)
✅ **Cache invalidation** on contract recompilation
✅ **Component queries** supported (via `instance_name` parameter)
✅ **Error handling** with proper HTTP status codes

## Next Steps After Testing

1. **Test Natural Language Generation** (requires ANTHROPIC_API_KEY)
2. **Test with Large Contracts** (1000+ solutions)
3. **Monitor Cache Performance** (first query vs cached query)
4. **Test Component Queries** (query specific components)
5. **Test Error Cases** (invalid predicates, missing contracts)

## Notes

- **Query caching**: First query computes, subsequent queries use cache
- **Cache invalidation**: Automatically invalidated when contract is recompiled
- **Component support**: Can query specific components via `instance_name` parameter
- **Mock data fallback**: Frontend falls back to mock data if backend is unavailable

