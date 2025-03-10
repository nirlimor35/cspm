import inspect
from providers.aws.aws import AWSTesters


class Service(AWSTesters):
    def __init__(self, client, account_id, region, shipper):
        self.service_name = "VPC"
        self.account_id = account_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.vpc_client = client("ec2")

    def run(self):
        if self.region != "global":

            try:
                results = []
                all_tests, test_names = self._get_all_tests()
                for cur_test in all_tests:
                    cur_results = cur_test()
                    if type(cur_results) is list:
                        for cur_result in cur_results:
                            results.append(cur_result)
                    else:
                        results.append(cur_results)
                if results and len(results) > 0:
                    print(
                        f"INFO :: {self.service_name} :: 📨 Sending {len(results)} logs to Coralogix for region {self.region}")
                    self.shipper(results)
                else:
                    print(f"INFO :: {self.service_name} :: No logs found for region {self.region}")

            except Exception as e:
                if e:
                    print(f"⭕️ ERROR :: {self.service_name} :: {e}")
                    exit(8)