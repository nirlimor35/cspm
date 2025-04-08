import inspect
import json

from providers.aws.aws import AWSTesters

"""
Amazon EC2 should be configured to use VPC endpoints that are created for the Amazon EC2 service
EC2 Client VPN endpoints should have client connection logging enabled
EC2 VPN connections should have logging enabled
EC2 Transit Gateways should not automatically accept VPC attachment requests
EC2 VPC Block Public Access settings should block internet gateway traffic
EC2 launch templates should not assign public IPs to network interfaces
EC2 paravirtual instance types should not be used
EC2 transit gateway attachments should be tagged
EC2 transit gateway route tables should be tagged
EC2 transit gateways should be tagged
Stopped EC2 instances should be removed after a specified time period
"""


class Service(AWSTesters):
    def __init__(self, execution_id, client, account_id, region, shipper):
        self.execution_id = execution_id
        self.service_name = "EC2"
        self.region = region
        self.account_id = account_id
        self.shipper = shipper.send_bulk
        self.ec2_client = client("ec2", self.region)
        self.autoscaling_client = client("autoscaling", self.region)
        self.all_tests, self.test_names = self._get_all_tests()
        self.describe_instances = None
        self.describe_autoscaling_groups = None
        self.describe_security_groups = None
        self.describe_subnets = None

    def _init_ec2(self):
        try:
            describe_instances = self.ec2_client.describe_instances()
            if "Reservations" in describe_instances:
                all_instances = []
                for instances in describe_instances["Reservations"]:
                    for instance in instances["Instances"]:
                        all_instances.append(instance)
                self.describe_instances = all_instances

            describe_autoscaling_groups = self.autoscaling_client.describe_auto_scaling_groups()
            if "AutoScalingGroups" in describe_autoscaling_groups:
                self.describe_autoscaling_groups = describe_autoscaling_groups["AutoScalingGroups"]

            describe_security_groups = self.ec2_client.describe_security_groups()
            if "SecurityGroups" in describe_security_groups:
                self.describe_security_groups = describe_security_groups["SecurityGroups"]

            describe_subnets = self.ec2_client.describe_subnets()
            if "Subnets" in describe_subnets:
                self.describe_subnets = describe_subnets["Subnets"]

        except Exception as e:
            print(f"ERROR ⭕️ {self.service_name} :: {e}")

    def _get_launch_templates_version(self, template_id, version):
        return self.ec2_client.describe_launch_template_versions(
            LaunchTemplateId=template_id,
            Versions=[str(version)]
        )

    def test_auto_scaling_group_should_have_tags(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.describe_autoscaling_groups and len(self.describe_autoscaling_groups) > 0:
            for auto_scaling_group in self.describe_autoscaling_groups:
                group_name = auto_scaling_group["AutoScalingGroupName"]
                tags = auto_scaling_group["Tags"]
                if tags and len(tags) > 0:
                    results.append(
                        self._generate_results(self.execution_id, self.account_id, self.service_name, test_name,
                                               group_name, self.region,
                                               False))
                else:
                    results.append(
                        self._generate_results(self.execution_id, self.account_id, self.service_name, test_name,
                                               group_name, self.region,
                                               True))
        return results

    def test_auto_scaling_group_should_cover_multiple_availability_zones(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.describe_autoscaling_groups and len(self.describe_autoscaling_groups) > 0:
            for auto_scaling_group in self.describe_autoscaling_groups:
                group_name = auto_scaling_group["AutoScalingGroupName"]
                availability_zones_array = auto_scaling_group["AvailabilityZones"]
                if availability_zones_array and len(availability_zones_array) > 1:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, group_name,
                                                          self.region, False,
                                                          {"availablity_zones": availability_zones_array}))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, group_name,
                                                          self.region, True,
                                                          {"availablity_zones": availability_zones_array}))
        return results

    def test_launch_template_require_instance_metadata_v2(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        try:
            all_launch_templates = self.ec2_client.describe_launch_templates()
            if all_launch_templates and "LaunchTemplates" in all_launch_templates:
                for launch_template in all_launch_templates["LaunchTemplates"]:
                    launch_template_name = launch_template["LaunchTemplateName"]
                    launch_template_id = launch_template["LaunchTemplateId"]
                    default_version = launch_template["DefaultVersionNumber"]
                    latest_version = launch_template["LatestVersionNumber"]

                    additional_data = {
                        "default_version": default_version,
                        "latest_version": latest_version
                    }
                    describe_cur_version = self._get_launch_templates_version(launch_template_id, default_version)
                    if "LaunchTemplateVersions" in describe_cur_version:
                        cur_version = describe_cur_version["LaunchTemplateVersions"][0]
                        if "LaunchTemplateData" in cur_version \
                                and "MetadataOptions" in cur_version["LaunchTemplateData"] \
                                and "HttpTokens" in cur_version["LaunchTemplateData"]["MetadataOptions"] \
                                and cur_version["LaunchTemplateData"]["MetadataOptions"]["HttpTokens"] == "required":
                            results.append(self._generate_results(self.execution_id,
                                                                  self.account_id, self.service_name, test_name,
                                                                  launch_template_name, self.region, False,
                                                                  additional_data))
                        else:
                            results.append(self._generate_results(self.execution_id,
                                                                  self.account_id, self.service_name, test_name,
                                                                  launch_template_name, self.region, True,
                                                                  additional_data))
        except Exception as e:
            print(f"ERROR ⭕ {self.service_name} :: {e}")

        return results

    def test_launch_configuration_require_instance_metadata_v2(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        all_launch_configurations = self.autoscaling_client.describe_launch_configurations()
        if "LaunchConfigurations" in all_launch_configurations:
            for launch_configuration in all_launch_configurations["LaunchConfigurations"]:
                launch_configuration_name = launch_configuration["LaunchConfigurationName"]
                if "MetadataOptions" in launch_configuration \
                        and "HttpTokens" in launch_configuration["MetadataOptions"] \
                        and launch_configuration["MetadataOptions"]["HttpTokens"] == "required":
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          launch_configuration_name, self.region, False))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          launch_configuration_name, self.region, True))
        return results

    def test_auto_scaling_groups_should_use_launch_templates(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.describe_autoscaling_groups and len(self.describe_autoscaling_groups) > 0:
            for auto_scaling_group in self.describe_autoscaling_groups:
                group_name = auto_scaling_group["AutoScalingGroupName"]
                if "LaunchConfigurationName" in auto_scaling_group:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, group_name,
                                                          self.region, True))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, group_name,
                                                          self.region, False))
        return results

    def test_unused_eips_should_be_removed(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        try:
            all_elastic_ips = self.ec2_client.describe_addresses()
            if all_elastic_ips and "Addresses" in all_elastic_ips:
                for elastic_ip in all_elastic_ips["Addresses"]:
                    cur_address = elastic_ip["PublicIp"]
                    if "AllocationId" not in elastic_ip:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name, cur_address,
                                                              self.region, True))
                    else:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name, cur_address,
                                                              self.region, False))
        except Exception as e:
            print(f"ERROR ⭕ {self.service_name} :: {e}")
        return results

    def test_instances_should_be_tagged(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for instance in self.describe_instances:
            cur_instance_id = instance["InstanceId"]
            if "Tags" in instance and len(instance["Tags"]) > 0:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, cur_instance_id,
                                                      self.region, False,
                                                      {"tags": instance["Tags"]}))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, cur_instance_id,
                                                      self.region, True,
                                                      {"tags": {}}))
        return results

    def test_instances_launched_using_auto_scaling_group_should_not_have_public_ip_addresses(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for instance in self.describe_instances:
            cur_instance_id = instance["InstanceId"]
            if "Tags" in instance and len(instance["Tags"]) > 0:
                for tag in instance["Tags"]:
                    if tag["Key"] == "aws:autoscaling:groupName":
                        if "PublicIpAddress" in instance and instance["PublicIpAddress"] and len(
                                instance["PublicIpAddress"]) > 0:
                            results.append(self._generate_results(self.execution_id,
                                                                  self.account_id, self.service_name, test_name,
                                                                  cur_instance_id, self.region, True,
                                                                  {"public_ip": instance["PublicIpAddress"]}))
                        else:
                            results.append(self._generate_results(self.execution_id,
                                                                  self.account_id, self.service_name, test_name,
                                                                  cur_instance_id, self.region, False,
                                                                  {"public_ip": "no IP found"}))
        return results

    def test_unused_security_groups_should_be_removed(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        used_security_group = []
        for instance in self.describe_instances:
            if "SecurityGroups" in instance:
                for security_group in instance["SecurityGroups"]:
                    used_security_group.append(security_group["GroupId"])

        existing_security_groups = {}
        for existing_security_group in self.describe_security_groups:
            if existing_security_group["GroupName"] != "default":
                existing_security_groups.update({
                    existing_security_group["GroupName"]: existing_security_group["GroupId"]
                })

        for security_group_name, security_group_id in existing_security_groups.items():
            if security_group_id in used_security_group:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, security_group_id,
                                                      self.region, False, {"security_group_name": security_group_name}))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, security_group_id,
                                                      self.region, True, {"security_group_name": security_group_name}))
        return results

    def test_security_groups_should_be_tagged(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for existing_security_group in self.describe_security_groups:
            security_group_name = existing_security_group["GroupName"]
            security_group_id = existing_security_group["GroupId"]
            if "Tags" in existing_security_group and existing_security_group["Tags"] and len(
                    existing_security_group["Tags"]) > 0:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, security_group_id,
                                                      self.region, False,
                                                      {"security_group_name": security_group_name}))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, security_group_id,
                                                      self.region, True,
                                                      {"security_group_name": security_group_name}))

        return results

    def test_default_security_groups_should_not_allow_inbound_or_outbound_traffic(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for security_group in self.describe_security_groups:
            security_group_name = security_group["GroupName"]
            security_group_id = security_group["GroupId"]
            if security_group_name == "default":
                ingress_rules_exists = False
                egress_rules_exists = False
                if "IpPermissions" in security_group and len(security_group["IpPermissions"]) > 0:
                    ingress_rules_exists = True
                if "IpPermissionsEgress" in security_group and len(security_group["IpPermissionsEgress"]) > 0:
                    egress_rules_exists = True

                if egress_rules_exists or ingress_rules_exists:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          security_group_id,
                                                          self.region, True,
                                                          {"security_group_name": security_group_name}))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          security_group_id,
                                                          self.region, False,
                                                          {"security_group_name": security_group_name}))
        return results

    def test_instances_should_not_have_a_public_ipv4_address(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for instance in self.describe_instances:
            cur_instance_id = instance["InstanceId"]
            if "PublicIpAddress" in instance and len(instance["PublicIpAddress"]) > 0:
                additional_data = {"public_ip": instance["PublicIpAddress"]}
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, cur_instance_id,
                                                      self.region, True, additional_data))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, cur_instance_id,
                                                      self.region, False, {"public_ip": "None"}))
        return results

    def test_instances_should_not_use_multiple_enis(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for instance in self.describe_instances:
            cur_instance_id = instance["InstanceId"]
            if "NetworkInterfaces" in instance:
                eni_ids = [eni["NetworkInterfaceId"] for eni in instance["NetworkInterfaces"]]
                additional_data = {"network_interface_ids": eni_ids}
                if len(eni_ids) > 1:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          cur_instance_id,
                                                          self.region, True, additional_data))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          cur_instance_id,
                                                          self.region, False, additional_data))
        return results

    def test_volumes_should_be_tagged(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        volumes = self.ec2_client.describe_volumes()
        if "Volumes" in volumes and len(volumes["Volumes"]) > 0:
            for volume in volumes["Volumes"]:
                cur_volume_id = volume["VolumeId"]
                attachments = json.loads(json.dumps(volume["Attachments"] if "Attachments" in volume else [], default=str))
                tags = json.loads(json.dumps(volume["Tags"] if "Tags" in volume else [], default=str))
                additional_data = {"attachments": attachments,
                                   "tags": tags}
                if "Tags" in volume and len(volume["Tags"]) > 0:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          cur_volume_id,
                                                          self.region, False, additional_data))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          cur_volume_id,
                                                          self.region, True, additional_data))
        return results

    def _security_protocol_validator(self, ports: list, ipv: int, protocol: str, test_name: str):
        results = []
        server_administration_ports = ports
        for security_group in self.describe_security_groups:
            security_group_id = security_group["GroupId"]
            issue_found_for_sg = False
            additional_data = {"rules": []}
            if "IpPermissions" in security_group and len(security_group["IpPermissions"]) > 0:
                for security_group_rule in security_group["IpPermissions"]:
                    current_protocol = security_group_rule["IpProtocol"]
                    current_from_port = security_group_rule["FromPort"] if "FromPort" in security_group_rule else 0
                    current_to_port = security_group_rule["ToPort"] if "ToPort" in security_group_rule else 0

                    if ipv == 4:
                        current_ip_ranges = security_group_rule["IpRanges"]
                        cidr_obj = {"CidrIp": "0.0.0.0/0"}
                    else:
                        current_ip_ranges = security_group_rule["Ipv6Ranges"]
                        cidr_obj = {"CidrIpv6": "::/0"}

                    additional_data["rules"].append(security_group_rule)

                    if current_protocol == protocol and \
                            current_from_port in server_administration_ports and \
                            current_to_port in server_administration_ports and \
                            cidr_obj in current_ip_ranges:
                        issue_found_for_sg = True

            if issue_found_for_sg:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name,
                                                      security_group_id,
                                                      self.region, True, additional_data))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name,
                                                      security_group_id,
                                                      self.region, False, additional_data))
        return results

    def test_security_groups_should_not_allow_ingress_from_any_ipv4_to_remote_server_administration_ports(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]
        return self._security_protocol_validator([22, 3389], 4, "tcp", test_name)

    def test_security_groups_should_not_allow_ingress_from_any_ipv6_to_remote_server_administration_ports(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]
        return self._security_protocol_validator([22, 3389], 6, "tcp", test_name)

    def test_subnets_should_not_automatically_assign_public_ip_addresses(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for subnet in self.describe_subnets:
            subnet_id = subnet["SubnetId"]
            additional_data = {"subnet_name": ""}
            if "Tags" in subnet:
                for tag in subnet["Tags"]:
                    if tag["Key"] == "Name":
                        additional_data["subnet_name"] = tag["Value"]
            if "MapPublicIpOnLaunch" in subnet and subnet["MapPublicIpOnLaunch"]:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name,
                                                      subnet_id,
                                                      self.region, True, additional_data))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name,
                                                      subnet_id,
                                                      self.region, False, additional_data))
        return results

    def test_instances_should_use_instance_metadata_service_version_2(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for instance in self.describe_instances:
            cur_instance_id = instance["InstanceId"]
            additional_data = {"metadata_options": instance["MetadataOptions"]}

            if "MetadataOptions" in instance and \
                    instance["MetadataOptions"]["HttpTokens"] == "required" and \
                    instance["MetadataOptions"]["HttpPutResponseHopLimit"] == 2:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name,
                                                      cur_instance_id, self.region, False, additional_data))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name,
                                                      cur_instance_id, self.region, True, additional_data))
        return results

    def run(self):
        global_tests, regional_tests = self._get_all_tests()
        if self.region != "global":
            self._init_ec2()
            self.run_test(self.service_name, regional_tests, self.shipper, self.region)
        if self.region == "global":
            self.run_test(self.service_name, global_tests, self.shipper, self.region)
