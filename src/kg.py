import os
import json
import logging
from typing import Dict
from pprint import pprint
from neo4j import GraphDatabase
# from pyvis.network import Network

from sourcer import (
    DataSourcer,
    CompaniesSourcer,
    AcquiredCompaniesSourcer,
    EmployedPersonsSourcer
)

# TODO: unit tests
# TODO: data quality checks
#       (basic logic checks, missing or incomplete relationship)


class KnowledgeGraph:
    def __init__(self, config: str):
        self.__config = KnowledgeGraph.config(config)
        self.__db_config = self.__config.get("neo4j")
        self.__uri = "bolt://{}:{}".format(
                        self.__db_config.get("host"),
                        self.__db_config.get("port"))
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(
                               self.__uri,
                               auth=(self.__db_config.get("user"),
                                     self.__db_config.get("password")))
            logging.info("Connected to database")
        except Exception as e:
            logging.error("Failed to connect to database; \
                           cannot create the driver:", e)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def load_data(self, sourcer: DataSourcer, name: str, pkey: str):

        assert self.__driver is not None, "Driver not initialized!"

        try:
            # managed transaction with Session.execute_read()
            # method takes a transaction function callback;
            # responsible for actually carrying out the queries 
            #     and processing the result
            with self.__driver.session(
                    database=self.__db_config.get("database")) as session:
                batch = sourcer.get_data()
                pprint(batch)
                callablefunc = sourcer.get_updater
                pid = session.execute_write(callablefunc, batch)
                print(f"Added {name} {pkey} {pid}")

        except Exception as e:
            logging.error(f"Failed to load batch to database; \
                           batch size {len(batch)}:", e)

    def write_query_to_file(self, file: str):
        def get_data(session):
            # create empty dataset
            result = session.run("CALL apoc.export.json.all( \
                                         null, {stream: true})")
            return result.data()

        assert self.__driver is not None, "Driver not initialized!"

        with self.__driver.session(
                database=self.__db_config.get("database")) as session:
            data = session.execute_read(get_data)
            with open(file, "w") as f:
                for chunk in data:
                    logging.info("writing:", chunk)
                    f.write(chunk["data"])

    def close(self):
        # must close the driver connection when done
        if self.__driver is not None:
            self.__driver.close()

    @staticmethod
    def config(filepath: str) -> Dict:
        if filepath is None or not (os.path.exists(filepath)):
            raise Exception("Failed to load file; invalid file (=$filepath)")

        with open(filepath) as fh:
            data = json.load(fh)
        return data


if __name__ == "__main__":
    # load companies from json file
    comp_sourcer = CompaniesSourcer()
    companies = comp_sourcer.collect_data(file="../data/companies_100.json")
    logging.info(f"Loaded {len(companies)} companies")

    # load acquired_companies from json file
    acq_sourcer = AcquiredCompaniesSourcer()
    acq_companies = acq_sourcer.collect_data(file="../data/company_acquisition_9.json")   # noqa
    logging.info(f"Loaded {len(acq_companies)} acquired companies")

    # load employees from json file
    emp_sourcer = EmployedPersonsSourcer()
    employees = emp_sourcer.collect_data(file="../data/person_employment_25.json")   # noqa
    logging.info(f"Loaded {len(employees)} employees")

    # connect to our neo4j database
    with KnowledgeGraph(config="../conf/test_config.json") as kg:
        kg.load_data(sourcer=comp_sourcer, name="org", pkey="org_id")
        kg.load_data(sourcer=acq_sourcer, name="acquired_org", pkey="sub_id")
        kg.load_data(sourcer=emp_sourcer, name="person", pkey="person_id")