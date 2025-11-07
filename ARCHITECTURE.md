# AWS Serverless Architecture for LAML Legal Contract System

## Overview
This document outlines the serverless architecture for deploying the LAML legal contract analysis system as an MCP service on AWS.

## Architecture Components

### 1. API Layer (MCP Interface)
**API Gateway (REST/HTTP API)**
- **Purpose**: MCP protocol endpoint, HTTP API for web clients
- **Features**:
  - RESTful endpoints for contract operations
  - WebSocket support for streaming analysis results
  - Request validation and rate limiting
  - API key management for legal office clients

**Endpoints**:
- `POST /contracts/compile` - Compile LAML contract
- `GET /contracts/{id}/analysis` - Get violation/fulfillment analysis
- `POST /contracts/query` - Execute legal queries
- `POST /contracts/generate` - Generate contract from template
- `GET /contracts/{id}/html` - Get rendered contract HTML

### 2. Compute Layer (Lambda Functions)

#### 2.1 Contract Compilation Service
**Lambda Function**: `laml-compiler`
- **Runtime**: Python 3.12 (or Custom Runtime with compiled `lamlc` binary)
- **Memory**: 512MB-1024MB (for binary execution)
- **Timeout**: 5 minutes
- **Trigger**: API Gateway POST /contracts/compile
- **Responsibilities**:
  - Download LAML source files from S3
  - Execute `lamlc` binary (via Lambda Layer or EFS)
  - Upload AST JSON results to S3
  - Trigger async analysis workflow

**Dependencies**:
- S3: Read contracts/laws/principles
- S3: Write compilation results
- EventBridge: Emit compilation events

#### 2.2 Analysis Service
**Lambda Function**: `laml-analyzer`
- **Runtime**: Python 3.12
- **Memory**: 1024MB (for large JSON processing)
- **Timeout**: 15 minutes
- **Trigger**: EventBridge (after compilation) or API Gateway
- **Responsibilities**:
  - Parse AST JSON files
  - Convert to SQL (DynamoDB operations)
  - Perform violation/fulfillment analysis
  - Store analysis results

**Dependencies**:
- S3: Read AST JSON
- DynamoDB: Store predicates, solutions, contracts
- S3: Write analysis results

#### 2.3 Query Service
**Lambda Function**: `laml-query`
- **Runtime**: Python 3.12
- **Memory**: 512MB
- **Timeout**: 30 seconds
- **Trigger**: API Gateway POST /contracts/query
- **Responsibilities**:
  - Execute violation queries
  - Execute fulfillment queries
  - Perform team semantics analysis
  - Return formatted results

**Dependencies**:
- DynamoDB: Query predicates and solutions
- S3: Read vector files if needed

#### 2.4 Contract Generation Service
**Lambda Function**: `contract-generator`
- **Runtime**: Python 3.12
- **Memory**: 512MB
- **Timeout**: 2 minutes
- **Trigger**: API Gateway POST /contracts/generate
- **Responsibilities**:
  - Generate LAML from templates
  - Validate contract structure
  - Return generated LAML or trigger compilation

**Dependencies**:
- S3: Read templates
- Bedrock/Claude API: AI-assisted generation (optional)

#### 2.5 HTML Renderer Service
**Lambda Function**: `contract-renderer`
- **Runtime**: Python 3.12
- **Memory**: 512MB
- **Timeout**: 30 seconds
- **Trigger**: API Gateway GET /contracts/{id}/html
- **Responsibilities**:
  - Parse contract AST
  - Generate Mexican-style HTML contract
  - Return HTML or upload to S3

**Dependencies**:
- DynamoDB: Read contract metadata
- S3: Read AST JSON
- S3: Write HTML output

### 3. Data Storage Layer

#### 3.1 S3 Buckets
**Structure**:
```
laml-contracts-service/
├── source/
│   ├── contracts/          # User-uploaded contracts
│   ├── laws/               # Legal framework files
│   └── principles/         # Legal principles
├── compiled/
│   ├── ast/                # AST JSON results
│   └── vectors/            # Solution vectors
├── analysis/
│   └── results/            # Analysis JSON results
├── generated/
│   ├── html/               # Rendered contracts
│   └── laml/               # Generated LAML
└── templates/
    └── contract-templates/ # Contract templates
```

**Bucket Policies**:
- Encryption: SSE-S3 or SSE-KMS
- Versioning: Enabled for contracts
- Lifecycle: Archive old analysis results to Glacier

#### 3.2 DynamoDB Tables

**Table: `Contracts`**
- **PK**: `contract_id` (String)
- **GSI**: `contract_name` (String)
- **Attributes**:
  - `satisfiable` (Boolean)
  - `num_solutions` (Number)
  - `created_at` (String)
  - `compiled_at` (String)
  - `s3_ast_path` (String)
  - `status` (String: pending|compiling|ready|error)

**Table: `Predicates`**
- **PK**: `contract_id` (String)
- **SK**: `predicate_id` (String)
- **GSI**: `predicate_name` (String)
- **Attributes**:
  - `predicate_name` (String)
  - `predicate_type` (String: act|fact|claim|obligation|prohibition)
  - `arg1`, `arg2`, `arg3` (String)
  - `full_expression` (String)

**Table: `Solutions`**
- **PK**: `contract_id` (String)
- **SK**: `solution_id` (String)
- **GSI**: `solution_vector` (String, comma-separated predicate IDs)
- **Attributes**:
  - `predicate_ids` (List of Strings)
  - `solution_index` (Number)

**Table: `AnalysisResults`**
- **PK**: `contract_id` (String)
- **SK**: `analysis_type#predicate_name` (String)
- **Attributes**:
  - `analysis_type` (String: violation|fulfillment)
  - `predicate_name` (String)
  - `total_scenarios` (Number)
  - `consequences` (List of Maps)
  - `created_at` (String)

**Table: `ContractDependencies`**
- **PK**: `source_contract_id` (String)
- **SK**: `target_contract_id` (String)
- **Attributes**:
  - `dependency_type` (String)
  - `import_path` (String)

### 4. Workflow Orchestration

#### Step Functions State Machine
**Name**: `ContractProcessingWorkflow`

**States**:
1. **CompileContract**
   - Invoke `laml-compiler` Lambda
   - Wait for compilation completion
   - Handle errors

2. **StoreAST**
   - Upload AST JSON to S3
   - Store metadata in DynamoDB

3. **ConvertToSQL**
   - Invoke `laml-analyzer` Lambda
   - Convert JSON to DynamoDB entries

4. **RunAnalysis**
   - Run violation analysis
   - Run fulfillment analysis
   - Store results

5. **GenerateHTML** (Optional)
   - Invoke `contract-renderer` Lambda
   - Upload HTML to S3

6. **NotifyCompletion**
   - Send SNS notification
   - Update contract status

### 5. Event-Driven Architecture

#### EventBridge Rules
- **Contract Compiled**: Trigger analysis workflow
- **Analysis Complete**: Trigger notification
- **Error Occurred**: Trigger error handling Lambda

#### SQS Queues
- **High Priority Queue**: Real-time analysis requests
- **Batch Queue**: Background processing
- **DLQ**: Failed messages for investigation

#### SNS Topics
- **ContractStatus**: Notifications for contract state changes
- **AnalysisComplete**: Notify when analysis is ready

### 6. Supporting Services

#### Lambda Layers
- **Python Dependencies Layer**: 
  - `anthropic` (for Claude API)
  - `boto3` (AWS SDK)
  - Other Python dependencies

- **Binary Layer** (if needed):
  - `lamlc` compiled binary
  - `tree_fold_cpp` binary

#### EFS (Elastic File System) - Alternative Approach
- **Use Case**: If `lamlc` binary is too large or needs filesystem
- **Mount**: Attach to Lambda functions
- **Storage**: Store compiled binaries and temporary files

#### CloudWatch
- **Logs**: Lambda execution logs
- **Metrics**: 
  - Compilation duration
  - Analysis query latency
  - Error rates
  - Contract processing throughput
- **Alarms**: Error rate thresholds

### 7. Security & Access Control

#### IAM Roles
- **Lambda Execution Roles**: Minimal permissions per function
- **API Gateway**: Invoke Lambda permissions
- **S3 Access**: Read/write specific prefixes
- **DynamoDB Access**: Read/write specific tables

#### Cognito (Optional)
- **User Authentication**: For legal office users
- **API Authorization**: API Gateway integration

#### Secrets Manager
- **API Keys**: External service keys (Claude API, etc.)
- **Database Credentials**: If using RDS (not recommended for serverless)

### 8. Cost Optimization Strategies

#### 1. Lambda Configuration
- **Provisioned Concurrency**: Only for critical paths
- **Reserved Concurrency**: Limit for expensive operations
- **Memory Tuning**: Right-size based on actual usage

#### 2. DynamoDB
- **On-Demand**: For unpredictable workloads
- **DynamoDB Streams**: For real-time updates (if needed)
- **DAX**: For frequently accessed queries (optional)

#### 3. S3
- **Intelligent Tiering**: Automatic cost optimization
- **Lifecycle Policies**: Archive old data
- **Compression**: Compress JSON files

#### 4. Caching
- **API Gateway Caching**: Cache analysis results
- **ElastiCache** (optional): For frequently accessed data

### 9. Deployment Architecture

#### Infrastructure as Code
- **AWS CDK** or **Terraform**: Define all resources
- **SAM (Serverless Application Model)**: For Lambda-centric deployment

#### CI/CD Pipeline
- **CodeCommit/GitHub**: Source control
- **CodeBuild**: Build Lambda packages
- **CodePipeline**: Deploy to environments
- **Environments**: Dev → Staging → Production

### 10. Monitoring & Observability

#### X-Ray
- **Distributed Tracing**: Track requests across services
- **Service Map**: Visualize architecture

#### CloudWatch Dashboards
- **Contract Processing Metrics**
- **API Performance**
- **Error Rates**
- **Cost Tracking**

### 11. Scalability Considerations

#### Horizontal Scaling
- **Lambda**: Auto-scales to 1000 concurrent executions
- **DynamoDB**: Auto-scales with On-Demand mode
- **API Gateway**: Handles millions of requests

#### Vertical Scaling
- **Lambda Memory**: Adjust based on workload
- **DynamoDB**: RCU/WCU capacity

#### Performance Optimization
- **Parallel Processing**: Use Step Functions Map state
- **Batch Operations**: Process multiple contracts
- **Async Processing**: Non-blocking workflows

### 12. Migration Strategy

#### Phase 1: File Storage
- Migrate contracts/laws/principles to S3
- Update file paths in code

#### Phase 2: Database Migration
- Convert SQLite → DynamoDB
- Create migration scripts

#### Phase 3: Lambda Functions
- Port Python scripts to Lambda
- Create Lambda Layers for dependencies

#### Phase 4: API Integration
- Deploy API Gateway
- Integrate MCP protocol

#### Phase 5: Workflow Automation
- Implement Step Functions
- Add event-driven processing

## Estimated Costs (Monthly)

### Development Environment
- Lambda: ~$10-20 (low usage)
- DynamoDB: ~$5-10 (On-Demand)
- S3: ~$2-5 (storage)
- API Gateway: ~$1-3 (free tier)
- **Total**: ~$20-40/month

### Production (Medium Load)
- Lambda: ~$50-100 (100K requests)
- DynamoDB: ~$30-50 (On-Demand)
- S3: ~$10-20 (storage + requests)
- API Gateway: ~$10-20 (1M requests)
- Step Functions: ~$5-10
- **Total**: ~$100-200/month

### Production (High Load)
- Lambda: ~$200-500 (1M+ requests)
- DynamoDB: ~$100-200 (On-Demand)
- S3: ~$50-100
- API Gateway: ~$50-100
- Step Functions: ~$20-50
- **Total**: ~$400-900/month

## Next Steps

1. **Create Lambda Layer** for Python dependencies
2. **Set up S3 bucket structure** and migrate files
3. **Create DynamoDB tables** with proper schemas
4. **Port Python scripts** to Lambda functions
5. **Create API Gateway** with MCP endpoints
6. **Implement Step Functions** workflow
7. **Set up monitoring** and alerting
8. **Create deployment pipeline**

