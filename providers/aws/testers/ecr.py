import json
import docker
import base64
import subprocess


class Service:
    def __init__(self, client, region):
        self.service_name = "ECR"
        self.region = region
        self.client = client("ecr", self.region)

    def ecr_and_docker_auth(self):
        auth_response = self.client.get_authorization_token()
        auth_data = auth_response["authorizationData"][0]
        auth_token = auth_data["authorizationToken"]
        proxy_endpoint = auth_data["proxyEndpoint"]

        decoded_auth_token = base64.b64decode(auth_token).decode("utf-8")
        username, password = decoded_auth_token.split(":")

        docker_client = docker.from_env()
        docker_client.login(username=username, password=password, registry=proxy_endpoint)
        return proxy_endpoint.replace("https://", "")

    def get_image_findings(self, repository_name, registry, tag="latest"):
        full_image_name = f"{registry}/{repository_name}:{tag}"
        cmd = ["grype", full_image_name, "-q", "--output", "json"]
        completed_process = subprocess.run(cmd, capture_output=True, text=True)

        if completed_process.returncode != 0:
            message = f"ERROR :: {self.service_name} :: Grype failed to run - {completed_process.stderr}"
            print(message)
            raise RuntimeError(message)

        try:
            parsed_output = json.loads(completed_process.stdout)
        except json.JSONDecodeError as e:
            message = f"ERROR :: {self.service_name} :: Failed to parse output as JSON - {e}"
            print(message)
            raise ValueError(message)
        if "matches" in parsed_output:
            return parsed_output["matches"]

    def run(self):
        all_repositories = self.client.describe_repositories()
        all_repositories_names = [repo["repositoryName"] for repo in all_repositories["repositories"]]
        registry = self.ecr_and_docker_auth()
        results = {}
        if len(all_repositories_names) > 0:
            print(f"INFO :: {self.service_name} :: Found {len(all_repositories_names)} repositor{'ies' if len(all_repositories_names) > 1 else 'y'} in {self.region}")
            for repository_name in all_repositories_names:
                findings = self.get_image_findings(repository_name, registry)
                cur_filtered_finding = []
                for cur_fin in findings:
                    cur_filtered_finding.append({
                        "binary": cur_fin["artifact"]["name"],
                        "cur_version": cur_fin["artifact"]["version"],
                        "cve_id": cur_fin["vulnerability"]["id"],
                        "url": cur_fin["vulnerability"]["dataSource"],
                        "severity": cur_fin["vulnerability"]["severity"],
                        "state": cur_fin["vulnerability"]["fix"]["state"],
                        "fixed_versions": cur_fin["vulnerability"]["fix"]["versions"]
                    })
                results.update({repository_name: cur_filtered_finding})
            return results
        else:
            print(f"INFO :: {self.service_name} :: No repositories found in region {self.region}")
