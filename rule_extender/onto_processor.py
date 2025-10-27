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
        self.ent2type = defaultdict(list)
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

    def get_domains(self, prop:str):
        return self.dom_ranges[prop][0]

    def get_ranges(self, prop:str):
        return self.dom_ranges[prop][1]

    def find_direct_types(self, types_file):

        with open(types_file, 'r') as f:
            for line in f.readlines():
                if 'syntax-ns#type' in line:
                    tokens = line.replace('<','').replace('>','').split()
                    self.ent2type[tokens[0]].append(tokens[2])

    def violates_dr_constraint(self, currentName:str, pName:str, checkRange:bool = True):
        '''

        :param currentName: name of the entity or class being analyzed, in some dataset the class is known a priori todo: remove this functionality
        :param pName: name of the property for which we check domain/range
        :param checkRange: whether domain or range is being considered
        :param classKnown: together with currentName, in case currentName is already a class
        :return: True if d/r constraints are violated, False otherwise
        '''

        super_classes = { superclass for t in  self.ent2type.get(currentName, []) for superclass in self.super_classes.get(t, []) }

        disjoin_req = { disjClass for c in super_classes for disjClass in self.disjoint_classes.get(c, [])}

        if checkRange:
            restrictions = self.get_ranges(pName)
        else:
            restrictions = self.get_domains(pName)

        if all(restriction in disjoin_req for restriction in restrictions):
            self.drStats +=1
            return True
        return False

    def func_trigger(self):
        self.funcStats += 1

    def get_stats(self):
        return f'func: {self.funcStats}; dr: {self.drStats}; sym: {self.symStats}'

    def violate_functionality(self, kg: nx.MultiDiGraph, triple: tuple):
        out_edges = kg.out_edges(triple[0], keys=True)
        if any((edge[2] == triple[1] and edge[1] != triple[2]) for edge in out_edges):  # very confusing i know
            self.funcStats +=1
            return True
        return False

    def sem_at_k(self,kg:nx.MultiDiGraph,triple:tuple, predictions:list, isObject:bool):
        valid=0.0
        for target in predictions:
            # domain/range
            if self.violates_dr_constraint(target, triple[1], isObject):
                continue

            if triple[1] in self.functional_properties and self.violate_functionality(kg, triple):
                continue
            valid+=1
        #check d/r
        return valid