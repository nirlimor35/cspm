import inspect
from providers.aws.aws import AWSTesters

"""
Route 53 health checks should be tagged
Route 53 public hosted zones should log DNS queries
"""


class Service(AWSTesters):
    def __init__(self, execution_id, client, account_id, region, shipper):
        self.service_name = "Route53"
        self.execution_id = execution_id
        self.account_id = account_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.route53_client = client("route53")

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
                        f" INFO 🔵 {self.service_name} :: 📨 Sending {len(results)} logs to Coralogix for region {self.region}")
                    self.shipper(results)
                else:
                    print(f" INFO 🔵 {self.service_name} :: No logs found for region {self.region}")

            except Exception as e:
                if e:
                    print(f"ERROR ⭕️ {self.service_name} :: {e}")
                    exit(8)
