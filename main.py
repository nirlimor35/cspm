import yaml
import pkgutil
import os.path
import importlib
import providers
import concurrent.futures
from datetime import datetime
from providers.aws.aws import AWS


class CSPM:
    def __init__(self, platform="coralogix", profile=None):
        self.platform = platform
        self.code_dir = os.path.dirname(__file__)
        self.cloud_provider = providers.get_cloud_provider()
        self.client = None
        self.regions = None
        self.profile = profile

    def init_aws(self):
        aws_service = AWS(self.profile)
        self.client = aws_service.get_client
        self.regions = aws_service.get_available_regions(client=self.client)

    def load_services_for_provider(self):
        services = []
        services_names = []
        testers_dir = os.path.join(self.code_dir, "providers", self.cloud_provider, "testers")

        for finder, module_name, is_pkg in pkgutil.iter_modules([testers_dir]):
            services_names.append(module_name)
            full_module_name = f"providers.{self.cloud_provider}.testers.{module_name}"
            module = importlib.import_module(full_module_name)
            if hasattr(module, 'Service'):
                service_class = getattr(module, 'Service')
                services.append(service_class)
        return services

    def run_service(self, service_class, region):
        service_class(client=self.client, region=region).run()

    def main(self):
        if self.cloud_provider == "aws":
            start_timestamp = datetime.now()
            print("INFO :: Starting scan in AWS")
            self.init_aws()
            print(f"Available regions:\n{yaml.dump(self.regions)}")
            discovered_services = self.load_services_for_provider()
            services_classes = discovered_services
            services_names = [str(service).split(".")[3] for service in discovered_services]
            print(f"Available Services:\n{yaml.dump(services_names)}")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for service_class in services_classes:
                    print(f"INFO :: {str(service_class).split(".")[3].upper()} :: Initiating...")
                    for region in self.regions:
                        futures.append(executor.submit(self.run_service, service_class, region))

            duration = (datetime.now() - start_timestamp).total_seconds()
            print(f"\n✅ Scan completed in {duration} seconds")


CSPM(profile="external-test").main()
