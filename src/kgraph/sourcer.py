import os
import logging
from common.utils import load_file
from typing import Dict
# from pprint import pprint

# TODO: unit tests
# TODO: data quality checks
#       (basic logic checks, missing or incomplete relationship)
# TODO: handle UTF-8, see company_id 10826297


class DataSourcer(object):
    def __init__(self, name: str):
        self.name = name
        self.dataset = dict()
        logging.basicConfig(level=logging.INFO)

    def collect_data(self, file: str):
        raise Exception("NotImplementedException")

    def get_data(self):
        return self.dataset

    @staticmethod
    def load_file(filepath: str) -> Dict:
        return load_file(filepath)


class CompaniesSourcer(DataSourcer):
    def __init__(self):
        super().__init__("companies")

    def collect_data(self, file: str):
        companies = DataSourcer.load_file(file)
        if companies and len(companies) == 0:
            raise Exception("Failed to data load; empty companies list")

        self.dataset = companies
        return self.dataset

    # @unit_of_work(timeout=10, metadata={"companies"})
    def get_updater(self, txn, batch):
        assert batch is not None, "Batch of entities is not defined!"
        assert len(batch) > 0, "Batch of entities is empty!"

        # create new node with given attributes, if not exists already
        # batch update with map
        result = txn.run(
            """
            WITH datetime({timezone: 'UTC'}) AS currentdt
            UNWIND $batch AS obj
            MERGE (o:Organization {company_id: obj.company_id})
            ON CREATE SET o = obj, o.created = currentdt
            ON MATCH SET o = obj, o.updated = currentdt
            RETURN o.org_id AS org_id
            """,
            batch=batch
        )
        return result


class AcquiredCompaniesSourcer(DataSourcer):
    def __init__(self):
        super().__init__("acquired_companies")

    def collect_data(self, file: str):
        acq_companies = DataSourcer.load_file(file)
        if acq_companies and len(acq_companies) == 0:
            raise Exception("Failed to data load; \
                             empty acquired companies list")

        self.dataset = acq_companies
        return self.dataset

    # @unit_of_work(timeout=10, metadata={"acquired-companies"})
    def get_updater(self, txn, batch):
        assert batch is not None, "Batch of entities is not defined!"
        assert len(batch) > 0, "Batch of entities is empty!"

        # create new node with given attributes, if not exists already
        # batch update with map
        result = txn.run(
            """
            // add or update subcompany
            WITH datetime({timezone: 'UTC'}) AS currentdt
            UNWIND $batch AS obj
            MERGE (s:Subsidiary {acquired_company_id: obj.acquired_company_id})
            ON CREATE SET s = obj, s.created = currentdt
            ON MATCH SET s = obj, s.updated = currentdt

            // find parent company ID and link to it
            // add or update relationship
            WITH s AS sub, datetime({timezone: 'UTC'}) AS currentdt
            MATCH (org:Organization {company_id: sub.parent_company_id})
            MERGE (org)-[r:ACQUIRED]->(sub)
            ON CREATE SET r.created = currentdt
            ON MATCH SET r.updated = currentdt

            RETURN org.company_id AS org_id,
                   sub.acquired_company_id AS sub_org_id
            """,
            batch=batch
        )

        # TODO: How to handle this scenario? Rollback? Should sub be added?
        # Parent organization is missing for subsidiary.
        # Parent company Id existed without company org node
        # Tag error for reprocessing when no data is available?

        return result


class EmployedPersonsSourcer(DataSourcer):
    def __init__(self):
        super().__init__("employees")

    def collect_data(self, file: str):
        persons = DataSourcer.load_file(file)
        if persons and len(persons) == 0:
            raise Exception("Failed to data load; empty persons list")

        self.dataset = persons
        return self.dataset

    # @unit_of_work(timeout=10, metadata={"employees"})
    def get_updater(self, txn, batch):
        assert batch is not None, "Batch of entities is not defined!"
        assert len(batch) > 0, "Batch of entities is empty!"

        # create new node with given attributes, if not exists already
        # add or update org and person relationship
        # TODO: Need to handle timezone on comparison
        result = txn.run(
            """
            // add or update person/employee
            WITH datetime({timezone: 'UTC'}) AS currentdt
            UNWIND $batch AS obj
            MERGE (p:Person {person_id: obj.person_id})
            ON CREATE SET p = obj, p.created = currentdt
            ON MATCH SET p = obj, p.updated = currentdt

            // add org and employee workAt relationship
            WITH p AS employee, datetime({timezone: 'UTC'}) AS currentdt
            MATCH (org:Organization {company_id: employee.company_id})
            MERGE (employee)-[r:WORKS_AT]->(org)
            ON CREATE SET r.created = currentdt
            ON MATCH SET r.updated = currentdt

            // remove workAt or ex- employment status
            // mark and update all companies along an employee employment path
            //   that were outside of one's current employment date range;
            //   update ex- relationship and update link.
            // 1) Add ex- relationship outside date range
            // 2) Remove the existing workAt relationship
            // 3) Skip/ignore update to relationship for null date values.
            WITH employee as p, date() AS current_date,
                 datetime({timezone: 'UTC'}) AS currentdt
            MATCH (emp:Person WHERE emp.person_id = p.person_id)
            MATCH (org:Organization)
            WHERE org.company_id = p.company_id AND
                  p.end_date IS NOT NULL AND
                  date(datetime(replace(p.end_date, " ", "T"))) < current_date
            MERGE (p)-[ex:EX_EMPLOYEE_OF]->(org)
            ON CREATE SET ex.created = currentdt
            ON MATCH SET ex.updated = currentdt
            // remove workAt relationship for ex-employee
            WITH p
            MATCH (p)-[r:WORKS_AT]->(org)
            DELETE r

            RETURN p.org_id AS org_id, p.person_id AS person_id
            """,
            batch=batch
        )

        # identify the employee current employment
        # TODO: How to handle this scenario? Rollback? Should sub be added?
        # Company is missing for employee.
        # Company Id existed without company org node
        # Tag error for reprocessing when no data is available?

        return result


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
