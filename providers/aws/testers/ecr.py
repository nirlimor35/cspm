import json
import docker
import base64
import inspect
import subprocess
from providers.aws.aws import AWSTesters

"""
ECR repositories should be encrypted with customer managed AWS KMS keys
ECR public repositories should be tagged
"""


class Service(AWSTesters):
    def __init__(self, execution_id, client, account_id, region, shipper):
        self.service_name = "ECR"
        self.execution_id = execution_id
        self.region = region
        self.account_id = account_id
        self.shipper = shipper.send_bulk
        self.ecr_client = client("ecr", self.region)
        self.all_tests, self.test_names = self._get_all_tests()
        self.describe_private_repos = None
        self.all_repositories_names = None

    def _ecr_init(self):
        describe_private_repos = self.ecr_client.describe_repositories()
        if "repositories" in describe_private_repos:
            self.describe_private_repos = describe_private_repos["repositories"]
            if len(describe_private_repos["repositories"]) > 0:
                self.all_repositories_names = [repo["repositoryName"] for repo in self.describe_private_repos]

    def test_private_repositories_should_have_image_scanning_configured(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for private_repo in self.describe_private_repos:
            repository_name = private_repo["repositoryName"]
            if "imageScanningConfiguration" in private_repo \
                    and "scanOnPush" in private_repo["imageScanningConfiguration"] \
                    and private_repo["imageScanningConfiguration"]["scanOnPush"]:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name,
                                                      repository_name, self.region, False))
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name,
                                                      repository_name, self.region, True))
        return results

    def test_private_repositories_should_have_tag_immutability_configured(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for private_repo in self.describe_private_repos:
            repository_name = private_repo["repositoryName"]
            if "imageTagMutability" in private_repo:
                if private_repo["imageTagMutability"] == "MUTABLE":
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          repository_name, self.region, True))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          repository_name, self.region, False))
        return results

    def test_repositories_should_have_at_least_one_lifecycle_policy_configured(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for private_repo in self.describe_private_repos:
            repository_name = private_repo["repositoryName"]
            repos_lifecycle_policy = self.ecr_client.get_lifecycle_policy(repositoryName=repository_name)
            if "lifecyclePolicyText" in repos_lifecycle_policy:
                try:
                    lifecycle_policy_text = json.loads(repos_lifecycle_policy["lifecyclePolicyText"])
                    additional_data = {"lifecycle_policy": lifecycle_policy_text}
                    if "rules" in lifecycle_policy_text and len(lifecycle_policy_text["rules"]) > 1:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              repository_name, self.region, False, additional_data))
                    else:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              repository_name, self.region, True, additional_data))
                except json.JSONDecodeError as e:
                    print(f"ERROR ⭕️ {self.service_name} :: Failed to load JSON - {e}")
            else:
                results.append(self._generate_results(self.execution_id,
                                                      self.account_id, self.service_name, test_name,
                                                      repository_name, self.region, True,
                                                      {"lifecycle_policy": "no policy found"}))
        return results

    def test_scanning_should_be_enabled_with_amazon_inspector(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        registry_scanning_configuration = self.ecr_client.get_registry_scanning_configuration()
        if "scanningConfiguration" in registry_scanning_configuration \
                and "scanType" in registry_scanning_configuration["scanningConfiguration"] \
                and registry_scanning_configuration["scanningConfiguration"]["scanType"] == "ENHANCED":
            results.append(self._generate_results(self.execution_id,
                                                  self.account_id, self.service_name, test_name,
                                                  "ecr", self.region, False))
        else:
            results.append(self._generate_results(self.execution_id,
                                                  self.account_id, self.service_name, test_name,
                                                  "ecr", self.region, True))
        return results

    def test_images_vulnerability_scan(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        if self.all_repositories_names and len(self.all_repositories_names) > 0:
            for repository_name in self.all_repositories_names:
                auth_response = self.ecr_client.get_authorization_token()
                auth_data = auth_response["authorizationData"][0]
                token = base64.b64decode(auth_data["authorizationToken"]).decode()
                username, password = token.split(":")
                registry = auth_data["proxyEndpoint"].replace("https://", "")

                docker_client = docker.from_env()
                docker_client.login(username=username, password=password, registry=registry)
                full_image_name = f"{registry}/{repository_name}:latest"
                docker_client.images.pull(full_image_name)

                cmd = ["grype", full_image_name, "--output", "json"]
                completed_process = subprocess.run(cmd, capture_output=True, text=True)
                findings = None
                if completed_process.returncode == 0:
                    try:
                        parsed_output = json.loads(completed_process.stdout)
                        if "matches" in parsed_output:
                            findings = parsed_output["matches"]
                    except json.JSONDecodeError as e:
                        print(f"ERROR ⭕️ {self.service_name} :: Failed to parse output as JSON - {e}")
                else:
                    print(
                        f"""ERROR ⭕️ {self.service_name} :: Grype failed with error code {completed_process.returncode}:
{completed_process.stderr}""")
                docker.from_env().images.remove(full_image_name)

                if findings and len(findings) > 0:
                    for cur_fin in findings:
                        additional_data = {
                            "binary": cur_fin["artifact"]["name"],
                            "cur_version": cur_fin["artifact"]["version"],
                            "cve_id": cur_fin["vulnerability"]["id"],
                            "url": cur_fin["vulnerability"]["dataSource"],
                            "severity": cur_fin["vulnerability"]["severity"],
                            "state": cur_fin["vulnerability"]["fix"]["state"],
                            "fixed_versions": cur_fin["vulnerability"]["fix"]["versions"]
                        }
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              repository_name, self.region, True, additional_data))
        return results

    def run(self):
        global_tests, regional_tests = self._get_all_tests()
        if self.region != "global":
            self._ecr_init()
            self.run_test(self.service_name, regional_tests, self.shipper, self.region)
        if self.region == "global":
            self.run_test(self.service_name, global_tests, self.shipper, self.region)
