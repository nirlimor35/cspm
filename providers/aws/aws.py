import boto3
from providers.aws.aws_request_throttling_handler import handle_request


class AWS:
    def __init__(self, profile=None):
        self.profile = profile

    def get_client(self, service, region="us-east-1"):
        client = None
        if self.profile and len(self.profile) > 0:
            client = boto3.Session(profile_name=self.profile).client(service_name=service, region_name=region)
        else:
            client = boto3.client(service, region_name=region)
        return handle_request(lambda: client)

    @staticmethod
    def get_available_regions(client):
        regions_raw = client("ec2").describe_regions()["Regions"]
        regions = [region["RegionName"] for region in regions_raw]
        return regions

    @staticmethod
    def help(arg):
        if arg == 'services':
            response = """
Available Services for AWS:
- ec2
- s3
- cloudtrail
"""
            return response
