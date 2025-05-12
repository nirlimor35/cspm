import inspect
from providers import Testers
from google.cloud import monitoring_v3
from google.cloud.logging_v2.services.metrics_service_v2 import MetricsServiceV2Client


class Service(Testers):
    def __init__(self, execution_id, credentials, project_id, region):
        self.service_name = "Logging"
        self.execution_id = execution_id
        self.project_id = project_id
        self.region = region
        self.log_client = MetricsServiceV2Client(credentials=credentials)
        self.monitoring_client = monitoring_v3.AlertPolicyServiceClient(credentials=credentials)

    @staticmethod
    def _log_metric_exists(client, project_id):
        EXPECTED_FILTER = (
            'resource.type="gcs_bucket" '
            'protoPayload.methodName:("SetIamPolicy" OR "SetBucketIamPolicy" OR "storage.setIamPermissions")'
        )
        for metric in client.list_log_metrics(parent=f"projects/{project_id}"):
            if EXPECTED_FILTER in metric.filter:
                return metric.name
        return None

    @staticmethod
    def _alerting_policy_exists(client, project_id, metric_name):
        project_name = f"projects/{project_id}"
        for policy in client.list_alert_policies(name=project_name):
            for condition in policy.conditions:
                if condition.condition_monitoring_query_language \
                        and metric_name in condition.condition_monitoring_query_language.query:
                    return True
        return False

    def global_test_log_metric_filter_and_alerts_should_exist_for_iam_permission_changes(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        metric_name = self._log_metric_exists(self.log_client, self.project_id)
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
            self.run_test(self.service_name, global_tests, "", self.region)
