import networkx
import networkx as nx
from rdflib import Graph
from collections import defaultdict
import re
from rule_extender.utils import load_ontology, find_functional_prop, find_inverse_functional_prop, find_dom_range, find_disjoint_classes, \
    find_super_classes,find_asymmetric_properties,find_symmetric_properties


class onto_processor:
    def __init__(self,ontology_file:str, def_uri:str, checkSem:bool, ruleset:str):
        self.def_uri = def_uri #for future proofing
        onto = load_ontology(ontology_file)
        self.functional_properties = find_functional_prop(onto)
        self.inverse_functional_properties = find_inverse_functional_prop(onto)
        self.dom_ranges = find_dom_range(onto)
        self.disjoint_classes = find_disjoint_classes(onto)
        self.super_classes = find_super_classes(onto)
        self.symmetric_properties = find_symmetric_properties(onto)
        self.asymmetric_properties = find_asymmetric_properties(onto)
        self.ent2type = defaultdict(list)
        self.funcStats = 0
        self.ifuncStats = 0
        self.asymmStats = 0
        self.drStats = 0
        self.branchingStats = 0
        self.checkSem = checkSem
        self.ruleset= ruleset


    def is_functional(self, prop:str):
        return prop in self.functional_properties
    def is_inverse_functional(self, prop:str):
        return prop in self.inverse_functional_properties
    def is_symmetric(self, prop:str):
        return prop in self.symmetric_properties
    def is_anti_symmetric(self, prop:str):
        return prop in self.asymmetric_properties

    def get_domains(self, prop:str):
        return self.dom_ranges[prop][0]

    def get_ranges(self, prop:str):
        return self.dom_ranges[prop][1]

    def find_direct_types(self, types_file):

        with open(types_file, 'r', encoding='utf-8') as f:
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
            # restrictions = self.get_ranges(pName)
            restrictions = [self.super_classes.get(r, []) for r in self.get_ranges(pName)]
        else:
            # restrictions = self.get_domains(pName)
            restrictions = [self.super_classes.get(d, []) for d in self.get_domains(pName)]

        # if len(restrictions)>0 and all(restriction in disjoin_req for restriction in restrictions):
        if len(restrictions) > 0 and all(any(restrictionSC in disjoin_req for restrictionSC in restriction)for restriction in restrictions):
            self.drStats +=1
            return True
        return False


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

        return valid/len(predictions)

    def func_trigger(self):
        self.funcStats += 1

    def ifunc_trigger(self):
        self.ifuncStats += 1

    def asymm_trigger(self):
        self.asymmStats += 1

    def branching_trigger(self):
        self.branchingStats += 1

    def print_stats(self):
        print(
            f'found: {self.funcStats} functional exceptions; {self.ifuncStats} inv functional exceptions; {self.drStats} dr exceptions')

    def report_branching(self):
        print(self.branchingStats)
        self.branchingStats = 0
