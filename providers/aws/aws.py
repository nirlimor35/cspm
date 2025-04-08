import boto3
import json
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
    def _generate_results(execution_id, account_id: str, service: str, test_name: str, resource: str, region: str, issue_found: bool, additional_data=None) -> dict:
        return {
            "execution_id": execution_id,
            "account_id": account_id,
            "service": service,
            "test_name": test_name,
            "resource": resource,
            "region": region,
            "issue_found": issue_found,
            "additional_data": {} if additional_data is None else additional_data
        }

    @staticmethod
    def _datetime_handler(obj):
        from datetime import datetime, timezone

        if isinstance(obj, datetime):
            return obj.astimezone(timezone.utc).isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def _get_all_tests(self):
        global_tests = list()
        regional_tests = list()
        for method_name in dir(self):
            if method_name.startswith("global_test_"):
                method = getattr(self, method_name)
                if callable(method):
                    global_tests.append(method)
            elif method_name.startswith("test_"):
                method = getattr(self, method_name)
                if callable(method):
                    regional_tests.append(method)
        return global_tests, regional_tests

    @staticmethod
    def run_test(service_name, all_tests, shipper, region):
        try:
            results = []
            for cur_test in all_tests:
                try:
                    cur_results = cur_test()
                    if type(cur_results) is list:
                        for cur_result in cur_results:
                            results.append(cur_result)
                    else:
                        results.append(cur_results)
                except Exception as e:
                    print(e)
            if results and len(results) > 0:
                print(json.dumps(results, indent=2))
                print(f" INFO 🔵 {service_name} :: Sending {len(results)} logs to Coralogix for {region} region")
                # shipper(results)
            else:
                pass
                # print(f" INFO 🔵 {service_name} :: No logs found for {region}")
        except Exception as e:
            print(f"ERROR ⭕️ {service_name} :: {e}")
            exit(8)
