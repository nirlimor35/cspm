import json
import docker
import base64
import inspect
import subprocess
from providers.aws.aws import AWSTesters, AWS

"""
ECR private repositories should have image scanning configured
ECR private repositories should have tag immutability configured
ECR repositories should have at least one lifecycle policy configured
ECR public repositories should be tagged
ECR repositories should be encrypted with customer managed AWS KMS keys
EKS clusters should use encrypted Kubernetes secrets
Amazon Inspector ECR scanning should be enabled
IAM customer managed policies should not allow decryption actions on all KMS keys
IAM principals should not have IAM inline policies that allow decryption actions on all KMS keys
"""


class Service(AWSTesters, AWS):
    def __init__(self, execution_id, client, account_id, region, shipper):
        super().__init__()
        self.service_name = "ECR"
        self.execution_id = execution_id
        self.region = region
        self.account_id = account_id
        self.shipper = shipper.send_bulk
        self.client = client("ecr", self.region)
        self.all_tests, self.test_names = self._get_all_tests()

    def _ecr_and_docker_auth(self):
        auth_response = self.client.get_authorization_token()
        auth_data = auth_response["authorizationData"][0]
        auth_token = auth_data["authorizationToken"]
        proxy_endpoint = auth_data["proxyEndpoint"]

        decoded_auth_token = base64.b64decode(auth_token).decode("utf-8")
        username, password = decoded_auth_token.split(":")

        docker_client = docker.from_env()
        docker_client.login(username=username, password=password, registry=proxy_endpoint)
        return proxy_endpoint.replace("https://", "")

    def _get_image_findings(self, repository_name, registry, tag="latest"):
        full_image_name = f"{registry}/{repository_name}:{tag}"
        cmd = ["grype", full_image_name, "-q", "--output", "json"]
        completed_process = subprocess.run(cmd, capture_output=True, text=True)

        if completed_process.returncode != 0:
            message = f"ERROR ⭕️ {self.service_name} :: Grype failed to run - {completed_process.stderr}"
            print(message)
            raise RuntimeError(message)

        try:
            parsed_output = json.loads(completed_process.stdout)
        except json.JSONDecodeError as e:
            message = f"ERROR ⭕️ {self.service_name} :: Failed to parse output as JSON - {e}"
            print(message)
            raise ValueError(message)
        if "matches" in parsed_output:
            return parsed_output["matches"]

    def test_images_vulnerability_scan(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        all_repositories = self.client.describe_repositories()
        all_repositories_names = [repo["repositoryName"] for repo in all_repositories["repositories"]]
        registry = self._ecr_and_docker_auth()
        results = []
        if len(all_repositories_names) > 0:
            for repository_name in all_repositories_names:
                findings = self._get_image_findings(repository_name, registry)
                cur_filtered_finding = []

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
                        cur_filtered_finding.append(additional_data)
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              repository_name, self.region, True, additional_data))

        return results

    def run(self):
        if self.region != "global":
            results = []
            try:
                for cur_test in self.all_tests:
                    cur_results = cur_test()
                    if type(cur_results) is list:
                        for cur_result in cur_results:
                            results.append(cur_result)
                    else:
                        results.append(cur_results)
                if results and len(results) > 0:
                    print(
                        f" INFO 🔵 {self.service_name} :: 📨 Sending {len(results)} logs to Coralogix for region {self.region}")
                    self.shipper(results)
                else:
                    print(f" INFO 🔵 {self.service_name} :: No logs found for region {self.region}")
            except Exception as e:
                print(e)
