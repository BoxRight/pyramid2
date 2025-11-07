# Frontend-Backend Connection Setup

## ✅ Fixed: Mock Data Issue

The frontend was defaulting to mock data. I've fixed this by:

1. **Created `.env` file** in `frontend/` directory:
   ```env
   VITE_USE_MOCK_DATA=false
   VITE_API_BASE_URL=/api
   ```

2. **Updated components** to only show MockDataIndicator when mock data is enabled

## 🔄 Restart Required

**IMPORTANT**: You must restart the frontend dev server for `.env` changes to take effect!

```bash
# Stop the frontend server (Ctrl+C)
# Then restart:
cd frontend
npm run dev
```

## Verification Steps

1. **Check Backend is Running**:
   ```bash
   curl http://localhost:8000/
   # Should return: {"status":"ok","service":"LAML Contract API","version":"1.0.0"}
   ```

2. **Check Frontend**:
   - After restart, the "Using Mock Data" indicator should disappear
   - Browser console should show API calls to `/api/...`
   - No CORS errors

3. **Test Connection**:
   - Try loading a contract from `contracts/` folder
   - Compile it
   - Check that it uses the real backend (not mock data)

## Troubleshooting

### Still Shows Mock Data After Restart

1. **Check `.env` file exists**:
   ```bash
   cat frontend/.env
   # Should show: VITE_USE_MOCK_DATA=false
   ```

2. **Check backend is running**:
   ```bash
   curl http://localhost:8000/
   ```

3. **Check browser console** for errors:
   - Open DevTools (F12)
   - Look for network errors or CORS issues

### Backend Not Responding

1. **Check if backend is running**:
   ```bash
   ps aux | grep "python.*main.py"
   ```

2. **Start backend**:
   ```bash
   cd backend
   python main.py
   ```

3. **Check backend logs** for errors

### CORS Errors

The backend CORS is configured for:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:5173` (alternative Vite port)
- `http://127.0.0.1:5173`

If you're using a different port, update `backend/main.py` CORS configuration.

### API Calls Fail

1. **Check Vite proxy** is working:
   - Frontend calls `/api/contracts/compile`
   - Vite proxy should rewrite to `http://localhost:8000/contracts/compile`

2. **Check backend logs** for incoming requests

3. **Test backend directly**:
   ```bash
   curl -X POST http://localhost:8000/contracts/compile \
     -H "Content-Type: application/json" \
     -d '{"contract_id":"test","laml_content":"..."}'
   ```

## Next Steps

After restarting the frontend:
1. ✅ Mock data indicator should be gone
2. ✅ Real API calls should work
3. ✅ Backend should receive requests
4. ✅ Query caching should work (first query computes, second uses cache)

