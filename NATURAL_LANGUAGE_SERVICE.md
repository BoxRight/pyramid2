# Natural Language to LAML Service - Architecture Extension

## ✅ Yes! Your Architecture Supports This

The serverless architecture is **perfectly designed** to add new services like natural language to LAML conversion. Here's how:

---

## 🎯 How It Fits In

### Current Architecture Flow:
```
User → API Gateway → Lambda Functions → DynamoDB/S3
```

### With Natural Language Service:
```
User (Natural Language) → API Gateway → NL-to-LAML Lambda → LAML → Compiler Lambda → Analysis
```

**Key Point**: The architecture is **modular** - you just add a new Lambda function!

---

## 🏗️ Architecture Extension

### New Component: Natural Language to LAML Service

```
┌─────────────────────────────────┐
│     Natural Language Service    │
│                                 │
│  1. Receives: "Create a solar   │
│     lease between SolarCorp     │
│     and HomeOwner for $200/mo"  │
│                                 │
│  2. Uses AI (Claude/Bedrock)    │
│     to understand intent         │
│                                 │
│  3. Generates LAML contract     │
│                                 │
│  4. Validates LAML structure     │
│                                 │
│  5. Returns LAML or triggers    │
│     compilation workflow         │
└─────────────────────────────────┘
```

---

## 📦 Implementation Options

### Option 1: New Lambda Function (Recommended)

**Function**: `nl-to-laml-generator`

**Responsibilities**:
- Accept natural language input
- Use AI to convert to LAML
- Validate generated LAML
- Return LAML or trigger compilation

**Integration Points**:
- Uses existing **Generator Lambda** as template
- Can call **Claude API** (you already use Anthropic)
- Can use **AWS Bedrock** (AWS's managed AI service)
- Outputs to same **S3 bucket**
- Can trigger existing **Compilation workflow**

### Option 2: Enhance Existing Generator Lambda

Add a new endpoint to your existing `contract-generator` Lambda:
- Existing: Template-based generation
- New: Natural language generation

---

## 🔧 Detailed Implementation

### 1. New API Endpoint

**Add to API Gateway**:
```
POST /contracts/generate-from-nl
```

**Request Body**:
```json
{
  "natural_language": "Create a solar lease contract between SolarCorp and HomeOwner. The monthly rent is $200. Include maintenance obligations and return conditions.",
  "contract_type": "solar_lease",
  "jurisdiction": "Mexico",
  "additional_context": {
    "parties": {
      "lessor": "SolarCorp",
      "lessee": "HomeOwner"
    },
    "terms": {
      "rent": "$200/month",
      "duration": "5 years"
    }
  }
}
```

**Response**:
```json
{
  "contract_id": "contract-123",
  "laml_content": "# Generated LAML contract...",
  "status": "generated",
  "validation_errors": [],
  "compilation_triggered": true
}
```

### 2. New Lambda Function Structure

**File**: `serverless/lambda/nl-to-laml/handler.py`

```python
"""
Natural Language to LAML Generator
Uses AI to convert natural language to LAML contracts
"""

import json
import boto3
from anthropic import Anthropic
from typing import Dict, Any

# Initialize AWS clients
s3 = boto3.client('s3')
sns = boto3.client('sns')

# Initialize Anthropic client (you already use this!)
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Convert natural language to LAML contract
    """
    try:
        # Extract request data
        natural_language = event.get('natural_language')
        contract_type = event.get('contract_type', 'generic')
        jurisdiction = event.get('jurisdiction', 'Mexico')
        
        # Step 1: Use AI to generate LAML
        laml_code = generate_laml_from_nl(
            natural_language, 
            contract_type, 
            jurisdiction,
            event.get('additional_context', {})
        )
        
        # Step 2: Validate LAML structure
        validation_result = validate_laml(laml_code)
        
        if not validation_result['valid']:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Generated LAML is invalid',
                    'validation_errors': validation_result['errors'],
                    'laml_preview': laml_code[:500]  # Preview
                })
            }
        
        # Step 3: Save to S3
        contract_id = save_laml_to_s3(laml_code, contract_type)
        
        # Step 4: Optionally trigger compilation
        if event.get('auto_compile', False):
            trigger_compilation(contract_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'contract_id': contract_id,
                'laml_content': laml_code,
                'status': 'generated',
                'validation_errors': [],
                'compilation_triggered': event.get('auto_compile', False)
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'type': type(e).__name__
            })
        }


def generate_laml_from_nl(
    natural_language: str,
    contract_type: str,
    jurisdiction: str,
    context: Dict[str, Any]
) -> str:
    """
    Use Claude API to generate LAML from natural language
    """
    
    # Load LAML templates and examples from S3
    templates = load_laml_templates(contract_type)
    examples = load_example_contracts(contract_type)
    
    # Build prompt for Claude
    prompt = build_laml_generation_prompt(
        natural_language,
        contract_type,
        jurisdiction,
        context,
        templates,
        examples
    )
    
    # Call Claude API
    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",  # Latest Claude model
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    # Extract LAML code from response
    laml_code = extract_laml_code(response.content[0].text)
    
    return laml_code


def build_laml_generation_prompt(
    nl_input: str,
    contract_type: str,
    jurisdiction: str,
    context: Dict,
    templates: str,
    examples: str
) -> str:
    """
    Build comprehensive prompt for Claude
    """
    return f"""You are a legal contract expert specializing in LAML (Legal Markup Language).

Your task is to convert natural language contract descriptions into valid LAML code.

INPUT:
Natural Language: "{nl_input}"
Contract Type: {contract_type}
Jurisdiction: {jurisdiction}
Additional Context: {json.dumps(context, indent=2)}

REFERENCE MATERIAL:
LAML Templates for {contract_type}:
{templates}

Example LAML Contracts:
{examples}

LAML SYNTAX RULES:
1. Use institution() to define contracts
2. Define parties with Person() types
3. Define objects with Thing() types
4. Use predicates for acts: act_name(party1, object, party2) = Person(...), Thing(...)
5. Use rules with implies for obligations: rule_name = condition implies oblig(action)
6. Import laws from ../laws/ directory
7. Import principles from ../principles/ directory
8. Use comments starting with # for documentation

REQUIREMENTS:
- Generate complete, valid LAML code
- Include all necessary imports
- Follow the structure of example contracts
- Include proper type bindings
- Add appropriate rules for obligations and claims
- Include metadata comments (@id, @derives, @priority)

OUTPUT:
Return ONLY the LAML code, no explanations or markdown formatting."""


def validate_laml(laml_code: str) -> Dict[str, Any]:
    """
    Validate LAML structure (basic validation)
    """
    errors = []
    
    # Check for required elements
    if 'institution(' not in laml_code:
        errors.append("Missing institution() definition")
    
    if 'Person(' not in laml_code:
        errors.append("Missing Person() type bindings")
    
    # Check for syntax issues
    if laml_code.count('(') != laml_code.count(')'):
        errors.append("Mismatched parentheses")
    
    if laml_code.count('{') != laml_code.count('}'):
        errors.append("Mismatched braces")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def save_laml_to_s3(laml_code: str, contract_type: str) -> str:
    """
    Save generated LAML to S3
    """
    import uuid
    from datetime import datetime
    
    contract_id = f"nl-generated-{uuid.uuid4().hex[:8]}"
    timestamp = datetime.utcnow().isoformat()
    
    s3_key = f"generated/nl/{contract_id}.laml"
    
    s3.put_object(
        Bucket=os.getenv('S3_BUCKET'),
        Key=s3_key,
        Body=laml_code.encode('utf-8'),
        ContentType='text/plain',
        Metadata={
            'contract_id': contract_id,
            'contract_type': contract_type,
            'generated_at': timestamp,
            'source': 'natural_language'
        }
    )
    
    return contract_id


def trigger_compilation(contract_id: str):
    """
    Trigger the existing compilation workflow
    """
    # You can use Step Functions, EventBridge, or directly call Compiler Lambda
    # This integrates with your existing architecture!
    pass
```

---

## 🔄 Integration with Existing Architecture

### Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│  User: "Create solar lease contract..."                │
└──────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  API Gateway: POST /contracts/generate-from-nl          │
└──────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  NL-to-LAML Lambda                                       │
│  - Receives natural language                             │
│  - Calls Claude API                                      │
│  - Generates LAML code                                   │
│  - Validates structure                                   │
└──────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  S3: Save generated LAML                                 │
│  Path: generated/nl/contract-123.laml                     │
└──────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  EventBridge: "Contract generated" event                 │
└──────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Step Functions: Trigger Compilation Workflow             │
│  (Your existing workflow!)                                │
└──────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Existing Compiler → Analyzer → Query Functions          │
│  (All your existing services work automatically!)        │
└─────────────────────────────────────────────────────────┘
```

---

## 🎨 AI Service Options

### Option 1: Anthropic Claude (You Already Use This!)

**Pros**:
- You're already using it (`ast_contract_parser.py`)
- Best for legal/complex reasoning
- High quality output

**Integration**:
```python
from anthropic import Anthropic

anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
response = anthropic.messages.create(...)
```

**Cost**: ~$3 per 1M input tokens, $15 per 1M output tokens

### Option 2: AWS Bedrock (Fully Managed)

**Pros**:
- Native AWS integration
- No API keys to manage
- Multiple models (Claude, Llama, etc.)
- Better cost for high volume

**Integration**:
```python
import boto3

bedrock = boto3.client('bedrock-runtime')
response = bedrock.invoke_model(
    modelId='anthropic.claude-3-5-sonnet-20241022',
    body=json.dumps({
        'messages': [...]
    })
)
```

**Cost**: Similar to direct API, but integrated billing

### Option 3: Hybrid Approach

**Strategy**:
- Use Bedrock for simple contracts (cost-effective)
- Use Claude API for complex contracts (better quality)
- Route based on contract complexity

---

## 📊 Updated SAM Template

Add this to your `template.yaml`:

```yaml
NLToLAMLFunction:
  Type: AWS::Serverless::Function
  Properties:
    FunctionName: !Sub '${Environment}-nl-to-laml'
    CodeUri: ../../lambda/nl-to-laml/
    Handler: handler.lambda_handler
    MemorySize: 512
    Timeout: 120
    Environment:
      Variables:
        ANTHROPIC_API_KEY: !Ref AnthropicApiKey  # From Secrets Manager
        S3_BUCKET: !Ref S3BucketName
    Policies:
      - S3WritePolicy:
          BucketName: !Ref S3BucketName
      - S3ReadPolicy:
          BucketName: !Ref S3BucketName
      - SecretsManagerReadPolicy:
          SecretArn: !Ref AnthropicApiKey
    Events:
      NLGenerateApi:
        Type: Api
        Properties:
          Path: /contracts/generate-from-nl
          Method: post
```

---

## 🎯 Benefits of This Approach

### 1. **Seamless Integration**
- Uses your existing infrastructure
- No changes to existing functions
- Leverages existing compilation workflow

### 2. **Scalable**
- Auto-scales with Lambda
- Handles concurrent requests
- Cost-effective (pay per request)

### 3. **Flexible**
- Can improve AI prompts over time
- Can add multiple AI models
- Can add validation layers

### 4. **Maintainable**
- Separate Lambda function (easy to update)
- Can A/B test different AI models
- Can version API endpoints

---

## 🚀 Implementation Steps

### Phase 1: Basic Implementation
1. Create `nl-to-laml` Lambda function
2. Add API Gateway endpoint
3. Integrate Claude API
4. Basic validation

### Phase 2: Enhancement
1. Add template system (load from S3)
2. Add example contracts (few-shot learning)
3. Improve prompts
4. Add better validation

### Phase 3: Integration
1. Connect to compilation workflow
2. Add error handling
3. Add monitoring
4. Add user feedback loop

### Phase 4: Optimization
1. Add caching for common requests
2. Optimize prompts (reduce tokens)
3. Add streaming for long contracts
4. Add batch processing

---

## 💡 Advanced Features You Can Add

### 1. **Interactive Generation**
- Multi-turn conversation
- "Add a clause about maintenance"
- "Change rent to $300"

### 2. **Template-Based Generation**
- User selects template
- AI fills in details
- More reliable output

### 3. **Validation & Suggestions**
- AI suggests improvements
- Legal compliance checking
- Best practice recommendations

### 4. **Multi-Language Support**
- Input in Spanish, output LAML
- Translate existing contracts

---

## 📈 Cost Considerations

### Natural Language Generation Costs

**Per Request**:
- Claude API: ~$0.01-0.05 per contract (depending on length)
- Lambda: $0.0000002 per request
- S3: $0.000005 per file
- **Total**: ~$0.01-0.05 per contract

**Monthly (1000 contracts)**:
- AI API: $10-50
- Lambda: $0.0002
- S3: $0.005
- **Total**: ~$10-50/month

**Cost Optimization**:
- Cache common contract types
- Use simpler models for simple contracts
- Batch similar requests

---

## ✅ Answer: YES, It's Perfect!

Your architecture is **designed exactly for this**:

1. ✅ **Modular**: Add new Lambda function
2. ✅ **Integrated**: Uses existing services
3. ✅ **Scalable**: Auto-scales with demand
4. ✅ **Cost-effective**: Pay per use
5. ✅ **Maintainable**: Separate, testable component

The natural language service would be a **perfect addition** that leverages your existing infrastructure!

---

## 🎓 Next Steps

1. **Start Simple**: Create basic NL-to-LAML Lambda
2. **Test with Claude**: Use your existing Anthropic setup
3. **Integrate**: Connect to compilation workflow
4. **Iterate**: Improve prompts and validation

Would you like me to:
1. Create the complete Lambda function code?
2. Show how to integrate with your existing compilation workflow?
3. Design the API request/response format?
4. Create a prompt engineering guide for best results?

