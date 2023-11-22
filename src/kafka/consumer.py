import os
import json
import argparse
import logging
import datetime as dt
from common.utils import load_file
from kafka import KafkaConsumer


class Consumer:
    def __init__(self, config: str, topic: str,
                 group_id: str = None, offset: str = None):
        self.__config = load_file(config)
        self.__kf_config = self.__config.get("kafka")
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=[
              f"{self.__kf_config.get('broker_host')}:{self.__kf_config.get('broker_port')}"   # noqa
            ],
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset=offset,
            consumer_timeout_ms=1000,
            group_id=group_id,
            enable_auto_commit=False,
            auto_commit_interval_ms=1000
        )
        logging.basicConfig(level=logging.INFO)
        logging.info(f'Initialized Kafka consumer at {dt.datetime.utcnow()}')
        logging.info(self.__kf_config)

    def poll(self):
        while True:
            try:
                # timeout in millis , here set to 1 min
                records = self.consumer.poll(60 * 1000)

                record_list = []
                for tp, consumer_records in records.items():
                    for consumer_record in consumer_records:
                        record_list.append(consumer_record.value)
                print(record_list)
            except Exception as e:
                logging.error("Failed while polling data:", e)
                raise


if __name__ == "__main__":
    cwd = os.getcwd()
    data_path = f"{cwd}/data"
    conf_path = f"{cwd}/conf"

    parser = argparse.ArgumentParser(description='Kafka Console Consumer')
    parser.add_argument('-t', '--topic', help='topic', required=True)
    parser.add_argument('-o', '--offset', help='offset', default="latest")
    parser.add_argument('-g', '--group', help='group', default=None)
    args = vars(parser.parse_args())

    topic = args.get('topic')
    offset = args.get('offset', '')
    group = args.get('group', '')

    # poll data from kafka
    # By default, kafka python starts from the last offset,
    #    ie., read only the new messages
    # To read from the beginning, set offset='earliest'
    console = Consumer(
        config=f"{conf_path}/test_config.json",
        topic=topic, group_id=group, offset=offset
    )
    console.poll()
