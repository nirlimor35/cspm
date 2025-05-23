import inspect
from providers import Testers
from google.cloud import monitoring_v3
from google.cloud.logging_v2.services.metrics_service_v2 import MetricsServiceV2Client


class Service(Testers):
    def __init__(self, execution_id, credentials, project_id, region, shipper):
        self.service_name = "Logging"
        self.execution_id = execution_id
        self.project_id = project_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.log_client = MetricsServiceV2Client(credentials=credentials)
        self.monitoring_client = monitoring_v3.AlertPolicyServiceClient(credentials=credentials)

    def _log_metric_exists(self, client, filter_to_check):
        for metric in list(client.list_log_metrics(parent=f"projects/{self.project_id}")):
            if filter_to_check in metric.filter:
                return metric.name
        return None

    @staticmethod
    def _alerting_policy_exists(client, project_id, metric_name):
        project_name = f"projects/{project_id}"
        for policy in list(client.list_alert_policies(name=project_name)):
            for condition in policy.conditions:
                if condition.condition_monitoring_query_language \
                        and metric_name in condition.condition_monitoring_query_language.query:
                    return True
        return False

    def global_test_log_metric_filter_and_alerts_should_exist_for_iam_permission_changes(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        filter_to_check = (
            'resource.type="gcs_bucket" '
            'protoPayload.methodName:("SetIamPolicy" OR "SetBucketIamPolicy" OR "storage.setIamPermissions")'
        )
        metric_name = self._log_metric_exists(self.log_client, filter_to_check)
        if metric_name:
            alert_exists = self._alerting_policy_exists(self.monitoring_client, self.project_id, metric_name)
            if alert_exists:
                results.append(self._generate_results(self.execution_id, self.project_id, self.service_name,
                                                      test_name, metric_name, self.region, False))
            else:
                results.append(self._generate_results(self.execution_id, self.project_id, self.service_name,
                                                      test_name, metric_name, self.region, True))
        else:
            results.append(self._generate_results(self.execution_id, self.project_id, self.service_name,
                                                  test_name, "no metric found", self.region, True))
        return results

    def run(self):
        global_tests, regional_tests = self._get_all_tests()
        if self.region != "global":
            pass
        if self.region == "global":
            # self.logging_init()
            self.run_test(self.service_name, global_tests, self.shipper, self.region)
