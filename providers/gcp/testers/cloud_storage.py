import inspect
from providers import Testers
from google.cloud import storage

to_do = [
    {
        "name": "Bucket IAM not monitored",
        "description": "Log metric filter and alerts should exist for Cloud Storage IAM permission changes",
        "status": "pending"
    }
]
"""
Public bucket ACL
Public log bucket
Bucket CMEK disabled
Bucket IAM not monitored
Locked retention policy not set
"""


class Service(Testers):
    def __init__(self, execution_id, credentials, project_id, region, shipper):
        self.service_name = "Cloud Storage"
        self.execution_id = execution_id
        self.project_id = project_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.storage_client = storage.Client(project=project_id, credentials=credentials)
        self.all_bucket = None

    def cloud_storage_init(self):
        all_buckets = list(self.storage_client.list_buckets())
        self.all_bucket = all_buckets

    def global_test_bucket_logging_should_be_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for bucket in self.all_bucket:
            bucket.reload()
            bucket_name = bucket.name
            properties = bucket._properties

            if "logging" in properties and properties["logging"] and "logBucket" in properties["logging"] and \
                    properties['logging']['logBucket']:
                results.append(self._generate_results(self.execution_id, self.project_id, self.service_name,
                                                      test_name, bucket_name, self.region, False))
            else:
                results.append(self._generate_results(self.execution_id, self.project_id, self.service_name,
                                                      test_name, bucket_name, self.region, True))
        return results

    def global_test_bucket_versioning_should_be_enabled(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for bucket in self.all_bucket:
            bucket_name = bucket.name
            if hasattr(bucket, "versioning_enabled"):
                results.append(self._generate_results(self.execution_id, self.project_id, self.service_name,
                                                      test_name, bucket_name, self.region,
                                                      False if bucket.versioning_enabled
                                                      else True))
        return results

    def run(self):
        global_tests, regional_tests = self._get_all_tests()
        if self.region != "global":
            pass
        if self.region == "global":
            self.cloud_storage_init()
            self.run_test(self.service_name, global_tests, self.shipper, self.region)
