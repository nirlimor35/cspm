provider "aws" {
  region  = var.aws_region_for_lambda
}

data "aws_iam_policy" "AWSLambdaBasicExecutionRole" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

variable "aws_region_for_lambda" {
  type        = string
  description = "The region where the Lambda function will provision"
}
variable "platform" {
  type    = string
  default = "coralogix"
}
variable "coralogix_endpoint" {
  type = string
  validation {
    condition     = can(regex("^((EU|US)[12]|AP[123])$", var.coralogix_endpoint))
    error_message = "Coralogix endpoint can only be EU1, EU2, US1, US2, AP1, AP2, AP3"
  }
}
variable "coralogix_api_key" {
  type        = string
  sensitive   = true
  description = "Coralogix send-your-data key"
}
variable "aws_region_list" {
  type        = string
  default     = ""
  description = "Comma separated list of regions to scan (leave empty for all regions)"
}
variable "aws_services_list" {
  type        = string
  default     = ""
  description = "Comma separated list of services to scan (leave empty for all services)"
}
variable "cspm_run_frequency" {
  type        = number
  default     = 12
  description = "What is the interval the CSPM should run in hours"
}

resource "aws_lambda_function" "this" {
  function_name = "CSPM"
  role          = aws_iam_role.this.arn
  filename      = "../code/code.zip"
  runtime       = "python3.13"
  handler       = "cspm.lambda_handler"
  timeout       = 900
  memory_size   = 1024
  layers        = [aws_lambda_layer_version.this.arn]
  environment {
    variables = {
      LAMBDA         = true
      CLOUD_PROVIDER = "aws"
      PLATFORM       = var.platform
      CX_ENDPOINT    = var.coralogix_endpoint
      CX_API_KEY     = var.coralogix_api_key
      AWS_REGIONS    = var.aws_region_list
      AWS_SERVICES   = var.aws_services_list
    }
  }
}
resource "aws_lambda_layer_version" "this" {
  layer_name          = "cspm-python3-13"
  filename            = "../code/layer.zip"
  compatible_runtimes = ["python3.13"]
}
resource "aws_iam_role" "this" {
  name               = "CSPM-Role"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}
resource "aws_iam_policy" "policy" {
  name        = "cspm_policy"
  path        = "/"
  description = "CSPM Policy"
  policy      = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Sid    = "CSPM"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeLaunchConfigurations",
          "cloudtrail:ListTags",
          "cloudtrail:GetTrailStatus",
          "cloudtrail:GetEventSelectors",
          "cloudtrail:DescribeTrails",
          "ec2:DescribeAddresses",
          "ec2:DescribeInstances",
          "ec2:DescribeFlowLogs",
          "ec2:DescribeVpcEndpointServices",
          "ec2:DescribeLaunchTemplates",
          "ec2:DescribeVpcPeeringConnections",
          "ec2:DescribeLaunchTemplateVersions",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeVpcs",
          "ec2:DescribeVpcEndpoints",
          "ec2:DescribeRegions",
          "ecr:DescribeRepositories",
          "ecr:GetLifecyclePolicy",
          "ecr:GetRegistryScanningConfiguration",
          "ecr:GetAuthorizationToken",
          "guardduty:ListDetectors",
          "guardduty:GetDetector",
          "iam:GetAccountPasswordPolicy",
          "iam:ListAttachedUserPolicies",
          "iam:ListAccessKeys",
          "iam:ListRoleTags",
          "iam:ListMFADevices",
          "iam:GetAccessKeyLastUsed",
          "iam:ListRoles",
          "iam:ListUserPolicies",
          "iam:ListUsers",
          "iam:GetUser",
          "iam:GetLoginProfile",
          "s3:GetBucketPublicAccessBlock",
          "s3:GetBucketObjectLockConfiguration",
          "s3:GetEncryptionConfiguration",
          "s3:GetLifecycleConfiguration",
          "s3:ListAllMyBuckets",
          "s3:GetBucketVersioning",
          "s3:GetBucketNotification",
          "secretsmanager:ListSecrets",
          "sns:ListTagsForResource",
          "sns:ListTopics",
          "sns:GetTopicAttributes",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}
resource "aws_iam_policy_attachment" "this" {
  name       = "cspm-policy-to-role-attachment"
  policy_arn = aws_iam_policy.policy.arn

  roles = [aws_iam_role.this.name]
}
resource "aws_iam_policy_attachment" "AWSLambdaBasicExecutionRole" {
  roles      = [aws_iam_role.this.name]
  policy_arn = data.aws_iam_policy.AWSLambdaBasicExecutionRole.arn
  name       = data.aws_iam_policy.AWSLambdaBasicExecutionRole.name
}
resource "aws_lambda_permission" "eventbridge-lambda-invoke" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduler.arn
}
resource "aws_cloudwatch_event_rule" "scheduler" {
  name                = "lambda-updater-for-eks-shipping"
  schedule_expression = "rate(${var.cspm_run_frequency} hours)"
}
resource "aws_cloudwatch_event_target" "scheduler-target" {
  arn       = aws_lambda_function.this.arn
  rule      = aws_cloudwatch_event_rule.scheduler.name
  target_id = "lambda-eks-scheduler-target"
}
