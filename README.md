# Nemo AI ECS Infrastructure

AWS CDK project that deploys an AI agent on ECS Fargate with Bedrock integration.

## Architecture

- **ECS Fargate**: Containerized AI agent (512 CPU, 1GB memory)
- **AWS Bedrock**: AI model access and code interpreter
- **OpenTelemetry**: Observability and tracing
- **GitHub Actions**: Auto-deploy on main branch push

## Structure

```
├── infrastructure/ecs_fargate_stack.py  # CDK stack
├── cdk_app.py                          # CDK entry point
├── .github/workflows/deploy.yml        # CI/CD pipeline
└── otel_config.env                     # Observability config
```

## Quick Start

```bash
pip install -r requirements-dev.txt
npm install -g aws-cdk
export CDK_DEFAULT_ACCOUNT=your-account-id
cdk deploy
```

## Requirements

- ECR repository: `nemo-ai-agent`
- AWS Secrets Manager: GitHub token
- Python 3.12+, Node.js 22+