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
        "iam:GetAccountPasswordPolicy",
        "ec2:DescribeAddresses",
        "ec2:DescribeInstances",
        "iam:ListRoleTags",
        "cloudtrail:GetTrailStatus",
        "ec2:DescribeFlowLogs",
        "sns:ListTopics",
        "ec2:DescribeVpcEndpointServices",
        "cloudtrail:GetEventSelectors",
        "iam:ListMFADevices",
        "guardduty:GetDetector",
        "cloudtrail:ListTags",
        "iam:ListAttachedUserPolicies",
        "iam:ListAccessKeys",
        "sns:ListTagsForResource",
        "guardduty:ListDetectors",
        "sns:GetTopicAttributes",
        "ec2:DescribeLaunchTemplates",
        "ec2:DescribeVpcPeeringConnections",
        "ec2:DescribeLaunchTemplateVersions",
        "iam:GetAccessKeyLastUsed",
        "iam:ListRoles",
        "iam:ListUserPolicies",
        "cloudtrail:DescribeTrails",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeVpcs",
        "iam:ListUsers",
        "ec2:DescribeVpcEndpoints",
        "iam:GetUser",
        "iam:GetLoginProfile",
        "secretsmanager:ListSecrets"
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
  -e API_KEY=123 \
  -e AWS_REGIONS= \
  -e AWS_SERVICES= \
  --network host \
  -v ~/.aws:/root/.aws \
  -v /var/run/docker.sock:/var/run/docker.sock \
  cspm
```