import json
import inspect
from providers.aws.aws import AWSTesters
from botocore.exceptions import ClientError


class Service(AWSTesters):
    def __init__(self, execution_id, client, account_id, region, shipper):
        self.execution_id = execution_id
        self.service_name = "CloudTrail"
        self.account_id = account_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.cloudtrail_client = client
        self.s3_client = client("s3")
        self.trail_list = None

    def _init_cloudtrail(self):
        trail_list = self.cloudtrail_client("cloudtrail").describe_trails()
        if "trailList" in trail_list:
            self.trail_list = trail_list["trailList"]

    def global_test_cloudtrail_should_be_enabled_and_configured_with_at_least_one_multi_region_trail_that_includes_read_and_write_management_events(
            self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.trail_list and len(self.trail_list) > 0:
            for trail in self.trail_list:
                trail_name = trail['Name']
                region = trail["HomeRegion"]
                additional_data = {"home_region": region}

                status = self.cloudtrail_client("cloudtrail", region).get_trail_status(Name=trail_name)
                event_selectors = self.cloudtrail_client("cloudtrail", region).get_event_selectors(TrailName=trail_name)
                if "EventSelectors" in event_selectors:
                    event_selectors = event_selectors["EventSelectors"]
                elif "AdvancedEventSelectors" in event_selectors:
                    event_selectors = event_selectors["AdvancedEventSelectors"]
                is_enabled = status['IsLogging']
                is_multi_region = trail['IsMultiRegionTrail']

                logs_read__or_write_only = False
                for field_selector in event_selectors:
                    for k, v in field_selector.items():
                        if k == "FieldSelectors":
                            read_only = [f for f in v if f["Field"] == "readOnly"]
                            if read_only and len(read_only) > 0:
                                additional_data.update({"field_selector": field_selector["FieldSelectors"]})
                                logs_read__or_write_only = True

                if is_enabled and is_multi_region and not logs_read__or_write_only:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, trail_name,
                                                          self.region, False,
                                                          additional_data))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, trail_name,
                                                          self.region, True,
                                                          additional_data))
        return results

    def global_test_trail_should_have_encryption_at_rest_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.trail_list and len(self.trail_list) > 0:
            for trail in self.trail_list:
                trail_name = trail['Name']
                region = trail["HomeRegion"]
                additional_data = {"home_region": region}
                if "KmsKeyId" in trail:
                    additional_data.update({"kms_key_id": trail["KmsKeyId"]})
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, trail_name,
                                                          self.region, False,
                                                          additional_data))
                else:
                    additional_data.update({"kms_key_id": "no key found"})
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, trail_name,
                                                          self.region, True,
                                                          additional_data))
        return results

    def global_test_at_least_one_trail_is_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.trail_list and len(self.trail_list) > 0:
            results.append(self._generate_results(self.execution_id,
                                                  self.account_id, self.service_name, test_name, "CloudTrail",
                                                  self.region, False))
        else:
            results.append(self._generate_results(self.execution_id,
                                                  self.account_id, self.service_name, test_name, "CloudTrail",
                                                  self.region, True))
        return results

    def global_test_log_file_validation_should_be_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.trail_list and len(self.trail_list) > 0:
            for trail in self.trail_list:
                trail_name = trail['Name']
                region = trail["HomeRegion"]
                additional_data = {"home_region": region}
                if "LogFileValidationEnabled" in trail and trail["LogFileValidationEnabled"]:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, trail_name,
                                                          self.region, False,
                                                          additional_data))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, trail_name,
                                                          self.region, True,
                                                          additional_data))

        return results

    def global_test_trails_should_be_integrated_with_cloudwatch_logs(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.trail_list and len(self.trail_list) > 0:
            for trail in self.trail_list:
                trail_name = trail['Name']
                region = trail["HomeRegion"]
                additional_data = {"home_region": region}
                if "CloudWatchLogsLogGroupArn" in trail and len(trail["CloudWatchLogsLogGroupArn"]) > 0 \
                        and "CloudWatchLogsRoleArn" in trail and len(trail["CloudWatchLogsRoleArn"]) > 0:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, trail_name,
                                                          self.region, False,
                                                          additional_data))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name, trail_name,
                                                          self.region, True,
                                                          additional_data))

        return results

    def global_test_trails_should_be_tagged(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.trail_list and len(self.trail_list) > 0:
            for trail in self.trail_list:
                trail_name = trail['Name']
                trail_arn = trail["TrailARN"]
                region = trail["HomeRegion"]
                additional_data = {"home_region": region}
                resource_tag_list = self.cloudtrail_client("cloudtrail", region).list_tags(ResourceIdList=[trail_arn])

                if "ResourceTagList" in resource_tag_list:
                    cur_resource_tag_list = resource_tag_list["ResourceTagList"][0]
                    if "TagsList" in cur_resource_tag_list:
                        trail_tags = cur_resource_tag_list["TagsList"]
                        if trail_tags and len(trail_tags) > 0:
                            additional_data.update({"trail_tags": trail_tags})
                            results.append(self._generate_results(self.execution_id,
                                                                  self.account_id, self.service_name, test_name,
                                                                  trail_name, self.region, False,
                                                                  additional_data))
                        else:
                            results.append(self._generate_results(self.execution_id,
                                                                  self.account_id, self.service_name, test_name,
                                                                  trail_name, self.region, True,
                                                                  additional_data))

        return results

    def global_test_ensure_the_s3_bucket_used_to_store_cloudtrail_logs_is_not_publicly_accessible(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.trail_list and len(self.trail_list) > 0:
            for trail in self.trail_list:
                trail_name = trail['Name']
                if "S3BucketName" in trail:
                    s3_bucket_trail = trail["S3BucketName"]
                    additional_data = {"trails_bucket": s3_bucket_trail}
                    public_by_acl = False
                    public_by_policy = False
                    try:
                        acl = self.s3_client.get_bucket_acl(Bucket=s3_bucket_trail)
                        for grant in acl.get("Grants", []):
                            grantee = grant.get("Grantee", {})
                            if grantee.get("Type") == "Group" and "AllUsers" in grantee.get("URI", ""):
                                public_by_acl = True
                    except ClientError as e:
                        print(f"Error retrieving ACL for {s3_bucket_trail}: {e}")

                    try:
                        policy = self.s3_client.get_bucket_policy(Bucket=s3_bucket_trail)
                        policy_statements = json.loads(policy["Policy"]).get("Statement", [])
                        for statement in policy_statements:
                            if statement.get("Effect") == "Allow":
                                principal = statement.get("Principal", {})
                                if principal == "*" or (
                                        isinstance(principal, dict) and "AWS" in principal and principal["AWS"] == "*"):
                                    public_by_policy = True
                    except ClientError as e:
                        if "NoSuchBucketPolicy" in str(e):
                            print(f"[INFO] No bucket policy found for {s3_bucket_trail}.")
                        else:
                            print(f"Error retrieving policy for {s3_bucket_trail}: {e}")

                    if not public_by_acl and not public_by_policy:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              trail_name, self.region, False, additional_data))
                    else:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              trail_name, self.region, False, additional_data))
        return results

    def global_test_ensure_s3_bucket_access_logging_is_enabled_on_the_cloudtrail_s3_bucket(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.trail_list and len(self.trail_list) > 0:
            for trail in self.trail_list:
                trail_name = trail['Name']
                if "S3BucketName" in trail:
                    s3_bucket_trail = trail["S3BucketName"]
                    additional_data = {"trails_bucket": s3_bucket_trail}
                    try:
                        bucket_logging = self.s3_client.get_bucket_logging(Bucket=s3_bucket_trail)
                        if "LoggingEnabled" in bucket_logging:
                            results.append(self._generate_results(self.execution_id,
                                                                  self.account_id, self.service_name, test_name,
                                                                  trail_name, self.region, False, additional_data))
                        else:
                            results.append(self._generate_results(self.execution_id,
                                                                  self.account_id, self.service_name, test_name,
                                                                  trail_name, self.region, True, additional_data))
                    except ClientError as e:
                        print(f"Error {e}")
        return results

    def run(self):
        global_tests, regional_tests = self._get_all_tests()
        self._init_cloudtrail()
        if self.region != "global":
            self.run_test(self.service_name, regional_tests, self.shipper, self.region)
        if self.region == "global":
            self.run_test(self.service_name, global_tests, self.shipper, self.region)
