from googleapiclient import discovery


class GCP:
    @staticmethod
    def get_available_regions(credentials, project_id):
        compute = discovery.build('compute', 'v1', credentials=credentials)
        request = compute.regions().list(project=project_id)
        response = request.execute()
        regions = [region["name"] for region in response.get('items', [])]
        return regions
