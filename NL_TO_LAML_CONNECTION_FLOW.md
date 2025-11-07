# Natural Language to LAML Connection Flow

## `/contracts/generate-from-nl` Endpoint Flow

```
Frontend
  ↓ POST /contracts/generate-from-nl
Backend (main.py)
  ↓ generate_laml_from_natural_language()
Service (nl_to_laml.py)
  ↓
Anthropic Claude API (External)
  ↓
Returns LAML code
```

## Connection Details

### 1. **Endpoint** (`backend/main.py`)
```python
@app.post("/contracts/generate-from-nl")
async def generate_from_natural_language(request: GenerateNLRequest):
    result = await generate_laml_from_natural_language(...)
```

### 2. **Service** (`backend/services/nl_to_laml.py`)
```python
async def generate_laml_from_natural_language(...):
    # Initialize Anthropic client
    api_key = os.getenv('ANTHROPIC_API_KEY')
    anthropic = Anthropic(api_key=api_key)
    
    # Call Claude API
    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
```

### 3. **External API**: Anthropic Claude API

**Connection**: HTTPS to `api.anthropic.com`
- **Service**: Anthropic Claude AI
- **Model**: `claude-3-5-sonnet-20240620`
- **Authentication**: API Key from `ANTHROPIC_API_KEY` environment variable
- **Location**: External cloud service (not local)

## Requirements

### Environment Variable
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

**Location**: `.env` file in project root

### API Key Setup
1. Get API key from: https://console.anthropic.com/
2. Add to `.env` file:
   ```env
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

## What It Does

1. **Loads Examples**: Reads example contracts from `contracts/solar_lease_simple.laml`
2. **Builds Prompt**: Creates a comprehensive prompt with:
   - Natural language input
   - Contract type and jurisdiction
   - Example LAML contracts
   - LAML syntax rules
3. **Calls Claude API**: Sends prompt to Anthropic's Claude AI
4. **Extracts LAML**: Parses Claude's response to extract LAML code
5. **Validates**: Basic validation (checks for required elements)
6. **Returns**: Generated LAML code with contract ID

## Error Handling

If `ANTHROPIC_API_KEY` is missing:
```python
raise ValueError("ANTHROPIC_API_KEY environment variable is required")
```

If Claude API fails:
```python
raise Exception(f"Failed to generate LAML: {str(e)}")
```

## Serverless Mapping

**Current (Local)**:
- Direct HTTP call to Anthropic API
- API key from `.env` file

**Future (Lambda)**:
- Same HTTP call to Anthropic API
- API key from AWS Secrets Manager or environment variables
- Could use AWS Bedrock (Claude via AWS) for cost optimization

## Summary

**`/contracts/generate-from-nl` connects to**:
- ✅ **External API**: Anthropic Claude AI (`api.anthropic.com`)
- ✅ **Requires**: `ANTHROPIC_API_KEY` environment variable
- ✅ **Model**: Claude 3.5 Sonnet
- ✅ **Purpose**: Converts natural language → LAML code

**NOT connected to**:
- ❌ Local services
- ❌ Database
- ❌ Other internal APIs

It's a direct external API call to Anthropic's Claude AI service.

