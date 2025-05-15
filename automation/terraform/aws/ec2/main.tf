provider "aws" {
  region  = var.aws_region
  profile = "external-test"
}

variable "aws_region" {
  type        = string
  description = "For more information visit https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html"
}
variable "instance_type" {
  type        = string
  description = "Instance type in AWS - for more information visit https://aws.amazon.com/ec2/instance-types/"
}
variable "local-ssh-key-path" {
  type        = string
  description = "The full path to your existing SSH private key name without the"
}
variable "grant_public_ip_address" {
  type        = bool
  default     = true
  description = "Decide if the EC2 instance should pull a public IP address or not"
}
variable "subnet_id" {
  type        = string
  description = "ID of the subnet the instance will be provisioned in"
  validation {
    condition     = can(regex("^subnet\\-[a-f0-9]{17}$", var.subnet_id))
    error_message = "Invalid subnet ID provided"
  }
}
variable "security_group_id" {
  type        = string
  description = "ID of the security group the instance will use"
  validation {
    condition     = length(var.security_group_id) > 0 ? can(regex("^sg\\-[a-f0-9]{17}$", var.subnet_id)) : true
    error_message = "Invalid security group ID provided"
  }
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
  type        = list(string)
  default     = []
  description = "List of regions to scan (leave empty for all regions)"
}
variable "aws_services_list" {
  type        = list(string)
  default     = []
  description = "List of services to scan (leave empty for all services)"
}
variable "additional_tags" {
  type        = map(string)
  default = {}
  description = "Any additional tags to add to all resources (do not use the 'Name' key)"
}
variable "cspm_run_frequency" {
  type        = number
  default     = 12
  description = "What is the interval the CSPM should run in hours"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  owners = ["099720109477"] # Canonical
}
data "aws_subnet" "this" {
  id = var.subnet_id
}
data "http" "external-ip-address" {
  url = "http://ipinfo.io/ip"
  lifecycle {
    postcondition {
      condition     = self.status_code == 200
      error_message = "${self.url} returned an unhealthy status code. Consider using the 'STA-external-IP-address-for-management' variable to define access IP to the STA."
    }
    postcondition {
      condition     = can(regex("^(\\d{1,3}\\.){3}\\d{1,3}$", self.response_body))
      error_message = "${self.url} returned a respnse that is not IPv4. Consider using the 'STA-external-IP-address-for-management' variable to define access IP to the STA."
    }
  }
}

locals {
  docker_install = <<EOF
apt-get remove docker docker-engine docker.io containerd runc
apt-get install ca-certificates curl gnupg lsb-release -y
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null\nsudo apt update
apt update
apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y
usermod -aG docker ubuntu
newgrp docker
EOF
  security_group_rules = {
    ingress_1 = {
      type        = "ingress"
      protocol    = "tcp"
      from_port   = 22
      to_port     = 22
      cidr_blocks = ["${data.http.external-ip-address.response_body}/32"]
    }
    egress_1 = {
      type        = "egress"
      protocol    = "-1"
      from_port   = 0
      to_port     = 65535
      cidr_blocks = ["0.0.0.0/0"]
    }
  }
}

resource "aws_instance" "this" {
  ami                         = data.aws_ami.ubuntu.image_id
  instance_type               = var.instance_type
  key_name                    = replace(basename(var.local-ssh-key-path), ".pem", "")
  associate_public_ip_address = var.grant_public_ip_address
  security_groups             = [
      length(var.security_group_id) > 0 ? var.security_group_id : aws_security_group.this[0].id
  ]
  subnet_id            = var.subnet_id
  iam_instance_profile = aws_iam_instance_profile.this.id
  provisioner "file" {
    source      = "../code/code.zip"
    destination = "/home/ubuntu/code.zip"
  }
  connection {
    type        = "ssh"
    host        = self.public_ip
    user        = "ubuntu"
    private_key = file(var.local-ssh-key-path)
    timeout     = "4m"
  }
  root_block_device {
    volume_type = "gp3"
    volume_size = 30
  }
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }
  user_data = <<EOF
#!/bin/bash
sudo apt-get update
sudo apt-get install unzip -y

mkdir /home/ubuntu/cspm
unzip /home/ubuntu/code.zip -d /home/ubuntu/cspm/
rm /home/ubuntu/code.zip

echo "PLATFORM: ${var.platform}" > /home/ubuntu/cspm/config.yaml
echo "CX_ENDPOINT: ${var.coralogix_endpoint}" >> /home/ubuntu/cspm/config.yaml
echo "CX_API_KEY: ${var.coralogix_api_key}" >> /home/ubuntu/cspm/config.yaml
echo "AWS_REGIONS: ${jsonencode(var.aws_region_list)}" >> /home/ubuntu/cspm/config.yaml
echo "AWS_SERVICES: ${jsonencode(var.aws_services_list)}" >> /home/ubuntu/cspm/config.yaml

${local.docker_install}
crontab -l | { cat; echo \"0 ${var.cspm_run_frequency} * * * python3 /home/ubuntu/cspm/cspm.py \"; } | crontab -
EOF
  tags      = merge(var.additional_tags,
    {
      Name = "CSPM"
    }
  )
}
resource "aws_security_group" "this" {
  count  = length(var.security_group_id) > 0 ? 0 : 1
  name   = "CSPM"
  vpc_id = data.aws_subnet.this.vpc_id
  tags   = var.additional_tags
}
resource "aws_security_group_rule" "this" {
  for_each          = length(var.security_group_id) > 0 ? {} : local.security_group_rules
  security_group_id = aws_security_group.this[0].id
  type              = each.value["type"]
  protocol          = each.value["protocol"]
  from_port         = each.value["from_port"]
  to_port           = each.value["to_port"]
  cidr_blocks       = each.value["cidr_blocks"]
}
resource "aws_iam_instance_profile" "this" {
  name = "CSPM-Instance-Profile"
  role = aws_iam_role.this.name
  tags = var.additional_tags
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
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
  tags = var.additional_tags
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
  roles      = [aws_iam_role.this.name]
}

output "Instance-Address" {
  value = var.grant_public_ip_address ? aws_instance.this.public_ip : "No public IP attached for the instance"
}