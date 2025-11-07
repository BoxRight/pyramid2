# Development Setup Guide

This guide explains how to set up and run the LAML Contract System locally for development.

## Architecture Overview

The system consists of:
- **Frontend**: React app (Vite) on port 3000
- **Backend**: FastAPI server on port 8000
- **Storage**: Local file-based storage (mimics S3/DynamoDB)

## Quick Start

### 1. Backend Setup

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
# Create .env file in project root:
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Start the server
python main.py
# Or use the startup script:
./start.sh
```

The backend API will be available at:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 3. Connect Frontend to Backend

The frontend is configured to automatically connect to the backend at `http://localhost:8000/api`. 

If the backend is not available, it will automatically fall back to mock data (you'll see a "Using Mock Data" indicator).

To disable mock data and force API usage:

```bash
# In frontend/.env
VITE_USE_MOCK_DATA=false
VITE_API_BASE_URL=http://localhost:8000/api
```

## Development Workflow

### 1. Start Both Servers

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 2. Test the Flow

1. **Generate Contract**: Use natural language input to generate a LAML contract
2. **Compile**: The contract is automatically compiled after generation
3. **Analyze**: Analysis runs automatically after compilation
4. **Query**: Use the query interface to ask about specific predicates

### 3. View Data

Local storage is in the `data/` directory:
```
data/
├── source/contracts/      # LAML source files
├── compiled/ast/          # Compiled AST JSON
├── analysis/results/      # Analysis results
├── generated/html/       # Rendered HTML
└── contracts_metadata.json
```

## API Endpoints

### Contract Operations
- `POST /contracts/generate-from-nl` - Generate LAML from natural language
- `POST /contracts/compile` - Compile LAML contract
- `GET /contracts/{id}/analysis` - Get analysis results
- `POST /contracts/query` - Query specific predicate
- `GET /contracts/{id}/html` - Get rendered HTML
- `GET /contracts` - List all contracts

See `backend/README.md` for detailed API documentation.

## Troubleshooting

### Backend Issues

**`lamlc` binary not found:**
- Ensure `lamlc` is in the project root
- Check execute permissions: `chmod +x lamlc`

**Claude API errors:**
- Verify `ANTHROPIC_API_KEY` is set in `.env`
- Check API key is valid

**Import errors:**
- Ensure you're running from project root
- Check that `backend/lib/` directory contains utilities
- Verify imports use `from backend.lib.*` syntax

### Frontend Issues

**API connection errors:**
- Verify backend is running on port 8000
- Check CORS settings in `backend/main.py`
- Frontend will automatically use mock data if backend unavailable

**Mock data always showing:**
- Set `VITE_USE_MOCK_DATA=false` in `frontend/.env`
- Restart the dev server

## Serverless Architecture Notes

The backend is designed to mirror AWS Lambda functions:

- Each service module (`backend/services/*.py`) can be extracted to a Lambda handler
- Storage layer (`backend/storage/local_storage.py`) can be replaced with boto3 S3/DynamoDB
- All functions are async and stateless (Lambda-ready)

See `ARCHITECTURE.md` for deployment details.

## Next Steps

1. **Test Natural Language Generation**: Requires valid `ANTHROPIC_API_KEY`
2. **Test Compilation**: Requires `lamlc` binary in project root
3. **Test Analysis**: Requires compiled contracts
4. **Test Queries**: Requires analyzed contracts

## Environment Variables

### Backend (.env in project root)
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Frontend (frontend/.env)
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_MOCK_DATA=false
```

