import re
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


class AWSTesters:
    @staticmethod
    def _generate_results(account_id: str, service: str, test_name: str, resource: str, region: str, issue_found: bool, additional_data=None) -> dict:
        return {
            "account_id": account_id,
            "service": service,
            "test_name": test_name,
            "resource": resource,
            "region": region,
            "issue_found": issue_found,
            "additional_data": {} if additional_data is None else additional_data
        }

    def _get_all_tests(self):
        test_names = []
        tests = list()
        for method_name in dir(self):
            if method_name.startswith("test_"):
                cur_test_name = re.search(r"test_(\S+)", str(method_name)).group(1)
                test_names.append(cur_test_name)
                method = getattr(self, method_name)
                if callable(method):
                    tests.append(method)
        return tests, test_names
