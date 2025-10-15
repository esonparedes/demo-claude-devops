# AWS Infrastructure with Terraform

This directory contains Terraform infrastructure-as-code for deploying the demo-claude-devops Python application to AWS using ECS Fargate.

## Architecture Overview

The infrastructure includes:

- **VPC**: Custom VPC with public and private subnets across 2 availability zones
- **ECR**: Elastic Container Registry for storing Docker images
- **ECS Fargate**: Serverless container orchestration
- **Application Load Balancer**: Distributes traffic across ECS tasks
- **Auto Scaling**: CPU and memory-based auto-scaling policies
- **CloudWatch**: Centralized logging and monitoring
- **IAM**: Least-privilege roles for ECS tasks and GitHub Actions

## Directory Structure

```
terraform/
├── main.tf                  # Main Terraform configuration
├── variables.tf             # Input variables
├── outputs.tf               # Output values
├── terraform.tfvars.example # Example variable values
├── .gitignore              # Git ignore rules
└── modules/
    ├── vpc/                # VPC, subnets, NAT gateways
    ├── ecr/                # Container registry
    ├── iam/                # IAM roles and policies
    ├── alb/                # Application Load Balancer
    └── ecs/                # ECS cluster, service, tasks
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** >= 1.5.0 installed
3. **AWS CLI** configured with credentials
4. **GitHub OIDC Provider** (optional, for secure deployments)

## Quick Start

### 1. Configure Variables

Copy the example file and customize:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
aws_region   = "us-east-1"
project_name = "demo-claude-devops"
environment  = "staging"
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review the Plan

```bash
terraform plan
```

### 4. Apply the Infrastructure

```bash
terraform apply
```

Review the proposed changes and type `yes` to confirm.

### 5. Get Outputs

After successful deployment:

```bash
terraform output
```

Key outputs:
- `application_url`: URL to access your application
- `ecr_repository_url`: Docker image repository URL
- `ecs_cluster_name`: ECS cluster name

## Remote State Configuration (Production)

For production environments, use remote state with S3 backend:

1. Create an S3 bucket for state storage:

```bash
aws s3 mb s3://your-terraform-state-bucket
```

2. Create a DynamoDB table for state locking:

```bash
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

3. Uncomment and configure the backend in `main.tf`:

```hcl
backend "s3" {
  bucket         = "your-terraform-state-bucket"
  key            = "demo-claude-devops/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-state-lock"
}
```

4. Re-initialize Terraform:

```bash
terraform init -migrate-state
```

## GitHub OIDC Setup (Recommended)

For secure deployments without long-lived AWS credentials:

1. Create GitHub OIDC provider in AWS (one-time setup):

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

2. The Terraform IAM module creates a GitHub Actions role automatically

3. Update your GitHub Actions workflow to use OIDC:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::ACCOUNT_ID:role/demo-claude-devops-staging-github-actions-role
    aws-region: us-east-1
```

## Modules

### VPC Module

Creates network infrastructure:
- VPC with DNS support
- Public subnets for ALB
- Private subnets for ECS tasks
- NAT gateways for outbound internet access
- Route tables and associations
- VPC Flow Logs

### ECR Module

Container registry with:
- Image scanning on push
- Encryption at rest (AES256)
- Lifecycle policies (keep last 10 tagged images)
- Repository policies for ECS access

### IAM Module

Least-privilege IAM roles:
- **ECS Task Execution Role**: Pull images, write logs
- **ECS Task Role**: Application-level AWS permissions
- **GitHub Actions Role**: Deploy to ECS, push to ECR

### ALB Module

Application Load Balancer with:
- HTTP listener (port 80)
- Target group with health checks
- Security groups
- CloudWatch logging

### ECS Module

Container orchestration:
- Fargate cluster with Container Insights
- Service with deployment circuit breaker
- Task definition with health checks
- Auto-scaling policies (CPU and memory)
- CloudWatch log groups

## Variables

Key variables (see `variables.tf` for full list):

| Variable | Description | Default |
|----------|-------------|---------|
| `aws_region` | AWS region | `us-east-1` |
| `project_name` | Project name | `demo-claude-devops` |
| `environment` | Environment (staging/production) | Required |
| `desired_count` | Number of ECS tasks | `2` |
| `cpu` | CPU units per task | `256` |
| `memory` | Memory per task (MB) | `512` |
| `image_tag` | Docker image tag | `latest` |

## Outputs

Key outputs:

- `application_url`: Load balancer URL
- `ecr_repository_url`: ECR repository URL
- `ecs_cluster_name`: ECS cluster name
- `ecs_service_name`: ECS service name

## Multi-Environment Setup

Deploy separate environments using Terraform workspaces:

```bash
# Create staging workspace
terraform workspace new staging
terraform apply -var-file=staging.tfvars

# Create production workspace
terraform workspace new production
terraform apply -var-file=production.tfvars

# List workspaces
terraform workspace list

# Switch workspaces
terraform workspace select staging
```

## Best Practices

1. **Remote State**: Always use remote state for team collaboration
2. **State Locking**: Enable DynamoDB state locking
3. **Variables**: Never commit `.tfvars` files with secrets
4. **Modules**: Keep modules focused and reusable
5. **Versioning**: Pin Terraform and provider versions
6. **Validation**: Use `terraform validate` and `terraform plan`
7. **Documentation**: Update this README when making changes

## Terraform Commands

```bash
# Format code
terraform fmt -recursive

# Validate configuration
terraform validate

# Plan changes
terraform plan

# Apply changes
terraform apply

# Show current state
terraform show

# List resources
terraform state list

# Destroy infrastructure
terraform destroy
```

## Troubleshooting

### Issue: "Error creating ECR repository: RepositoryAlreadyExistsException"

**Solution**: The repository already exists. Import it:

```bash
terraform import module.ecr.aws_ecr_repository.app demo-claude-devops-staging
```

### Issue: "Error: Provider configuration not found"

**Solution**: Re-initialize Terraform:

```bash
terraform init
```

### Issue: "Error: timeout while waiting for state to become 'available'"

**Solution**: Check AWS service limits or increase timeout:

```hcl
resource "aws_ecs_service" "app" {
  # ...
  wait_for_steady_state = true

  timeouts {
    create = "15m"
    update = "15m"
  }
}
```

## Security Considerations

1. **Encryption**: All data encrypted at rest and in transit
2. **Network Isolation**: ECS tasks in private subnets
3. **IAM Policies**: Least-privilege access
4. **Security Groups**: Restricted ingress/egress rules
5. **Image Scanning**: ECR scans images for vulnerabilities
6. **Secrets Management**: Use AWS Secrets Manager for sensitive data

## Cost Estimation

Approximate monthly costs (us-east-1):

- VPC: $0 (free tier)
- NAT Gateways: ~$65/month (2 AZs)
- ALB: ~$20/month
- ECS Fargate: ~$15/month (2 tasks, 0.25 vCPU, 0.5 GB)
- ECR: ~$1/month (< 10 GB)
- CloudWatch Logs: ~$5/month

**Total**: ~$106/month

Reduce costs by:
- Using a single NAT Gateway
- Reducing desired task count
- Using smaller task sizes
- Enabling log retention policies

## Additional Resources

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
