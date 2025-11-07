# LAML Contract API - Local Development Server

FastAPI server for the LAML Legal Contract Analysis System. Designed with serverless architecture in mind - all service functions can be extracted to AWS Lambda functions.

## Features

- ✅ **Natural Language to LAML**: Convert natural language descriptions to LAML contracts using Claude API
- ✅ **Contract Compilation**: Compile LAML contracts to AST JSON using `lamlc` binary
- ✅ **Contract Analysis**: Analyze contracts for violations and fulfillments
- ✅ **Query Interface**: Query specific predicates for consequences
- ✅ **HTML Rendering**: Generate HTML contracts from AST
- ✅ **Local Storage**: File-based storage (mimics S3/DynamoDB structure)

## Architecture

The server is structured to mirror AWS Lambda functions:

```
backend/
├── main.py                 # FastAPI app (routes map to Lambda functions)
├── lib/                    # Shared utilities (Lambda-ready)
│   ├── violation_analysis.py
│   └── ast_contract_parser.py
├── services/              # Service modules (extract to Lambda handlers)
│   ├── contract_compiler.py      → laml-compiler Lambda
│   ├── contract_analyzer.py      → laml-analyzer Lambda
│   ├── contract_query.py         → laml-query Lambda
│   ├── nl_to_laml.py             → nl-to-laml-generator Lambda
│   └── contract_renderer.py       → contract-renderer Lambda
└── storage/
    └── local_storage.py    # Local file storage (replace with S3/DynamoDB in Lambda)
```

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3. Run the Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /` - Health check

### Contract Generation
- `POST /contracts/generate-from-nl` - Generate LAML from natural language
  ```json
  {
    "natural_language": "Create a solar lease contract...",
    "contract_type": "solar_lease",
    "jurisdiction": "Mexico"
  }
  ```

### Contract Compilation
- `POST /contracts/compile` - Compile LAML contract
  ```json
  {
    "contract_id": "contract-123",
    "laml_content": "# LAML code here..."
  }
  ```

### Contract Analysis
- `GET /contracts/{contract_id}/analysis` - Get violation/fulfillment analysis

### Contract Query
- `POST /contracts/query` - Query specific predicate
  ```json
  {
    "contract_id": "contract-123",
    "predicate_name": "pay_rent",
    "query_type": "violation"
  }
  ```

### Contract Rendering
- `GET /contracts/{contract_id}/html` - Get rendered HTML contract

### Contract Listing
- `GET /contracts` - List all contracts

## Data Storage

Local storage uses a file-based structure that mimics S3:

```
data/
├── source/contracts/      # LAML source files
├── compiled/ast/          # Compiled AST JSON files
├── analysis/results/      # Analysis results
├── generated/html/       # Rendered HTML contracts
└── contracts_metadata.json # Contracts metadata (simulates DynamoDB)
```

## Migration to Lambda

When ready to deploy to AWS:

1. **Extract Service Functions**: Each function in `services/` can become a Lambda handler
2. **Replace Storage**: Replace `LocalStorage` with `boto3` S3 and DynamoDB clients
3. **Update Paths**: Adjust file paths for Lambda environment
4. **Package Binary**: Include `lamlc` binary in Lambda Layer or container

See `serverless/lambda/query/handler.py` for an example Lambda handler structure.

## Development Notes

- The server runs on port 8000 by default
- CORS is enabled for `localhost:3000` (frontend)
- All service functions are async and can be easily converted to Lambda handlers
- Local storage structure mirrors S3 bucket organization for easy migration

## Troubleshooting

### `lamlc` binary not found
- Ensure the `lamlc` binary is in the project root directory
- Check that it has execute permissions: `chmod +x lamlc`

### Claude API errors
- Verify `ANTHROPIC_API_KEY` is set in `.env` file
- Check API key is valid and has credits

### Import errors
- Ensure you're running from the project root
- Check that `backend/lib/` directory contains utilities
- Verify imports use `from backend.lib.*` syntax

