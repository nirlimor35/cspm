import inspect
from google.cloud import compute_v1
from providers import Testers


class Service(Testers):
    def __init__(self, execution_id, credentials, project_id, region, shipper):
        self.service_name = "Compute"
        self.execution_id = execution_id
        self.project_id = project_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.instances_client = compute_v1.InstancesClient(credentials=credentials)
        self.image_client = compute_v1.ImagesClient(credentials=credentials)
        self.images = []

    def compute_instance_init(self):
        pass

    def compute_images_init(self):
        image_client = compute_v1.ImagesClient()
        request = compute_v1.ListImagesRequest(project=self.project_id)
        self.images = list(image_client.list(request=request))

    @staticmethod
    def _is_public_iam(policy, permissions):
        for binding in policy.bindings:
            if any(member in permissions for member in binding.members):
                return True
        return False

    def global_test_vm_images_should_be_private(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]
        results = []
        for image in self.images:
            try:
                policy = self.image_client.get_iam_policy(project=self.project_id, resource=image.name)
                permissions_to_check = {"allUsers", "allAuthenticatedUsers"}
                if self._is_public_iam(policy, permissions_to_check):
                    results.append(self._generate_results(self.execution_id, self.project_id, self.service_name,
                                                          test_name, image.name, self.region, True))
                else:
                    results.append(self._generate_results(self.execution_id, self.project_id, self.service_name,
                                                          test_name, image.name, self.region, False))
            except Exception as e:
                print(f"ERROR :: Failed to check image '{image.name}' - {e}")
        return results

    def run(self):
        global_tests, regional_tests = self._get_all_tests()
        if self.region != "global":
            pass
            # self.compute_instance_init()
        if self.region == "global":
            self.compute_images_init()
            self.run_test(self.service_name, global_tests, self.shipper, self.region)


