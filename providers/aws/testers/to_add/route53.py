import inspect
from providers import Testers

"""
Route 53 health checks should be tagged
Route 53 public hosted zones should log DNS queries
"""


class Service(Testers):
    def __init__(self, execution_id, client, account_id, region, shipper):
        self.service_name = "Route53"
        self.execution_id = execution_id
        self.account_id = account_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.route53_client = client("route53")

    def run(self):
        global_tests, regional_tests = self._get_all_tests()
        if self.region != "global":
            self.run_test(self.service_name, regional_tests, self.shipper, self.region)
        if self.region == "global":
            self.run_test(self.service_name, global_tests, self.shipper, self.region)
