import inspect
from providers.aws.aws import AWSTesters

"""
RDS snapshot should be private
IAM authentication should be configured for RDS instances
RDS instances should have automatic backups enabled
IAM authentication should be configured for RDS clusters
RDS automatic minor version upgrades should be enabled
RDS DB clusters should be configured for multiple Availability Zones
RDS DB clusters should be configured to copy tags to snapshots
RDS DB instances should be configured to copy tags to snapshots
RDS instances should be deployed in a VPC
Existing RDS event notification subscriptions should be configured for critical cluster events
RDS DB Instances should prohibit public access, as determined by the PubliclyAccessible configuration
Existing RDS event notification subscriptions should be configured for critical database instance events
An RDS event notifications subscription should be configured for critical database parameter group events
An RDS event notifications subscription should be configured for critical database security group events
RDS instances should not use a database engine default port
RDS Database Clusters should use a custom administrator username
RDS database instances should use a custom administrator username
RDS DB instances should be protected by a backup plan
RDS DB clusters should be encrypted at rest
RDS DB clusters should be tagged
RDS DB cluster snapshots should be tagged
RDS DB instances should have encryption at-rest enabled
RDS DB instances should be tagged
RDS DB security groups should be tagged
RDS DB snapshots should be tagged
RDS DB subnet groups should be tagged
RDS DB clusters should have automatic minor version upgrade enabled
RDS for PostgreSQL DB instances should publish logs to CloudWatch Logs
RDS for PostgreSQL DB instances should be encrypted in transit
RDS for MySQL DB instances should be encrypted in transit
RDS cluster snapshots and database snapshots should be encrypted at rest
RDS for SQL Server DB instances should publish logs to CloudWatch Logs
RDS DB instances should be configured with multiple Availability Zones
Enhanced monitoring should be configured for RDS DB instances
RDS clusters should have deletion protection enabled
RDS DB instances should have deletion protection enabled
RDS DB instances should publish logs to CloudWatch Logs
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
