import inspect
from providers.aws.aws import AWSTesters
from botocore.exceptions import ClientError

"""
mfa_should_be_enabled_for_users_with_console_access
Password policies for IAM users should have strong configurations
Ensure IAM password policy prevents password reuse
IAM policies should not allow full "*" administrative privileges
IAM users should not have IAM policies attached
IAM customer managed policies that you create should not allow wildcard actions for services
IAM user credentials unused for 45 days should be removed
IAM Access Analyzer analyzers should be tagged
IAM roles should be tagged
IAM users should be tagged
Expired SSL/TLS certificates managed in IAM should be removed
IAM identities should not have the AWSCloudShellFullAccess policy attached
IAM Access Analyzer external access analyzer should be enabled
IAM users' access keys should be rotated every 90 days or less
IAM root user access key should not exist
Password policies for IAM users should have strong configurations
Unused IAM user credentials should be removed
IAM customer managed policies should not allow decryption actions on all KMS keys
IAM principals should not have IAM inline policies that allow decryption actions on all KMS keys
Neptune DB clusters should have IAM database authentication enabled
IAM authentication should be configured for RDS instances
IAM authentication should be configured for RDS clusters
"""


class Service(AWSTesters):
    def __init__(self, client, account_id, region, shipper):
        self.service_name = "IAM"
        self.account_id = account_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.iam_client = client("iam")
        self.password_policy = None

    def _iam_init(self):
        account_password_policy = self.iam_client.get_account_password_policy()
        self.password_policy = account_password_policy["PasswordPolicy"] if "PasswordPolicy" in account_password_policy else None
        list_users_response = self.iam_client.list_users()
        self.iam_users = list_users_response["Users"] if "Users" in list_users_response else None

    def test_iam_password_policy_requires_at_least_one_uppercase_letter(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.password_policy and self.password_policy["RequireUppercaseCharacters"]:
            results.append(self._generate_results(
                self.account_id, self.service_name, test_name, self.account_id, self.region, False, self.password_policy))
        else:
            results.append(self._generate_results(
                self.account_id, self.service_name, test_name, self.account_id, self.region, True, self.password_policy))
        return results

    def test_iam_password_policy_requires_at_least_one_lowercase_letter(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.password_policy and self.password_policy["RequireLowercaseCharacters"]:
            results.append(self._generate_results(
                self.account_id, self.service_name, test_name, self.account_id, self.region, False, self.password_policy))
        else:
            results.append(self._generate_results(
                self.account_id, self.service_name, test_name, self.account_id, self.region, True, self.password_policy))
        return results

    def test_iam_password_policy_requires_symbols(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.password_policy and self.password_policy["RequireSymbols"]:
            results.append(self._generate_results(
                self.account_id, self.service_name, test_name, self.account_id, self.region, False, self.password_policy))
        else:
            results.append(self._generate_results(
                self.account_id, self.service_name, test_name, self.account_id, self.region, True, self.password_policy))
        return results

    def test_iam_password_policy_requires_numbers(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.password_policy and self.password_policy["RequireNumbers"]:
            results.append(self._generate_results(
                self.account_id, self.service_name, test_name, self.account_id, self.region, False, self.password_policy))
        else:
            results.append(self._generate_results(
                self.account_id, self.service_name, test_name, self.account_id, self.region, True, self.password_policy))
        return results

    def test_iam_password_policy_requires_minimum_password_length_of_14_or_greater(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.password_policy and self.password_policy["MinimumPasswordLength"]:
            if self.password_policy["MinimumPasswordLength"] < 14:
                results.append(self._generate_results(
                    self.account_id, self.service_name, test_name, self.account_id, self.region, True, self.password_policy))
            else:
                results.append(self._generate_results(
                    self.account_id, self.service_name, test_name, self.account_id, self.region, False, self.password_policy))
        return results

    def test_iam_password_policy_expires_passwords_within_90_days_or_less(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.password_policy and self.password_policy["MaxPasswordAge"]:
            if self.password_policy["MaxPasswordAge"] < 90:
                results.append(self._generate_results(
                    self.account_id, self.service_name, test_name, self.account_id, self.region, False, self.password_policy))
            else:
                results.append(self._generate_results(
                    self.account_id, self.service_name, test_name, self.account_id, self.region, True, self.password_policy))
        return results

    def test_mfa_should_be_enabled_for_all_iam_users(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        user_names = [user["UserName"] for user in self.iam_users]
        for user_name in user_names:
            mfa_device_for_user = self.iam_client.list_mfa_devices(UserName=user_name)
            if "MFADevices" in mfa_device_for_user and len(mfa_device_for_user["MFADevices"]) > 0:
                results.append(self._generate_results(
                    self.account_id, self.service_name, test_name, user_name, self.region, False))
            else:
                results.append(self._generate_results(
                    self.account_id, self.service_name, test_name, user_name, self.region, True))
        return results

    def test_mfa_should_be_enabled_for_users_with_console_access(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        user_names = [user["UserName"] for user in self.iam_users]
        for user_name in user_names:
            try:
                user_with_console_access = self.iam_client.get_login_profile(UserName=user_name)
                if user_with_console_access and len(user_with_console_access) > 0:
                    mfa_device_for_user = self.iam_client.list_mfa_devices(UserName=user_name)
                    if "MFADevices" in mfa_device_for_user and len(mfa_device_for_user["MFADevices"]) > 0:
                        results.append(self._generate_results(
                            self.account_id, self.service_name, test_name, user_name, self.region, False))
                    else:
                        results.append(self._generate_results(
                            self.account_id, self.service_name, test_name, user_name, self.region, True))
            except ClientError as error:
                if error.response['Error']['Code'] == 'NoSuchEntity':
                    results.append(self._generate_results(
                        self.account_id, self.service_name, test_name, user_name, self.region, False))

        return results

    def run(self):
        if self.region == "global":
            self._iam_init()
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
                        f"INFO :: {self.service_name} :: 📨 Sending {len(results)} logs to Coralogix")
                    self.shipper(results)
                else:
                    print(f"INFO :: {self.service_name} :: No logs found")

            except Exception as e:
                if e:
                    print(f"⭕️ ERROR :: {self.service_name} :: {e}")
                    exit(8)
        else:
            pass
