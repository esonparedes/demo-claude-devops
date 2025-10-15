# AWS Deployment Guide

This guide walks you through deploying the demo-claude-devops Python application to AWS using Terraform and GitHub Actions.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS Account Setup](#aws-account-setup)
3. [GitHub Secrets Configuration](#github-secrets-configuration)
4. [Infrastructure Deployment](#infrastructure-deployment)
5. [Application Deployment](#application-deployment)
6. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
7. [Rollback Procedures](#rollback-procedures)

## Prerequisites

Before you begin, ensure you have:

- AWS Account with billing enabled
- GitHub repository with admin access
- AWS CLI installed and configured
- Terraform >= 1.5.0 installed locally
- Docker installed locally (for testing)

## AWS Account Setup

### 1. Create IAM User for GitHub Actions

Create an IAM user with programmatic access:

```bash
aws iam create-user --user-name github-actions-deploy
```

### 2. Create IAM Policy

Create a policy file `github-actions-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:RegisterTaskDefinition",
        "ecs:DescribeTasks",
        "ecs:ListTasks"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": [
        "arn:aws:iam::*:role/*-ecs-task-execution-role",
        "arn:aws:iam::*:role/*-ecs-task-role"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:DescribeTargetHealth"
      ],
      "Resource": "*"
    }
  ]
}
```

Attach the policy:

```bash
aws iam create-policy \
  --policy-name GitHubActionsECSDeploy \
  --policy-document file://github-actions-policy.json

aws iam attach-user-policy \
  --user-name github-actions-deploy \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/GitHubActionsECSDeploy
```

### 3. Create Access Keys

```bash
aws iam create-access-key --user-name github-actions-deploy
```

Save the `AccessKeyId` and `SecretAccessKey` - you'll need these for GitHub Secrets.

### 4. (Optional) Set Up GitHub OIDC Provider

For more secure authentication without long-lived credentials:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

## GitHub Secrets Configuration

Add the following secrets to your GitHub repository:

### Navigate to Repository Settings

1. Go to your GitHub repository
2. Click **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**

### Required Secrets

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ACCESS_KEY_ID` | From step above | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | From step above | AWS secret key |
| `AWS_REGION` | `us-east-1` | AWS region |

### Verify Secrets

Run this test workflow to verify credentials:

```yaml
name: Test AWS Credentials
on: workflow_dispatch

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION || 'us-east-1' }}

      - name: Test AWS CLI
        run: aws sts get-caller-identity
```

## Infrastructure Deployment

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Create Variable Files

Create `staging.tfvars`:

```hcl
aws_region   = "us-east-1"
project_name = "demo-claude-devops"
environment  = "staging"

# Network configuration
vpc_cidr             = "10.0.0.0/16"
availability_zones   = ["us-east-1a", "us-east-1b"]
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]

# ECS configuration
container_port = 8000
desired_count  = 2
cpu            = "256"
memory         = "512"

# Health check
health_check_path    = "/health"
health_check_matcher = "200"

image_tag = "v1.0.0"
```

Create `production.tfvars` with production values.

### 3. Deploy Staging Infrastructure

```bash
terraform workspace new staging
terraform apply -var-file=staging.tfvars
```

Review the plan and type `yes` to confirm.

### 4. Deploy Production Infrastructure

```bash
terraform workspace new production
terraform apply -var-file=production.tfvars
```

### 5. Save Terraform Outputs

```bash
# Staging
terraform workspace select staging
terraform output -json > staging-outputs.json

# Production
terraform workspace select production
terraform output -json > production-outputs.json
```

Key outputs:
- `ecr_repository_url`: Use this in GitHub Actions
- `application_url`: Your app's URL
- `ecs_cluster_name`: ECS cluster name
- `ecs_service_name`: ECS service name

## Application Deployment

### 1. Build and Test Locally

```bash
# Build Docker image
docker build -t demo-claude-devops:test .

# Test the image
docker run -p 8000:8000 demo-claude-devops:test

# Verify health
curl http://localhost:8000/health
```

### 2. Manual Deployment (First Time)

For the first deployment, push an initial image:

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag demo-claude-devops:test \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/demo-claude-devops-staging:v1.0.0

# Push image
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/demo-claude-devops-staging:v1.0.0
```

### 3. Trigger GitHub Actions Deployment

#### Option A: Automatic Deployment (on push to main)

```bash
git add .
git commit -m "feat: initial AWS deployment setup"
git push origin main
```

The workflow will automatically:
1. Build and push Docker image to ECR
2. Deploy to staging
3. Run health checks and smoke tests

#### Option B: Manual Deployment (workflow_dispatch)

1. Go to **Actions** tab in GitHub
2. Select **Deploy to AWS ECS** workflow
3. Click **Run workflow**
4. Select:
   - **Environment**: staging or production
   - **Image tag**: v1.0.0 (or your tag)
5. Click **Run workflow**

### 4. Verify Deployment

Check the deployment status:

```bash
# Check ECS service
aws ecs describe-services \
  --cluster demo-claude-devops-staging-cluster \
  --services demo-claude-devops-staging-service

# Check tasks
aws ecs list-tasks \
  --cluster demo-claude-devops-staging-cluster \
  --service-name demo-claude-devops-staging-service

# Get ALB URL
ALB_DNS=$(terraform output -raw application_url)
echo "Application URL: $ALB_DNS"

# Test health endpoint
curl $ALB_DNS/health
```

## Monitoring and Troubleshooting

### CloudWatch Logs

View application logs:

```bash
# List log streams
aws logs describe-log-streams \
  --log-group-name /ecs/demo-claude-devops-staging \
  --order-by LastEventTime \
  --descending

# Tail logs
aws logs tail /ecs/demo-claude-devops-staging --follow
```

### ECS Service Events

```bash
aws ecs describe-services \
  --cluster demo-claude-devops-staging-cluster \
  --services demo-claude-devops-staging-service \
  --query 'services[0].events[0:10]'
```

### Common Issues

#### Issue: Tasks failing to start

Check task logs:

```bash
# Get task ARN
TASK_ARN=$(aws ecs list-tasks \
  --cluster demo-claude-devops-staging-cluster \
  --service-name demo-claude-devops-staging-service \
  --query 'taskArns[0]' --output text)

# Describe task
aws ecs describe-tasks \
  --cluster demo-claude-devops-staging-cluster \
  --tasks $TASK_ARN
```

#### Issue: Health checks failing

Check target health:

```bash
aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw alb_target_group_arn)
```

#### Issue: Cannot pull image from ECR

Verify IAM permissions:

```bash
aws ecr describe-repositories --repository-names demo-claude-devops-staging
```

### Monitoring Dashboard

Access CloudWatch dashboards:

1. Go to AWS Console > CloudWatch
2. Navigate to Dashboards
3. View ECS metrics:
   - CPU Utilization
   - Memory Utilization
   - Task Count
   - ALB Request Count

## Rollback Procedures

### Method 1: Rollback via GitHub Actions

1. Go to **Actions** tab
2. Run **Deploy to AWS ECS** workflow
3. Select previous image tag

### Method 2: Manual Rollback

```bash
# List previous task definitions
aws ecs list-task-definitions \
  --family-prefix demo-claude-devops-staging \
  --sort DESC

# Update service with previous task definition
aws ecs update-service \
  --cluster demo-claude-devops-staging-cluster \
  --service demo-claude-devops-staging-service \
  --task-definition demo-claude-devops-staging:PREVIOUS_REVISION
```

### Method 3: Terraform Rollback

```bash
cd terraform
terraform workspace select staging

# Revert to previous image tag
terraform apply -var="image_tag=v1.0.0" -var-file=staging.tfvars
```

## Production Deployment Checklist

Before deploying to production:

- [ ] All tests passing in staging
- [ ] Security scan completed (no CRITICAL issues)
- [ ] Performance testing completed
- [ ] Rollback plan documented
- [ ] Team notified of deployment
- [ ] Image tag is immutable (not `latest`)
- [ ] Health checks configured and passing
- [ ] Monitoring alerts configured
- [ ] Backup taken (if applicable)
- [ ] Change request approved

## Deployment Best Practices

1. **Blue-Green Deployments**: Use ECS deployment strategies
2. **Canary Releases**: Deploy to subset of tasks first
3. **Auto-Rollback**: Enable circuit breaker in ECS
4. **Image Tags**: Use semantic versioning (v1.0.0), never `latest`
5. **Secrets**: Use AWS Secrets Manager, not environment variables
6. **Monitoring**: Set up CloudWatch alarms for errors and latency
7. **Backups**: Regular snapshots of critical data
8. **Documentation**: Keep this guide updated

## Cost Optimization

Reduce AWS costs:

1. **Right-size tasks**: Start small (256 CPU, 512 MB)
2. **Auto-scaling**: Scale down during off-hours
3. **Reserved instances**: For predictable workloads
4. **NAT Gateway**: Use single NAT for non-production
5. **Log retention**: Set to 7 days for staging
6. **ECR lifecycle**: Clean up old images

## Additional Resources

- [ECS Deployment Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [GitHub Actions for AWS](https://github.com/aws-actions)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

## Support

For issues:
1. Check CloudWatch logs
2. Review ECS service events
3. Verify IAM permissions
4. Check GitHub Actions workflow logs
5. Contact DevOps team
