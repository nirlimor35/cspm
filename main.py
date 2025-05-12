import os
import yaml
import uuid
import pkgutil
import importlib
import concurrent.futures
from datetime import datetime
from providers.gcp import GCP
from providers.aws.aws import AWS
from utils.coralogix import SendToCoralogix


class CSPM:
    def __init__(self):
        self.code_dir = os.path.dirname(__file__)
        self.config_file_path = os.path.join(self.code_dir, "config.yaml")
        self.platform = self.parameters_validator("PLATFORM").lower()
        self.cx_endpoint = self.coralogix_endpoint_convert(self.parameters_validator("CX_ENDPOINT"))
        self.cx_api_key = self.parameters_validator("CX_API_KEY")
        self.cloud_provider = self.parameters_validator("CLOUD_PROVIDER").lower()
        self.profile = self.parameters_validator("AWS_PROFILE")
        self.regions_to_scan = self.parameters_validator("REGIONS")
        self.user_selected_services = self.parameters_validator("SERVICES")

    def parameters_validator(self, param):
        config_file = self.config_file_path
        if os.path.isfile(config_file):
            with open(config_file, 'r') as file:
                config_file = yaml.safe_load(file.read())
            try:
                if param in config_file \
                        and config_file[param] \
                        and len(config_file[param]) > 0:
                    return config_file[param]
                else:
                    os.getenv(param)
            except:
                return None
        else:
            return os.getenv(param)

    def init_aws(self):
        aws = AWS(profile=self.profile)
        client = aws.get_client
        aws_regions = self.regions_to_scan
        if type(aws_regions) is str:
            if aws_regions and len(aws_regions) > 0:
                regions = [region.strip() for region in aws_regions.split(",")]
            else:
                regions = aws.get_available_regions(client=client)
        elif type(aws_regions) is list:
            regions = aws_regions
        else:
            regions = aws.get_available_regions(client=client)

        if "global" not in regions:
            regions.append("global")
        account_id = client("sts").get_caller_identity()["Account"]
        return client, regions, account_id

    def init_gcp(self):
        import google.auth
        credentials, project_id = google.auth.default()
        gcp_regions = self.regions_to_scan
        all_regions = GCP.get_available_regions(credentials, project_id)

        if gcp_regions and len(gcp_regions) > 0:
            if type(gcp_regions) is str:
                regions = [region.strip() for region in gcp_regions.split(",") if region in all_regions]
            elif type(gcp_regions) is list:
                for region in gcp_regions:
                    if region not in all_regions:
                        print(f"ERROR ⭕ Unknown GCP region '{region}' - stopping")
                        exit(8)
                    else:
                        regions = gcp_regions
            else:
                regions = all_regions
        else:
            regions = all_regions

        if "global" not in regions:
            regions.append("global")
        return credentials, project_id, regions


    def load_services_for_provider(self):
        services = []
        all_services = {}
        testers_dir = os.path.join(self.code_dir, "providers", self.cloud_provider, "testers")
        user_selected_services = None

        def load_module(module_to_load):
            if hasattr(module_to_load, 'Service'):
                service_class = getattr(module_to_load, 'Service')
                return service_class

        user_selected_services_env = self.user_selected_services
        if type(user_selected_services_env) is str:
            if user_selected_services_env and len(user_selected_services_env) > 0:
                user_selected_services = [service.strip().lower() for service in user_selected_services_env.split(",")]
        elif type(user_selected_services_env) is list:
            user_selected_services = self.user_selected_services
        for finder, module_name, is_pkg in pkgutil.iter_modules([testers_dir]):
            all_services.update({module_name: f"providers.{self.cloud_provider}.testers.{module_name}"})

        if user_selected_services and len(user_selected_services) > 0:
            for service in user_selected_services:
                if service in all_services:
                    module = importlib.import_module(all_services[service])
                    services.append(load_module(module))
                else:
                    t = [test.split(".")[0] for test in os.listdir(testers_dir) if not test.startswith("_")]
                    print(f"ERROR ⭕ Unknown service '{service}' for {self.cloud_provider.upper()}\n\nAvailable tests:")
                    print(yaml.safe_dump(t))
                    exit(9)
        else:
            for name, cur_module in all_services.items():
                module = importlib.import_module(cur_module)
                services.append(load_module(module))

        return services

    @staticmethod
    def coralogix_endpoint_convert(endpoint):
        if endpoint == "EU1":
            return "coralogix.com"
        elif endpoint == "EU2":
            return "eu2.coralogix.com"
        elif endpoint == "US1":
            return "coralogix.us"
        elif endpoint == "US2":
            return "cx498.coralogix.com"
        elif endpoint == "AP1":
            return "coralogix.in"
        elif endpoint == "AP2":
            return "coralogixsg.com"
        elif endpoint == "AP3":
            return "ap3.coralogix.com"
        else:
            return "coralogix.com"

    @staticmethod
    def run_aws_service(current_execution_id: str, service_class, client, account_id: str, region: str, shipper: SendToCoralogix):
        service_class(
            execution_id=current_execution_id,
            client=client,
            region=region,
            account_id=account_id,
            shipper=shipper
        ).run()

    @staticmethod
    def run_gcp_service(current_execution_id: str, service_class, credentials, project_id, region):
        service_class(
            execution_id=current_execution_id,
            credentials=credentials,
            project_id=project_id,
            region=region
        ).run()

    @staticmethod
    def create_execution_id():
        return str(uuid.uuid4())

    def main(self):
        current_execution_id = self.create_execution_id()
        print(f" INFO 🔵 Starting scan in {self.cloud_provider.upper()} 🔎\n")
        start_timestamp = datetime.now()
        discovered_services = self.load_services_for_provider()

        future_to_task = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for service_class in discovered_services:
                cur_service_name = str(service_class).split(".")[3].upper()

                special_names = ["CloudTrail", "GuardDuty", "Route53", "Secret Manager", "Cloud Storage", "Logging"]
                for special_name in special_names:
                    if cur_service_name == special_name.upper().replace(" ", "_"):
                        cur_service_name = special_name

                if self.platform == "coralogix":
                    shipper = SendToCoralogix(
                        endpoint=self.cx_endpoint,
                        api_key=self.cx_api_key,
                        application="CSPM",
                        subsystem=cur_service_name
                    )

            print(f" INFO 🔵 {cur_service_name} :: Initiating...")

            if self.cloud_provider == "aws":
                client, regions, account_id = self.init_aws()
                for region in regions:
                    future = executor.submit(
                        self.run_aws_service,
                        current_execution_id,
                        service_class,
                        client,
                        account_id,
                        region,
                        shipper
                    )
                    future_to_task[future] = (cur_service_name, region)

            elif self.cloud_provider == "gcp":
                credentials, project_id, regions = self.init_gcp()
                for region in regions:
                    future = executor.submit(
                        self.run_gcp_service,
                        current_execution_id,
                        service_class,
                        credentials,
                        project_id,
                        region
                    )
                    future_to_task[future] = (cur_service_name, region)

        duration = (datetime.now() - start_timestamp).total_seconds()
        print(f"\n✅ Scan completed in {duration} seconds")
