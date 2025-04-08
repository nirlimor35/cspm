# CSPM
This PoC CSPM is designed to catch a verity of misconfigurations and security exposures in AWS

Currently covering
* cloudtrail
* ec2
* ecr
* guardduty
* iam
* s3
* secret_manager
* sns
* vpc

With a total of 82 unique tests 

The current output can potentially vary, currently only supports Coralogix.  
## Prerequisites 
* For manual deployment - Set up the following policy in AWS 
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "CSPM",
          "Effect": "Allow",
          "Action": [
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
            "ec2:DescribeRegions",
            "ec2:DescribeVpcEndpoints",
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
            "sns:GetTopicAttributes"
          ],
          "Resource": "*"
        }
      ]
    }
    ```
* For Terraform automation, please [install terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)

## Usage
### As a container
Build the image
```shell
docker build -t cspm .
```

Run the code
```shell
docker run --rm \
  --name cspm \
  -e CLOUD_PROVIDER="aws" \
  -e PLATFORM=coralogix \
  -e CX_ENDPOINT=EU1 \
  -e CX_API_KEY=123... \
  -e AWS_REGIONS= \
  -e AWS_SERVICES= \
  --network host \
  -v ~/.aws:/root/.aws \
  --group-add $(stat -c '%g' /var/run/docker.sock) \
  -v /var/run/docker.sock:/var/run/docker.sock \
  cspm
```

#### Command explanation
* --network host is set to use the hosts network card instead of isolating the container completely
* -v ~/.aws:/root/.aws is set in case you are using local credentials. remove if not needed
* For scanning ECR containers
  * --group-add $(stat -c '%g' /var/run/docker.sock) is set to align the docker group ID on both the container and the host
  * -v /var/run/docker.sock:/var/run/docker.sock is the mapping of the unix socket file itself in order to use the docker service inside the container as if it is running from the host

### Terraform
Under the `automation` directory you can find two ready-made Terraform documents for deploying using
* EC2 machine
* Lambda function

Both options have a value file to fill the required data
Initialize terraform 
```bash
terraform init
```
Apply the run and review before deploying
```bash
terraform apply
```

After reviewing the resources to be added type "yes" in the prompted terminal and wait for the deployment to finish

Both deployments are contentious, and will run automatically in the interval of you choosing where the default is 12 hours

Common resources:
- Role
- Policy

EC2 resources:
- EC2 instance
- Instance profile
- Security group (when non was provided)
- Upon deployment, The stack will output the instances public IP (if `grant_public_ip_address` variable is set to `true` which is the default)

Lambda resources:
- Lambda function
- EventBridge rule for automating the trigger
