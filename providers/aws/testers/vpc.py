import inspect
from providers.aws.aws import AWSTesters

"""
VPC subnets should be tagged
EC2 network interfaces should be tagged
EC2 customer gateways should be tagged
EC2 Elastic IP addresses should be tagged
EC2 internet gateways should be tagged
EC2 NAT gateways should be tagged
EC2 network ACLs should be tagged
EC2 route tables should be tagged
EC2 VPN gateways should be tagged
"""


class Service(AWSTesters):
    def __init__(self, execution_id, client, account_id, region, shipper):
        self.service_name = "VPC"
        self.execution_id = execution_id
        self.account_id = account_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.vpc_client = client("ec2", self.region)
        self.describe_vpcs = None
        self.vpc_flow_logs = None
        self.vpc_endpoints = None

    def _init_vpc(self):
        try:
            describe_vpcs = self.vpc_client.describe_vpcs()
            if "Vpcs" in describe_vpcs:
                self.describe_vpcs = describe_vpcs["Vpcs"]
            self.vpc_flow_logs = self.vpc_client.describe_flow_logs()["FlowLogs"]
            self.vpc_endpoints = self.vpc_client.describe_vpc_endpoints()["VpcEndpoints"]
        except Exception as e:
            print(f"ERROR ⭕ {self.service_name} :: {e}")

    def test_vpcs_should_be_tagged(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for vpc in self.describe_vpcs:
            vpc_id = vpc["VpcId"]
            if "Tags" in vpc and len(vpc["Tags"]) > 0:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, vpc_id,
                                                      self.region, False, vpc["Tags"]))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, vpc_id,
                                                      self.region, True))
        return results

    def test_vpc_flow_logs_should_be_tagged(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if len(self.vpc_flow_logs) > 0:
            for vpc_flow_log in self.vpc_flow_logs:
                vpc_id = vpc_flow_log["ResourceId"]
                if "Tags" in vpc_flow_log and len(vpc_flow_log["Tags"]) > 0:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, vpc_id,
                                                          self.region, False, vpc_flow_log["Tags"]))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, vpc_id,
                                                          self.region, True))
        return results

    def test_vpc_endpoint_services_should_be_tagged(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        try:
            ep_services = self.vpc_client.describe_vpc_endpoint_services()["ServiceDetails"]
            for ep_service in ep_services:
                service_id = ep_service["ServiceId"]
                additional_data = {"service_name": ep_service["ServiceName"]}
                if ep_service["Owner"] != "amazon" and ep_service["Owner"] != "aws-marketplace":
                    if "Tags" in ep_service and len(ep_service["Tags"]) > 0:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name, service_id,
                                                              self.region, False, additional_data))
                    else:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name, service_id,
                                                              self.region, True, additional_data))
        except Exception as e:
            print(f"ERROR ⭕ {self.service_name} :: {e}")
        return results

    def test_vpc_peering_connections_should_be_tagged(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        try:
            peerings = self.vpc_client.describe_vpc_peering_connections()
            if "VpcPeeringConnections" in peerings and len(peerings["VpcPeeringConnections"]) > 0:
                for peering in peerings["VpcPeeringConnections"]:
                    accepter_vpc_id = peering["AccepterVpcInfo"]["VpcId"]
                    requester_vpc_id = peering["RequesterVpcInfo"]["VpcId"]
                    peering_tags = peering["Tags"]
                    peering_id = peering["VpcPeeringConnectionId"]
                    additional_data = {"accepter_vpc_id": accepter_vpc_id, "requester_vpc_id": requester_vpc_id,
                                       "peering_tags": peering_tags}
                    if len(peering_tags) > 0:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name, peering_id,
                                                              self.region, False, additional_data))
                    else:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name, peering_id,
                                                              self.region, True, additional_data))
        except Exception as e:
            print(f"ERROR ⭕ {self.service_name} :: {e}")
        return results

    def test_vpc_flow_logging_should_be_enabled_in_all_vpcs(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        all_vpc_ids = [vpc["VpcId"] for vpc in self.describe_vpcs]
        all_vpc_flow_logs_vpc_ids = [vpc["ResourceId"] for vpc in self.vpc_flow_logs]
        for vpc_id in all_vpc_ids:
            if vpc_id in all_vpc_flow_logs_vpc_ids:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, vpc_id,
                                                      self.region, False))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, vpc_id,
                                                      self.region, True))
        return results

    def _get_interface_endpoint(self, test_name, service_name):
        results = []
        if self.vpc_endpoints and len(self.vpc_endpoints) > 0:
            for vpc_endpoint in self.vpc_endpoints:
                vpc_id = vpc_endpoint["VpcId"]
                if vpc_endpoint["ServiceName"] == service_name and vpc_endpoint["State"] == "available":
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, vpc_id,
                                                          self.region, False))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, vpc_id,
                                                          self.region, True))
        return results

    def test_vpcs_should_be_configured_with_an_interface_endpoint_for_ecr_api(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]
        return self._get_interface_endpoint(test_name, f"com.amazonaws.{self.region}.ecr.api")

    def test_vpcs_should_be_configured_with_an_interface_endpoint_for_docker_registry(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]
        return self._get_interface_endpoint(test_name, f"com.amazonaws.{self.region}.ecr.dkr")

    def test_vpcs_should_be_configured_with_an_interface_endpoint_for_systems_manager(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]
        return self._get_interface_endpoint(test_name, f"com.amazonaws.{self.region}.ssm")

    def test_vpcs_should_be_configured_with_an_interface_endpoint_for_systems_manager_contacts(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]
        return self._get_interface_endpoint(test_name, f"com.amazonaws.{self.region}.ssm-contacts")

    def test_vpcs_should_be_configured_with_an_interface_endpoint_for_systems_manager_incidents(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]
        return self._get_interface_endpoint(test_name, f"com.amazonaws.{self.region}.ssm-incidents")

    def run(self):
        global_tests, regional_tests = self._get_all_tests()
        if self.region != "global":
            self._init_vpc()
            self.run_test(self.service_name, regional_tests, self.shipper, self.region)
        if self.region == "global":
            self.run_test(self.service_name, global_tests, self.shipper, self.region)
