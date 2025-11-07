# LAML Contracts Frontend

React-based frontend for the LAML Legal Contract Analysis System.

## Features

- **Natural Language Input**: Convert natural language descriptions to LAML contracts using Claude API
- **LAML Code Editor**: View and edit LAML code with syntax highlighting
- **Contract Analysis**: View violation and fulfillment analysis results
- **Query Interface**: Query contracts for specific predicates and consequences
- **Contract Management**: Browse and manage multiple contracts

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

The production build will be in the `dist` directory.

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

For production, set this to your API Gateway URL.

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── Sidebar.jsx
│   │   ├── NaturalLanguageInput.jsx
│   │   ├── LAMLViewer.jsx
│   │   ├── ContractAnalysis.jsx
│   │   ├── QueryInterface.jsx
│   │   └── ContractList.jsx
│   ├── services/            # API services
│   │   └── api.js
│   ├── App.jsx              # Main app component
│   ├── main.jsx             # Entry point
│   └── index.css            # Global styles
├── index.html
├── package.json
└── vite.config.js
```

## Design

The UI follows a VS Code-like dark theme inspired by the existing HTML files:
- Dark background (#1e1e1e)
- Sidebar navigation (#252526)
- Code editor with syntax highlighting
- Clean, modern interface

## API Integration

The frontend expects the following API endpoints:

- `POST /contracts/generate-from-nl` - Generate LAML from natural language
- `POST /contracts/compile` - Compile LAML contract
- `GET /contracts/{id}/analysis` - Get analysis results
- `POST /contracts/query` - Query contract predicates
- `GET /contracts/{id}/html` - Get rendered HTML contract
- `GET /contracts` - List all contracts

See `src/services/api.js` for implementation details.

