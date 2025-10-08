import networkx
import networkx as nx
from rdflib import Graph
from collections import defaultdict
import re
from rule_extender.utils import load_ontology, find_functional_prop, find_dom_range, find_disjoint_classes, \
    find_super_classes,find_asymmetric_properties,find_symmetric_properties


class onto_processor:
    def __init__(self,ontology_file:str, def_uri:str, checkSem:bool):
        self.def_uri = def_uri #for future proofing
        self.onto = load_ontology(ontology_file)
        self.functional_properties = find_functional_prop(self.onto)
        self.dom_ranges = find_dom_range(self.onto)
        self.disjoint_classes = find_disjoint_classes(self.onto)
        self.super_classes = find_super_classes(self.onto)
        self.symmetric_properties = find_symmetric_properties(self.onto)
        self.asymmetric_properties = find_asymmetric_properties(self.onto)
        # self.asym_classes= find_asymmm_classes(self.onto)
        self.funcStats = 0
        self.drStats = 0
        self.symStats= 0
        self.checkSem = checkSem

    def is_functional(self, prop:str):
        return prop in self.functional_properties

    def is_symmetric(self, prop:str):
        return prop in self.symmetric_properties
    def is_asymmetric(self, prop:str):
        return prop in self.asymmetric_properties

    def get_domain(self, prop:str):
        return self.dom_ranges[prop][0]

    def get_range(self, prop:str):
        return self.dom_ranges[prop][1]

    def violates_dr_constraint(self, cName:str, pName:str, checkRange:bool = True):
        sc = self.super_classes[cName]
        if checkRange:
            disjoint_req = self.disjoint_classes[self.get_range(pName)]
        else:
            disjoint_req = self.disjoint_classes[self.get_domain(pName)]

        if any(c in disjoint_req for c in sc):
            self.drStats += 1
            return True
        return False

    def func_trigger(self):
        self.funcStats += 1

    def get_stats(self):
        return f'func: {self.funcStats}; dr: {self.drStats}; sym: {self.symStats}'

    def violate_functionality(self, kg: nx.MultiDiGraph, triple: tuple):
        out_edges = kg.out_edges(triple[0], keys=True)
        if any((edge[2] == triple[1] and edge[1] != triple[2]) for edge in out_edges):  # very confusing i know
            return True
        return False

    def sem_at_k(self,kg:nx.MultiDiGraph,triple:tuple, predictions:list, isObject:bool):
        valid=0.0
        for target in predictions:
            # domain/range
            if self.violates_dr_constraint(target.split('_')[0], triple[1], isObject):
                continue

            if triple[1] in self.functional_properties and self.violate_functionality(kg, triple):
                continue
            valid+=1
        #check d/r
        return valid