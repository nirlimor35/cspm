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

With a total of 77 unique tests 

The current output can potentially vary, currently only supports Coralogix.  
## Prerequisites 
Set up the following policy in AWS 
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CSPM",
      "Effect": "Allow",
      "Action": [
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeLaunchConfigurations"
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
        "ecr:GetAuthorizationToken"
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
      ],
      "Resource": "*"
    }
  ]
}
```

## Usage
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
  -e CX_API_KEY=123 \
  -e AWS_REGIONS= \
  -e AWS_SERVICES= \
  --network host \
  -v ~/.aws:/root/.aws \
  -v /var/run/docker.sock:/var/run/docker.sock \
  cspm
```