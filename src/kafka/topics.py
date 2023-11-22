import os
import argparse
import logging
from common.utils import load_file
from typing import List
from kafka.admin import (
    KafkaAdminClient, NewTopic
)
from kafka.errors import (
    UnknownTopicOrPartitionError
)


class KafkaAdmin:
    def __init__(self, config: str):
        self.__config = load_file(config)
        self.__kf_config = self.__config.get("kafka")
        self.admin = KafkaAdminClient(
            bootstrap_servers=[
               f"{self.__kf_config.get('broker_host')}:{self.__kf_config.get('broker_port')}"   # noqa
            ],
            client_id='admin'
        )
        logging.basicConfig(level=logging.INFO)
        logging.info(self.__kf_config)

    def list_topics(self):
        return self.admin.list_topics()

    def create_topics(self, topic_list: List):
        assert topic_list is not None, "Topic list is not defined!"
        assert len(topic_list) > 0, "Topic list is empty!"

        # identify the new topics; skip topic creation if it is already existed
        new_topics = []
        for item in topic_list:
            found = False
            for name in self.admin.list_topics():
                if name == item.get("topic_name"):
                    found = True
                    break
            if not found:
                new_topics.append(item)

        topics = []
        for topic in new_topics:
            topic_name = topic.get("topic_name")
            topics.append(NewTopic(
                          name=topic_name,
                          num_partitions=topic.get("num_partitions"),
                          replication_factor=topic.get("replication_factor")))
            print(f"Added topic '{topic_name}'")
        self.admin.create_topics(new_topics=topics, validate_only=False)

    def delete_topics(self, topic_names: List):
        try:
            self.admin.delete_topics(topics=topic_names)
            logging.info("Successfully deleted topic")
        except UnknownTopicOrPartitionError as e:
            logging.error("Topic doesn't exist", e)
        except Exception as e:
            logging.error("Failed to delete topic:", e)


if __name__ == "__main__":
    cwd = os.getcwd()
    conf_path = f"{cwd}/conf"

    parser = argparse.ArgumentParser(description='Kafka Console Consumer')
    parser.add_argument('-c', '--create', help='create topic, Y or N')
    parser.add_argument('-r', '--remove', help='remove topic, Y or N')
    args = vars(parser.parse_args())

    create = args.get('create')
    delete = args.get('remove')

    action = None
    if create is not None and create.upper() == "Y" and delete is None:
        action = "create"
    elif delete is not None and delete.upper() == "Y" and create is None:
        action = "remove"
    else:
        raise Exception("Cannot proceed: No acction specified")

    # create topics if not already exist
    admin = KafkaAdmin(config=f"{conf_path}/test_config.json")

    topic_names = ["companies", "acq_companies", "persons"]
    topics = [
        {"topic_name": topic_names[0],
         "num_partitions": 1, "replication_factor": 1},
        {"topic_name": topic_names[1],
         "num_partitions": 1, "replication_factor": 1},
        {"topic_name": topic_names[2],
         "num_partitions": 1, "replication_factor": 1},
    ]

    if action == "create":
        admin.create_topics(topics)
        logging.info(f"topics: {admin.list_topics()}")
    elif action == "remove":
        admin.delete_topics(topics)
        logging.info(f"topics: {admin.list_topics()}")
