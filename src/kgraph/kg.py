import os
import logging
from common.utils import load_file
from pprint import pprint
from neo4j import GraphDatabase
# from pyvis.network import Network

from kgraph.sourcer import (
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
        self.__config = load_file(config)
        self.__db_config = self.__config.get("neo4j")
        self.__uri = "bolt://{}:{}".format(
                        self.__db_config.get("host"),
                        self.__db_config.get("port"))
        self.__driver = None
        logging.basicConfig(level=logging.INFO)

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


if __name__ == "__main__":
    cwd = os.getcwd()
    data_path = f"{cwd}/data"
    conf_path = f"{cwd}/conf"

    # load companies from json file
    comp_sourcer = CompaniesSourcer()
    companies = comp_sourcer.collect_data(file=f"{data_path}/companies_100.json")   # noqa
    logging.info(f"Loaded {len(companies)} companies")

    # load acquired_companies from json file
    acq_sourcer = AcquiredCompaniesSourcer()
    acq_companies = acq_sourcer.collect_data(file=f"{data_path}/company_acquisition_9.json")   # noqa
    logging.info(f"Loaded {len(acq_companies)} acquired companies")

    # load employees from json file
    emp_sourcer = EmployedPersonsSourcer()
    employees = emp_sourcer.collect_data(file=f"{data_path}/person_employment_25.json")   # noqa
    logging.info(f"Loaded {len(employees)} employees")

    # connect to our neo4j database
    with KnowledgeGraph(config=f"{conf_path}/test_config.json") as kg:
        kg.load_data(sourcer=comp_sourcer, name="org", pkey="org_id")
        kg.load_data(sourcer=acq_sourcer, name="acquired_org", pkey="sub_id")
        kg.load_data(sourcer=emp_sourcer, name="person", pkey="person_id")
