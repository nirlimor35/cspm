import os


def get_cloud_provider() -> str:
    provider = os.getenv("CLOUD_PROVIDER", "aws")
    if not provider:
        raise Exception("Missing required variable - 'CLOUD_PROVIDER'")
    else:
        return provider.lower()
