# Frontend Setup Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   - Navigate to `http://localhost:3000`

## What You Get

✅ **Dark Theme UI** - VS Code-inspired design matching your existing HTML files  
✅ **Natural Language Input** - Convert plain English to LAML contracts  
✅ **LAML Code Editor** - Syntax-highlighted code editor  
✅ **Contract Analysis** - View violation/fulfillment scenarios  
✅ **Query Interface** - Ask questions about contract predicates  
✅ **Contract Management** - Browse and manage contracts  

## Component Overview

### Natural Language Input
- Enter contract descriptions in plain English
- Select contract type (solar lease, generic lease, etc.)
- Choose jurisdiction (Mexico, US, etc.)
- Generates LAML code using Claude API

### LAML Viewer
- Code editor with syntax highlighting
- Compile contracts
- Trigger analysis automatically after compilation
- View formatted code preview

### Contract Analysis
- View total solutions and predicates
- See violation scenarios
- See fulfillment scenarios
- Understand consequences for each predicate

### Query Interface
- Query specific predicates
- Choose violation or fulfillment analysis
- See detailed consequences
- Example predicates included

### Contract List
- Browse all contracts
- View contract metadata
- Quick access to contracts

## API Integration

The frontend is ready to connect to your backend API. Currently configured to use:
- Local development: `http://localhost:8000/api`
- Production: Set via `VITE_API_BASE_URL` environment variable

### Expected API Endpoints

- `POST /contracts/generate-from-nl` - Generate LAML from natural language
- `POST /contracts/compile` - Compile LAML contract  
- `GET /contracts/{id}/analysis` - Get analysis results
- `POST /contracts/query` - Query contract predicates
- `GET /contracts/{id}/html` - Get rendered HTML
- `GET /contracts` - List all contracts

## Next Steps

1. **Backend Integration**: Connect to your Lambda functions or local backend
2. **Claude API**: Implement the NL-to-LAML Lambda function
3. **Testing**: Test the full flow end-to-end
4. **Deployment**: Deploy to S3 + CloudFront or your preferred hosting

## Troubleshooting

**Port already in use?**
- Change port in `vite.config.js` or use `npm run dev -- --port 3001`

**API connection errors?**
- Check `VITE_API_BASE_URL` in `.env`
- Ensure backend is running
- Check CORS settings on backend

**Syntax highlighting not working?**
- Ensure `react-syntax-highlighter` is installed
- Check browser console for errors

