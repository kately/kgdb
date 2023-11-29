import os
import json
import logging
import argparse
import datetime as dt
from time import sleep
from common.utils import load_file
from typing import List
from kafka import KafkaProducer


class Producer:
    def __init__(self, config: str):
        self.__config = load_file(config)
        self.__kf_config = self.__config.get("kafka")
        self.producer = KafkaProducer(
            bootstrap_servers=[
              f"{self.__kf_config.get('broker_host')}:{self.__kf_config.get('broker_port')}"   # noqa
            ]
        )
        logging.basicConfig(level=logging.INFO)
        logging.info(f'Initialized Kafka producer at {dt.datetime.utcnow()}')
        logging.info(self.__kf_config)

    def submit(self, topic: str, events: List) -> bool:
        batch = json.dumps(events, default=str).encode('utf-8')
        # send data to kafka
        self.producer.send(topic=topic, value=batch)
        # sleep to simulate a real-world interval
        sleep(0.5)
        return True

    def submit_file(self, topic: str, file: str) -> bool:
        events = load_file(file)
        return self.submit(topic=topic, events=events)


if __name__ == "__main__":
    cwd = os.getcwd()
    data_path = f"{cwd}/data"
    conf_path = f"{cwd}/conf"

    parser = argparse.ArgumentParser(description='Kafka Producer')
    parser.add_argument('-f', '--file', help='produce data by file')
    parser.add_argument('-s', '--sample', help='use default sample data')
    args = vars(parser.parse_args())

    file = args.get('file', None)
    sample = args.get('sample', None)

    if file is None and sample is None:
        raise Exception(
          "Which dataset to use: generate data by file or use default sample?"
        )

    # create producer to submit data to kafka
    producer = Producer(config=f"{conf_path}/test_config.json")

    # create default sample data set
    if sample and sample.upper() == "Y":
        companies_1 = [
          {"company_id": 1, "company_name": "ABC 01", "headcount": 200},
          {"company_id": 2, "company_name": "SUB ABC 01", "headcount": 20},
        ]

        companies_2 = [
          {"company_id": 2, "company_name": "SUB ABC 01", "headcount": 500},
          {"company_id": 3, "company_name": "SUB XYZ", "headcount": 30},
        ]

        acq_companies = [
          {"parent_company_id": 1, "acquired_company_id": 2,
           "merged_into_parent_company": True},
        ]

        persons = [
          {"company_id": 1, "person_id": 21, "employment_title": "Position A",
           "start_date": "2022-12-01 00:00:00", "end_date": None},
          {"company_id": 2, "person_id": 22, "employment_title": "Position X",
           "start_date": "2021-09-01 00:00:00", "end_date": None},
          {"company_id": 1, "person_id": 23, "employment_title": "Position D1",
           "start_date": "2019-05-01 00:00:00", "end_date": "2022-12-01"},
        ]

        # submit data to kafka
        producer.submit(topic="companies", events=companies_1)
        producer.submit(topic="companies", events=companies_2)
        # producer.submit(topic="acq_companies", events=acq_companies)
        # producer.submit(topic="persons", events=persons)

    if file and len(file) > 0:
        # submit data in file to kafka
        producer.submit_file(topic="companies", file=file)
