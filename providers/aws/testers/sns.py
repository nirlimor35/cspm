import json
import inspect
from providers import Testers


class Service(Testers):
    def __init__(self, execution_id, client, account_id, region, shipper):
        self.service_name = "SNS"
        self.execution_id = execution_id
        self.account_id = account_id
        self.region = region
        self.shipper = shipper.send_bulk
        self.sns_client = client("sns", self.region)
        self.list_topics = None

    def _init_sns(self):
        try:
            list_topics = self.sns_client.list_topics()
            if "Topics" in list_topics:
                self.list_topics = [topic["TopicArn"] for topic in list_topics["Topics"]]
        except Exception as e:
            print(f"ERROR ⭕ {self.service_name} :: {e}")

    def test_topics_should_be_tagged(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for topic_arn in self.list_topics:
            topic_name = str(topic_arn).split(f"{self.account_id}:")[1]
            try:
                topic_tags = self.sns_client.list_tags_for_resource(ResourceArn=topic_arn)

                if "Tags" in topic_tags and len(topic_tags["Tags"]) > 0:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          topic_name,
                                                          self.region, False, {"tags": topic_tags["Tags"]}))
                else:
                    results.append(self._generate_results(self.execution_id,
                                                          self.account_id, self.service_name, test_name,
                                                          topic_name,
                                                          self.region, True))
            except Exception as e:
                print(f"ERROR ⭕ {self.service_name} :: {e}")
        return results

    def test_topics_should_be_encrypted_at_rest_using_aws_kms(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for topic_arn in self.list_topics:
            topic_name = str(topic_arn).split(f"{self.account_id}:")[1]
            try:
                topic_attributes = self.sns_client.get_topic_attributes(TopicArn=topic_arn)
                if "Attributes" in topic_attributes:
                    cur_topic_attributes = topic_attributes["Attributes"]
                    if "KmsMasterKeyId" in cur_topic_attributes:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              topic_name,
                                                              self.region, False,
                                                              {"kmd_key_id": cur_topic_attributes["KmsMasterKeyId"]}))
                    else:
                        results.append(self._generate_results(self.execution_id,
                                                              self.account_id, self.service_name, test_name,
                                                              topic_name,
                                                              self.region, True))
            except Exception as e:
                print(f"ERROR ⭕ {self.service_name} :: {e}")
        return results

    def test_topic_access_policies_should_not_allow_public_access(self):
        test_name = inspect.currentframe().f_code.co_name.split("test_")[1]

        results = []
        for topic_arn in self.list_topics:
            topic_name = str(topic_arn).split(f"{self.account_id}:")[1]
            try:
                topic_attributes = self.sns_client.get_topic_attributes(TopicArn=topic_arn)
                if "Attributes" in topic_attributes:
                    cur_topic_attributes = topic_attributes["Attributes"]
                    if "Policy" in cur_topic_attributes:
                        topic_policy_statements = json.loads(cur_topic_attributes["Policy"])["Statement"]
                        principal_is_public = False
                        valid_condition = None

                        for topic_policy_document in topic_policy_statements:
                            cur_topic_policy_principal = topic_policy_document["Principal"]

                            for principal_option in ["AWS", "Service"]:
                                if principal_option in cur_topic_policy_principal:
                                    if cur_topic_policy_principal[principal_option] == "*":
                                        principal_is_public = True
                            if "Condition" in topic_policy_document \
                                    and "StringEquals" in topic_policy_document["Condition"] \
                                    and "AWS:SourceOwner" in topic_policy_document["Condition"]["StringEquals"] \
                                    and topic_policy_document["Condition"]["StringEquals"]["AWS:SourceOwner"] == self.account_id:
                                valid_condition = True

                        if (principal_is_public and valid_condition is None) \
                                or (principal_is_public and not valid_condition):
                            results.append(self._generate_results(self.execution_id,
                                                                  self.account_id, self.service_name, test_name,
                                                                  topic_name,
                                                                  self.region, True))
                        elif principal_is_public and valid_condition:
                            results.append(self._generate_results(self.execution_id,
                                                                  self.account_id, self.service_name, test_name,
                                                                  topic_name,
                                                                  self.region, False))
            except Exception as e:
                print(f"ERROR ⭕ {self.service_name} :: {e}")


        return results

    def run(self):
        global_tests, regional_tests = self._get_all_tests()
        if self.region != "global":
            self._init_sns()
            self.run_test(self.service_name, regional_tests, self.shipper, self.region)
        if self.region == "global":
            self.run_test(self.service_name, global_tests, self.shipper, self.region)
