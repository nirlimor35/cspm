##  AWS
aws_region         = "eu-west-1"
instance_type      = "t3.medium"
local-ssh-key-path = "/full/path/to/key.pem"
subnet_id          = "subnet-041a..."
security_group_id = ""

## CSPM
platform           = "coralogix"
coralogix_endpoint = "EU1"
coralogix_api_key  = "229254e4-..."
# Leave lists empty for ALL values ->
aws_region_list    = [
  "eu-west-1",
  "us-east-1"
]
aws_services_list  = [
  "ec2",
  "vpc"
]
