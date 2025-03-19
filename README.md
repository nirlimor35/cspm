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