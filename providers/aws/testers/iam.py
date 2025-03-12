import inspect
from providers.aws.aws import AWSTesters
from botocore.exceptions import ClientError
from datetime import datetime, timezone, timedelta

"""
IAM root user access key should not exist
IAM policies should not allow full "*" administrative privileges
IAM Access Analyzer analyzers should be tagged
mfa_should_be_enabled_for_users_with_console_access
Password policies for IAM users should have strong configurations
Ensure IAM password policy prevents password reuse
IAM customer managed policies that you create should not allow wildcard actions for services
Expired SSL/TLS certificates managed in IAM should be removed
IAM identities should not have the AWSCloudShellFullAccess policy attached
IAM Access Analyzer external access analyzer should be enabled
Password policies for IAM users should have strong configurations
Unused IAM user credentials should be removed
IAM customer managed policies should not allow decryption actions on all KMS keys
IAM principals should not have IAM inline policies that allow decryption actions on all KMS keys
Neptune DB clusters should have IAM database authentication enabled
"""


class Service(AWSTesters):
    def __init__(self, execution_id, client, account_id, region, shipper):
        self.execution_id = execution_id
        self.service_name = "IAM"
        self.account_id = account_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.iam_client = client("iam")
        self.password_policy = None
        self.roles = None

    def _iam_init(self):
        account_password_policy = self.iam_client.get_account_password_policy()
        self.password_policy = account_password_policy[
            "PasswordPolicy"] if "PasswordPolicy" in account_password_policy else None

        list_users_response = self.iam_client.list_users()
        self.iam_users = list_users_response["Users"] if "Users" in list_users_response else None

        roles = []
        paginator = self.iam_client.get_paginator('list_roles')
        for page in paginator.paginate():
            roles.extend(page['Roles'])
        self.roles = roles

    def global_test_iam_password_policy_requires_at_least_one_uppercase_letter(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.password_policy and self.password_policy["RequireUppercaseCharacters"]:
            results.append(self._generate_results(self.execution_id,
                                                  self.account_id, self.service_name, test_name, self.account_id,
                                                  self.region, False, self.password_policy))
        else:
            results.append(self._generate_results(self.execution_id,
                                                  self.account_id, self.service_name, test_name, self.account_id,
                                                  self.region, True, self.password_policy))
        return results

    def global_test_iam_password_policy_requires_at_least_one_lowercase_letter(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.password_policy and self.password_policy["RequireLowercaseCharacters"]:
            results.append(self._generate_results(self.execution_id,
                                                  self.account_id, self.service_name, test_name, self.account_id,
                                                  self.region, False, self.password_policy))
        else:
            results.append(self._generate_results(self.execution_id,
                                                  self.account_id, self.service_name, test_name, self.account_id,
                                                  self.region, True, self.password_policy))
        return results

    def global_test_iam_password_policy_requires_symbols(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.password_policy and self.password_policy["RequireSymbols"]:
            results.append(self._generate_results(self.execution_id,
                                                  self.account_id, self.service_name, test_name, self.account_id,
                                                  self.region, False, self.password_policy))
        else:
            results.append(self._generate_results(self.execution_id,
                                                  self.account_id, self.service_name, test_name, self.account_id,
                                                  self.region, True, self.password_policy))
        return results

    def global_test_iam_password_policy_requires_numbers(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.password_policy and self.password_policy["RequireNumbers"]:
            results.append(self._generate_results(self.execution_id,
                                                  self.account_id, self.service_name, test_name, self.account_id,
                                                  self.region, False, self.password_policy))
        else:
            results.append(self._generate_results(self.execution_id,
                                                  self.account_id, self.service_name, test_name, self.account_id,
                                                  self.region, True, self.password_policy))
        return results

    def global_test_iam_password_policy_requires_minimum_password_length_of_14_or_greater(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.password_policy and self.password_policy["MinimumPasswordLength"]:
            if self.password_policy["MinimumPasswordLength"] < 14:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, self.account_id,
                                                      self.region, True, self.password_policy))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, self.account_id,
                                                      self.region, False, self.password_policy))
        return results

    def global_test_iam_password_policy_expires_passwords_within_90_days_or_less(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.password_policy and self.password_policy["MaxPasswordAge"]:
            if self.password_policy["MaxPasswordAge"] < 90:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, self.account_id,
                                                      self.region, False, self.password_policy))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, self.account_id,
                                                      self.region, True, self.password_policy))
        return results

    def global_test_mfa_should_be_enabled_for_all_iam_users(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        user_names = [user["UserName"] for user in self.iam_users]
        for user_name in user_names:
            mfa_device_for_user = self.iam_client.list_mfa_devices(UserName=user_name)
            if "MFADevices" in mfa_device_for_user and len(mfa_device_for_user["MFADevices"]) > 0:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, user_name,
                                                      self.region, False))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, user_name,
                                                      self.region, True))
        return results

    def global_test_mfa_should_be_enabled_for_users_with_console_access(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        user_names = [user["UserName"] for user in self.iam_users]
        for user_name in user_names:
            try:
                user_with_console_access = self.iam_client.get_login_profile(UserName=user_name)
                if user_with_console_access and len(user_with_console_access) > 0:
                    mfa_device_for_user = self.iam_client.list_mfa_devices(UserName=user_name)
                    if "MFADevices" in mfa_device_for_user and len(mfa_device_for_user["MFADevices"]) > 0:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name, user_name,
                                                              self.region, False))
                    else:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name, user_name,
                                                              self.region, True))
            except ClientError as error:
                if error.response['Error']['Code'] == 'NoSuchEntity':
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, user_name,
                                                          self.region, False))

        return results

    def global_test_iam_users_should_be_tagged(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        user_names = [user["UserName"] for user in self.iam_users]
        for user_name in user_names:
            user_details = self.iam_client.get_user(UserName=user_name)["User"]
            if "Tags" in user_details:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, user_name,
                                                      self.region, False, {"tags": user_details["Tags"]}))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, user_name,
                                                      self.region, True))
        return results

    def global_test_iam_roles_should_be_tagged(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]
        results = []
        role_names = [role["RoleName"] for role in self.roles]
        for role_name in role_names:
            role_tags = self.iam_client.list_role_tags(RoleName=role_name)
            if "Tags" in role_tags and len(role_tags["Tags"]) > 0:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, role_name,
                                                      self.region, False, {"tags": role_tags["Tags"]}))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, role_name,
                                                      self.region, True, {"tags": role_tags["Tags"]}))
        return results

    def global_test_iam_users_should_not_have_iam_policies_attached(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        user_names = [user["UserName"] for user in self.iam_users]
        for user_name in user_names:
            existing_user_policies = False
            user_policies = self.iam_client.list_user_policies(UserName=user_name)
            if "PolicyNames" in user_policies and len(user_policies["PolicyNames"]) > 0:
                existing_user_policies = True

            existing_user_attached_policies = False
            user_attached_policies = self.iam_client.list_attached_user_policies(UserName=user_name)
            if "AttachedPolicies" in user_attached_policies and len(user_attached_policies["AttachedPolicies"]) > 0:
                existing_user_attached_policies = True

            additional_data = {"user_policies": user_policies["PolicyNames"],
                               "user_attached_policies": user_attached_policies["AttachedPolicies"]}
            if existing_user_policies or existing_user_attached_policies:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, user_name,
                                                      self.region, True, additional_data))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, user_name,
                                                      self.region, False, additional_data))
        return results

    def global_test_iam_user_credentials_unused_for_45_days_should_be_removed(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        threshold_date = datetime.now(timezone.utc) - timedelta(days=45)
        for user in self.iam_users:
            user_name = user['UserName']
            user_unused = True

            password_last_used = user.get('PasswordLastUsed')
            if password_last_used and password_last_used >= threshold_date:
                user_unused = False

            access_keys = self.iam_client.list_access_keys(UserName=user_name)['AccessKeyMetadata']
            for key in access_keys:
                key_id = key['AccessKeyId']
                last_used_response = self.iam_client.get_access_key_last_used(AccessKeyId=key_id)
                last_used_date = last_used_response['AccessKeyLastUsed'].get('LastUsedDate')

                if last_used_date and last_used_date >= threshold_date:
                    user_unused = False

            if user_unused:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, user_name,
                                                      self.region, True))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, user_name,
                                                      self.region, False))
        return results

    def global_test_iam_users_access_keys_should_be_rotated_every_90_days_or_less(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        threshold_date = datetime.now(timezone.utc) - timedelta(days=90)
        for user in self.iam_users:
            user_name = user['UserName']
            old_keys = []
            access_keys = self.iam_client.list_access_keys(UserName=user_name)['AccessKeyMetadata']
            for key in access_keys:
                key_id = key['AccessKeyId']
                created_date = key['CreateDate']
                if created_date < threshold_date:
                    old_keys.append({
                        'AccessKeyId': key_id,
                        'CreateDate': created_date.strftime('%Y-%m-%d')
                    })
            additional_data = {"access_keys": old_keys}
            if old_keys and len(old_keys) > 0:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, user_name,
                                                      self.region, True, additional_data))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name, user_name,
                                                      self.region, False, additional_data))
        return results

    def run(self):
        global_tests, regional_tests = self._get_all_tests()
        if self.region != "global":
            self.run_test(self.service_name, regional_tests, self.shipper, self.region)
        if self.region == "global":
            self._iam_init()
            self.run_test(self.service_name, global_tests, self.shipper, self.region)
