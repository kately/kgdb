import os
import json
import networkx as nx
from typing import Dict
from pprint import pprint
from pyvis.network import Network

# TODO: unit tests
# TODO: data quality checks
#       (basic logic checks, missing or incomplete relationship)


class KnowledgeGraph:
    def __init__(self):
        self.G = nx.Graph()

    @staticmethod
    def load_data(filepath: str) -> Dict:
        if filepath is None or not (os.path.exists(filepath)):
            raise Exception("Failed to data load; \
                             invalid input file (=$filepath)")

        with open(filepath) as fh:
            data = json.load(fh)
        # pprint(data)
        return data

    def init_companies(self, datafile: str):
        companies = KnowledgeGraph.load_data(datafile)
        if companies and len(companies) == 0:
            raise Exception("Failed to data load; empty companies list")

        self.all_companies = dict()
        for item in companies:
            self.all_companies.update({item['company_id']: item})
        pprint(self.all_companies)

    def init_acquired_companies(self, datafile: str):
        acq_companies = KnowledgeGraph.load_data(datafile)
        if acq_companies and len(acq_companies) == 0:
            raise Exception("Failed to data load; \
                             empty acquired companies list")

        self.all_acqs = dict()
        for item in acq_companies:
            parent_company_id = item['parent_company_id']
            if parent_company_id and \
               parent_company_id not in self.all_acqs.keys():
                company_acqs = list()
            company_acqs.append(item)
            if len(company_acqs) > 0:
                self.all_acqs.update({parent_company_id: company_acqs})
        # pprint(self.all_acqs)

    def init_employed_persons(self, datafile: str):
        persons = KnowledgeGraph.load_data(datafile)
        if persons and len(persons) == 0:
            raise Exception("Failed to data load; empty persons list")

        self.all_persons = dict()
        for item in persons:
            company_id = item['company_id']
            if company_id and company_id not in self.all_persons.keys():
                company_employees = list()
            company_employees.append(item)
            if len(company_employees) > 0:
                self.all_persons.update({company_id: company_employees})
        # pprint(self.all_persons)

    def build_graph(self):
        for company in self.all_companies.values():
            company_id = company["company_id"]
            company_name = company["company_name"].replace(" ", "_")
            company_acqs = self.all_acqs[company_id] \
                if company_id in self.all_acqs.keys() else list()
            company_emps = self.all_persons[company_id] \
                if company_id in self.all_persons.keys() else list()

            for acq in company_acqs:
                acq_company = self.all_companies[acq["acquired_company_id"]]
                acq_company_name = acq_company["company_name"]
                print("SUB:", acq["acquired_company_id"], acq_company_name)
                self.G.add_edge(company_name, acq_company_name)
            print(company_id, company_name, len(company_acqs), company_acqs)

            for employee in company_emps:
                emp_id = employee["person_id"]
                emp_title = employee["employment_title"].replace(" ", "_")
                print("EMP:", emp_id, emp_title)
                self.G.add_edge(company_name, f'{emp_id}:{emp_title}')
                # TODO: orphan check: person with company_id & no company info

            if len(company_acqs) == 0 and len(company_emps) == 0:
                print(company_id, company_name, 'sub=0', 'emp=0')
                self.G.add_node(company_name)

    def get_graph(self) -> Dict:
        return self.G


if __name__ == "__main__":
    kg = KnowledgeGraph()

    # load data from json files
    kg.init_companies(datafile="./data/companies_100.json")
    kg.init_acquired_companies(datafile="./data/company_acquisition_9.json")
    kg.init_employed_persons(datafile="./data/person_employment_25.json")
    kg.build_graph()

    # create color map for visualization
    color_map = nx.get_node_attributes(kg.get_graph(), "subcompany")
    color_map = nx.get_node_attributes(kg.get_graph(), "employee")

    net = Network(height='1500px', width='100%',
                  bgcolor='#ffffff', font_color='black', select_menu=True)
    net.from_nx(kg.get_graph())

    print(net.get_adj_list())

    # net.show_buttons(filter_=['physics'])
    net.show("org.html", notebook=False)
