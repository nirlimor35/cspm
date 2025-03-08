import inspect
from providers.aws.aws import AWSTesters

"""
✅GuardDuty should be enabled
✅GuardDuty S3 Protection should be enabled
✅GuardDuty Runtime Monitoring should be enabled
✅GuardDuty ECS Runtime Monitoring should be enabled
✅GuardDuty EC2 Runtime Monitoring should be enabled
✅GuardDuty EKS Runtime Monitoring should be enabled
✅GuardDuty detectors should be tagged
GuardDuty Lambda Protection should be enabled
GuardDuty RDS Protection should be enabled
GuardDuty filters should be tagged
GuardDuty IPSets should be tagged
GuardDuty EKS Audit Log Monitoring should be enabled
GuardDuty Malware Protection for EC2 should be enabled
"""


class Service(AWSTesters):
    def __init__(self, client, account_id, region, shipper):
        self.service_name = "GuardDuty"
        self.account_id = account_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.guardduty_client = client("guardduty", self.region)
        self.detector_ids = None

    def _init_guardduty(self):
        cur_detectors = self.guardduty_client.list_detectors()
        if "DetectorIds" in cur_detectors and len(cur_detectors["DetectorIds"]) > 0:
            self.detector_ids = cur_detectors["DetectorIds"]

    def _get_detector(self, detector_id):
        get_detector = self.guardduty_client.get_detector(DetectorId=detector_id)
        if get_detector and len(get_detector) > 0:
            return get_detector
        else:
            print(f"⭕️ ERROR :: {self.service_name} :: Failed to find detector with id '{detector_id}'")

    def _service_run_time_test(self, service, test_name):
        results = []
        if self.detector_ids and len(self.detector_ids):
            for detector_id in self.detector_ids:
                additional_data = {"detector_id": detector_id}
                cur_detector = self._get_detector(detector_id)
                if "Features" in cur_detector:
                    for feature in cur_detector["Features"]:
                        if feature["Name"] == "RUNTIME_MONITORING":
                            if "AdditionalConfiguration" in feature:
                                for additional_feature in feature["AdditionalConfiguration"]:
                                    if additional_feature["Name"] == service:
                                        if additional_feature["Status"] == "ENABLED":
                                            results.append(self._generate_results(
                                                self.account_id, self.service_name, test_name, "GuardDuty", self.region,
                                                False,
                                                additional_data))
                                        else:
                                            results.append(self._generate_results(
                                                self.account_id, self.service_name, test_name, "GuardDuty", self.region,
                                                True,
                                                additional_data))
        else:
            results.append(self._generate_results(
                self.account_id, self.service_name, test_name, "GuardDuty", self.region,
                True,
                {"detector_id": "no detector found"}))
        return results

    def test_guardduty_should_be_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.detector_ids and len(self.detector_ids):
            for detector_id in self.detector_ids:
                additional_data = {"detector_id": detector_id}
                cur_detector = self._get_detector(detector_id)
                if "Status" in cur_detector and cur_detector["Status"] == "ENABLED":
                    results.append(self._generate_results(
                        self.account_id, self.service_name, test_name, "GuardDuty", self.region, False,
                        additional_data))
                else:
                    results.append(self._generate_results(
                        self.account_id, self.service_name, test_name, "GuardDuty", self.region, True,
                        additional_data))

        else:
            results.append(self._generate_results(
                self.account_id, self.service_name, test_name, "GuardDuty", self.region, True,
                {"detector_id": "no detector found"}))
        return results

    def test_s3_protection_should_be_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.detector_ids and len(self.detector_ids):
            for detector_id in self.detector_ids:
                additional_data = {"detector_id": detector_id}

                cur_detector = self._get_detector(detector_id)

                s3_in_data_source = False
                s3_in_features = False

                if "DataSources" in cur_detector and "Features" in cur_detector:

                    # DataSources
                    if "S3Logs" in cur_detector["DataSources"] \
                            and "Status" in cur_detector["DataSources"]["S3Logs"] \
                            and cur_detector["DataSources"]["S3Logs"]["Status"] == "ENABLED":
                        s3_in_data_source = True

                    # Features
                    for feature in cur_detector["Features"]:
                        if feature["Name"] == "S3_DATA_EVENTS":
                            if feature["Status"] == "ENABLED":
                                s3_in_features = True

                if s3_in_data_source and s3_in_features:
                    results.append(self._generate_results(
                        self.account_id, self.service_name, test_name, "GuardDuty", self.region, False,
                        additional_data))
                else:
                    results.append(self._generate_results(
                        self.account_id, self.service_name, test_name, "GuardDuty", self.region, True))
        else:
            results.append(self._generate_results(
                self.account_id, self.service_name, test_name, "GuardDuty", self.region,
                True,
                {"detector_id": "no detector found"}))
        return results

    def test_runtime_monitoring_should_be_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.detector_ids and len(self.detector_ids):
            for detector_id in self.detector_ids:
                additional_data = {"detector_id": detector_id}
                cur_detector = self._get_detector(detector_id)
                if "Features" in cur_detector:
                    for feature in cur_detector["Features"]:
                        if feature["Name"] == "RUNTIME_MONITORING":
                            if feature["Status"] == "ENABLED":
                                results.append(self._generate_results(
                                    self.account_id, self.service_name, test_name, "GuardDuty", self.region, False,
                                    additional_data))
                            else:
                                results.append(self._generate_results(
                                    self.account_id, self.service_name, test_name, "GuardDuty", self.region, True,
                                    additional_data))
        else:
            results.append(self._generate_results(
                self.account_id, self.service_name, test_name, "GuardDuty", self.region,
                True,
                {"detector_id": "no detector found"}))
        return results

    def test_ec2_runtime_monitoring_should_be_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]
        return self._service_run_time_test("EC2_AGENT_MANAGEMENT", test_name)

    def test_ecs_runtime_monitoring_should_be_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]
        return self._service_run_time_test("ECS_FARGATE_AGENT_MANAGEMENT", test_name)

    def test_eks_runtime_monitoring_should_be_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]
        return self._service_run_time_test("EKS_ADDON_MANAGEMENT", test_name)

    def test_detectors_should_be_tagged(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.detector_ids and len(self.detector_ids):
            for detector_id in self.detector_ids:
                additional_data = {"detector_id": detector_id}
                cur_detector = self._get_detector(detector_id)
                if "Tags" in cur_detector and len(cur_detector["Tags"]) > 0:
                    results.append(self._generate_results(
                        self.account_id, self.service_name, test_name, "GuardDuty", self.region,
                        False,
                        additional_data))
                else:
                    results.append(self._generate_results(
                        self.account_id, self.service_name, test_name, "GuardDuty", self.region,
                        True,
                        additional_data))
        else:
            results.append(self._generate_results(
                self.account_id, self.service_name, test_name, "GuardDuty", self.region,
                True,
                {"detector_id": "no detector found"}))
        return results

    def run(self):
        import json
        if self.region != "global":
            self._init_guardduty()
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
                    print(json.dumps(results, indent=2))
                    print(
                        f"INFO :: {self.service_name} :: 📨 Sending {len(results)} logs to Coralogix for region {self.region}")
                    # self.shipper(results)
                else:
                    print(f"INFO :: {self.service_name} :: No logs found for region {self.region}")

            except Exception as e:
                if e:
                    print(f"⭕️ ERROR :: {self.service_name} :: {e}")
                    exit(8)
