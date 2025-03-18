# CSPM

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