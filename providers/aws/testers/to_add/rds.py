import inspect
from providers.aws.aws import AWSTesters

"""
An RDS event notifications subscription should be configured for critical database parameter group events
An RDS event notifications subscription should be configured for critical database security group events
Enhanced monitoring should be configured for RDS DB instances
Existing RDS event notification subscriptions should be configured for critical cluster events
Existing RDS event notification subscriptions should be configured for critical database instance events
IAM authentication should be configured for RDS clusters
IAM authentication should be configured for RDS instances
RDS DB Instances should prohibit public access, as determined by the PubliclyAccessible configuration
RDS DB cluster snapshots should be tagged
RDS DB clusters should be configured for multiple Availability Zones
RDS DB clusters should be configured to copy tags to snapshots
RDS DB clusters should be encrypted at rest
RDS DB clusters should be tagged
RDS DB clusters should have automatic minor version upgrade enabled
RDS DB instances should be configured to copy tags to snapshots
RDS DB instances should be configured with multiple Availability Zones
RDS DB instances should be protected by a backup plan
RDS DB instances should be tagged
RDS DB instances should have deletion protection enabled
RDS DB instances should have encryption at-rest enabled
RDS DB instances should publish logs to CloudWatch Logs
RDS DB security groups should be tagged
RDS DB snapshots should be tagged
RDS DB subnet groups should be tagged
RDS Database Clusters should use a custom administrator username
RDS automatic minor version upgrades should be enabled
RDS cluster snapshots and database snapshots should be encrypted at rest
RDS clusters should have deletion protection enabled
RDS database instances should use a custom administrator username
RDS for MySQL DB instances should be encrypted in transit
RDS for PostgreSQL DB instances should be encrypted in transit
RDS for PostgreSQL DB instances should publish logs to CloudWatch Logs
RDS for SQL Server DB instances should publish logs to CloudWatch Logs
RDS instances should be deployed in a VPC
RDS instances should have automatic backups enabled
RDS instances should not use a database engine default port
RDS snapshot should be private
"""


class Service(AWSTesters):
    def __init__(self, execution_id, client, account_id, region, shipper):
        self.service_name = "RDS"
        self.execution_id = execution_id
        self.account_id = account_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.rds_client = client("rds")

    def run(self):
        global_tests, regional_tests = self._get_all_tests()
        if self.region != "global":
            self.run_test(self.service_name, regional_tests, self.shipper, self.region)
        if self.region == "global":
            self.run_test(self.service_name, global_tests, self.shipper, self.region)
