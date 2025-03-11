import inspect
from providers.aws.aws import AWSTesters
from datetime import datetime, timezone, timedelta


class Service(AWSTesters):
    def __init__(self, execution_id, client, account_id, region, shipper):
        self.service_name = "Secret Manager"
        self.execution_id = execution_id
        self.account_id = account_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.secrets_manager_client = client("secretsmanager", self.region)
        self.list_secrets = None

    def _init_secret_manager(self):
        list_secrets = self.secrets_manager_client.list_secrets()
        if "SecretList" in list_secrets:
            self.list_secrets = list_secrets["SecretList"]

    def test_secrets_should_have_automatic_rotation_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.list_secrets and len(self.list_secrets) > 0:
            for secret in self.list_secrets:
                secret_name = secret["Name"]
                if "RotationEnabled" in secret:
                    if secret["RotationEnabled"]:
                        additional_data = {"rotation_rules": secret["RotationRules"]}
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              secret_name,
                                                              self.region, False,
                                                              additional_data))
                    else:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              secret_name,
                                                              self.region, True))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          secret_name,
                                                          self.region, True))

        return results

    def test_remove_unused_secrets_manager_secrets(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.list_secrets and len(self.list_secrets) > 0:
            for secret in self.list_secrets:
                secret_name = secret["Name"]

                last_accessed_str = secret["LastAccessedDate"] if "LastAccessedDate" in secret else None
                if last_accessed_str and len(str(last_accessed_str)) > 0:
                    last_accessed = datetime.fromisoformat(str(last_accessed_str))
                    now = datetime.now(timezone.utc)
                    difference = now - last_accessed.astimezone(timezone.utc)
                    secret_was_accessed_within_last_30_days = difference <= timedelta(days=14)
                    additional_data = {"difference": str(difference), "last_accessed": str(last_accessed_str)}

                    if secret_was_accessed_within_last_30_days:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              secret_name,
                                                              self.region, False,
                                                              additional_data))
                    else:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              secret_name,
                                                              self.region, True,
                                                              additional_data))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, secret_name,
                                                          self.region, True,
                                                          {"last_accessed": "never accessed",
                                                           "difference": "never accessed"}))
        return results

    def test_secrets_should_be_tagged(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.list_secrets and len(self.list_secrets) > 0:
            for secret in self.list_secrets:
                secret_name = secret["Name"]
                if "Tags" in secret and len(secret["Tags"]) > 0:
                    additional_data = {"tags": secret["Tags"]}
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, secret_name,
                                                          self.region, False, additional_data))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, secret_name,
                                                          self.region, True))
        return results

    def run(self):
        if self.region != "global":
            self._init_secret_manager()
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
                    # self.shipper(results)
                else:
                    print(f" INFO 🔵 {self.service_name} :: No logs found for region {self.region}")

            except Exception as e:
                if e:
                    print(f"ERROR ⭕️ {self.service_name} :: {e}")
                    exit(8)
