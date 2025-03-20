import inspect
from providers.aws.aws import AWSTesters
from botocore.exceptions import ClientError

"""
S3 general purpose buckets should log object-level write events
S3 general purpose buckets should log object-level read events
S3 general purpose buckets should block public read access
S3 general purpose buckets should have MFA delete enabled
S3 general purpose buckets should block public write access
S3 general purpose buckets should use cross-Region replication
S3 general purpose buckets should block public access
S3 general purpose buckets should have server access logging enabled
S3 general purpose buckets should require requests to use SSL
S3 general purpose bucket policies should restrict access to other AWS accounts
ACLs should not be used to manage user access to S3 general purpose buckets
S3 access points should have block public access settings enabled
S3 Multi-Region Access Points should have block public access settings enabled
"""


class Service(AWSTesters):
    def __init__(self, execution_id, client, account_id, region, shipper):
        self.service_name = "S3"
        self.execution_id = execution_id
        self.account_id = account_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.s3_client = client("s3")
        self.s3control_client = client("s3control", self.region)
        self.all_bucket_names = None
        self.all_access_points = None
        self.buckets_with_lifecycle_configuration_enabled = []
        self.buckets_with_versioning_enabled = []

    def _s3_init(self):
        try:
            all_buckets = self.s3_client.list_buckets()
            if "Buckets" in all_buckets:
                self.all_bucket_names = [bucket_name["Name"] for bucket_name in all_buckets["Buckets"]]
        except Exception as e:
            print(f"ERROR ⭕ {self.service_name} :: {e}")

    def _access_point_init(self):
        all_access_points = self.s3control_client.list_access_points(AccountId=self.account_id)
        if "AccessPointList" in all_access_points:
            self.all_access_points = all_access_points["AccessPointList"]

    def global_test_buckets_should_have_block_public_access_settings_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for bucket_name in self.all_bucket_names:
            try:
                cur_block_public_access = self.s3_client.get_public_access_block(Bucket=bucket_name)
                if cur_block_public_access and len(cur_block_public_access) > 0 \
                        and "PublicAccessBlockConfiguration" in cur_block_public_access:
                    open_configuration = False
                    for k, v in cur_block_public_access["PublicAccessBlockConfiguration"].items():
                        if not v:
                            open_configuration = True
                            break

                    if open_configuration:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              bucket_name, self.region, True,
                                                              cur_block_public_access[
                                                                  "PublicAccessBlockConfiguration"]))
                    else:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              bucket_name, self.region, False,
                                                              cur_block_public_access[
                                                                  "PublicAccessBlockConfiguration"]))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, bucket_name,
                                                          self.region, False,
                                                          cur_block_public_access["PublicAccessBlockConfiguration"]))
            except Exception as e:
                print(f"ERROR ⭕️ {self.service_name} :: {e}")
        return results

    def global_test_buckets_should_have_versioning_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for bucket_name in self.all_bucket_names:
            try:
                versioning = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
                if "Status" in versioning and versioning["Status"] == "Enabled":
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, bucket_name,
                                                          self.region, False))
                    self.buckets_with_versioning_enabled.append(bucket_name)
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, bucket_name,
                                                          self.region, True))
            except Exception as e:
                print(f"ERROR ⭕ {self.service_name} :: {e}")
        return results

    def global_test_buckets_should_have_lifecycle_configurations(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for bucket_name in self.all_bucket_names:
            try:
                response = self.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                rules = response.get('Rules', [])
                if rules:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, bucket_name,
                                                          self.region, False))
                    self.buckets_with_lifecycle_configuration_enabled.append(bucket_name)
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, bucket_name,
                                                          self.region, True))
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, bucket_name,
                                                          self.region, True))
                else:
                    print(f'ERROR ⭕️ Failed to check bucket "{bucket_name}" - {e}')
        return results

    def global_test_buckets_should_have_object_lock_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for bucket_name in self.all_bucket_names:
            try:
                response = self.s3_client.get_object_lock_configuration(Bucket=bucket_name)
                configuration = response.get('ObjectLockConfiguration', {})
                if configuration and configuration.get('ObjectLockEnabled') == 'Enabled':
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, bucket_name,
                                                          self.region, False))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, bucket_name,
                                                          self.region, True))
            except ClientError as e:
                if e.response['Error']['Code'] == 'ObjectLockConfigurationNotFoundError':
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, bucket_name,
                                                          self.region, True))
                else:
                    print(f'ERROR ⭕️ Failed to check bucket "{bucket_name}" - {e}')
        return results

    def global_test_buckets_with_versioning_enabled_should_have_lifecycle_configurations(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if len(self.buckets_with_versioning_enabled) > 0:
            for versioned_bucket in self.buckets_with_versioning_enabled:
                if versioned_bucket in self.buckets_with_lifecycle_configuration_enabled:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          versioned_bucket, self.region, False))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          versioned_bucket, self.region, True))
        return results

    def global_test_buckets_should_have_event_notifications_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for bucket_name in self.all_bucket_names:
            try:
                response = self.s3_client.get_bucket_notification_configuration(Bucket=bucket_name)
                del response["ResponseMetadata"]
                if response and len(response) > 0:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, bucket_name,
                                                          self.region, False, response))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, bucket_name,
                                                          self.region, True))
            except Exception as e:
                print(f"ERROR ⭕ {self.service_name} :: {e}")
        return results

    def global_test_buckets_should_be_encrypted_at_rest_with_aws_kms_keys(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for bucket_name in self.all_bucket_names:
            try:
                bucket_encryption = self.s3_client.get_bucket_encryption(Bucket=bucket_name)
                if "ServerSideEncryptionConfiguration" in bucket_encryption \
                        and "Rules" in bucket_encryption["ServerSideEncryptionConfiguration"]:
                    for rule in bucket_encryption["ServerSideEncryptionConfiguration"]["Rules"]:
                        if "BucketKeyEnabled" in rule:
                            if rule["BucketKeyEnabled"]:
                                results.append(self._generate_results(self.execution_id,
                                                                      self.account_id, self.service_name, test_name,
                                                                      bucket_name,
                                                                      self.region, False))
                            else:
                                results.append(self._generate_results(self.execution_id,
                                                                      self.account_id, self.service_name, test_name,
                                                                      bucket_name,
                                                                      self.region, True))
            except Exception as e:
                print(f"ERROR ⭕ {self.service_name} :: {e}")
        return results

    def test_s3_access_points_should_have_block_public_access_settings_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.all_access_points and len(self.all_access_points) > 0:
            for access_point in self.all_access_points:
                access_point_name = access_point["Name"]
                get_access_point = self.s3control_client.get_access_point(AccountId=self.account_id,
                                                                          Name=access_point_name)
                public_access_settings_enabled = True
                if "PublicAccessBlockConfiguration" in get_access_point:
                    for public_access_name, public_access_setting in \
                            get_access_point["PublicAccessBlockConfiguration"].items():
                        if not public_access_setting:
                            public_access_settings_enabled = False
                if public_access_settings_enabled:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          access_point_name,
                                                          self.region, False))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          access_point_name,
                                                          self.region, True))
        return results

    def run(self):
        global_tests, regional_tests = self._get_all_tests()
        self._s3_init()
        if self.region != "global":
            self._access_point_init()
            self.run_test(self.service_name, regional_tests, self.shipper, self.region)
        if self.region == "global":
            self.run_test(self.service_name, global_tests, self.shipper, self.region)
