import inspect
from providers.aws.aws import AWSTesters

"""
✅S3 general purpose buckets should have block public access settings enabled
S3 general purpose buckets with versioning enabled should have Lifecycle configurations
S3 general purpose buckets should have event notifications enabled
ACLs should not be used to manage user access to S3 general purpose buckets
S3 general purpose buckets should have Lifecycle configurations
S3 general purpose buckets should have versioning enabled
S3 general purpose buckets should have Object Lock enabled
S3 general purpose buckets should be encrypted at rest with AWS KMS keys
S3 access points should have block public access settings enabled
S3 general purpose buckets should block public read access
S3 general purpose buckets should have MFA delete enabled
S3 general purpose buckets should log object-level write events
S3 general purpose buckets should log object-level read events
S3 Multi-Region Access Points should have block public access settings enabled
S3 general purpose buckets should block public write access
S3 general purpose buckets should require requests to use SSL
S3 general purpose bucket policies should restrict access to other AWS accounts
S3 general purpose buckets should use cross-Region replication
S3 general purpose buckets should block public access
S3 general purpose buckets should have server access logging enabled
"""


class Service(AWSTesters):
    def __init__(self, client, account_id, region, shipper):
        self.service_name = "S3"
        self.account_id = account_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.s3_client = client("s3")
        self.all_bucket_names = None

    def _s3_init(self):
        all_buckets = self.s3_client.list_buckets()
        if "Buckets" in all_buckets:
            self.all_bucket_names = [bucket_name["Name"] for bucket_name in all_buckets["Buckets"]]

    def test_buckets_should_have_block_public_access_settings_enabled(self):
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
                        results.append(self._generate_results(
                            self.account_id, self.service_name, test_name, bucket_name, self.region, True,
                            cur_block_public_access["PublicAccessBlockConfiguration"]))
                    else:
                        pass
                        results.append(self._generate_results(
                            self.account_id, self.service_name, test_name, bucket_name, self.region, False,
                            cur_block_public_access["PublicAccessBlockConfiguration"]))
                else:
                    results.append(self._generate_results(
                        self.account_id, self.service_name, test_name, bucket_name, self.region, False,
                        cur_block_public_access["PublicAccessBlockConfiguration"]))
            except Exception as e:
                print(f"⭕️ ERROR :: {self.service_name} :: {e}")
        return results

    def run(self):
        if self.region == "global":
            self._s3_init()
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
