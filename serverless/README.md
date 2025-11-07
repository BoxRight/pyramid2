# Serverless Implementation Guide

## Directory Structure

```
serverless/
├── lambda/
│   ├── compiler/
│   │   ├── handler.py
│   │   └── requirements.txt
│   ├── analyzer/
│   │   ├── handler.py
│   │   └── requirements.txt
│   ├── query/
│   │   ├── handler.py
│   │   └── requirements.txt
│   ├── generator/
│   │   ├── handler.py
│   │   └── requirements.txt
│   └── renderer/
│       ├── handler.py
│       └── requirements.txt
├── layers/
│   ├── python-deps/
│   │   └── requirements.txt
│   └── binaries/
│       └── lamlc
├── infrastructure/
│   ├── cdk/              # CDK implementation
│   │   └── app.py
│   └── sam/              # SAM template
│       └── template.yaml
├── scripts/
│   ├── migrate_sqlite_to_dynamodb.py
│   └── upload_to_s3.py
└── tests/
    └── test_lambda_handlers.py
```

## Key Implementation Considerations

### 1. Lambda Binary Execution
The `lamlc` binary needs special handling:
- **Option A**: Package in Lambda Layer (if < 50MB)
- **Option B**: Use EFS mount (if larger or needs filesystem)
- **Option C**: Use containerized Lambda (if complex dependencies)

### 2. SQLite to DynamoDB Migration
- SQLite is file-based and not suitable for Lambda
- DynamoDB requires schema redesign
- Consider DynamoDB Streams for real-time updates

### 3. State Management
- Lambda is stateless - use DynamoDB for state
- S3 for large files (AST JSON, vectors)
- Step Functions for workflow orchestration

### 4. Cold Start Optimization
- Use Lambda Layers for common dependencies
- Provisioned concurrency for critical paths
- Keep Lambda packages small

