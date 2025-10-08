import networkx as nx
from rdflib import Graph
from collections import defaultdict
import re

def parse_rule(line:str):
    conf, rule = line.replace('<=', '').split('\t')[-2:]
    # pattern = re.compile(r'(<\w+>)\((\w+),(\w+)\)')
    # pattern = re.compile(r'(<[^>]+>)\s*\(([^,]+),([^)]+)\)')
    pattern = re.compile(r'(\w+)\((\w+),(\w+)\)')
    conf = float(conf)
    matches = pattern.findall(rule)
    return conf, matches

def parse_rules_file(rules_file : str):
    rules = []
    pred_rules_index = dict()
    with open(rules_file) as rf:
        for line in rf.readlines():
            rules.append(parse_rule(line))
    rules = sorted(rules, key=lambda x: x[0], reverse=True)

    for rule in rules: #todo: this can be optimized with the above line
        if rule[1][0][0] not in pred_rules_index.keys():
            pred_rules_index[rule[1][0][0]] = [rule]
        else:
            pred_rules_index[rule[1][0][0]].append(rule)

    return rules, pred_rules_index


def load_ontology(ontology_path: str):
    onto = Graph().parse(ontology_path)
    return onto

def find_functional_prop(ontology:Graph):
    query4functional = '''
    prefix xsd:     <http://www.w3.org/2001/XMLSchema#>
    prefix nellonto:  <http://ste-lod-crew.fr/nell/ontology/>
    prefix owl:     <http://www.w3.org/2002/07/owl#>
    prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
    prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    select distinct ?prop where {
        ?prop a owl:FunctionalProperty .
    }
    '''
    res4functional = ontology.query(query4functional)
    return [str(row.prop).split('/')[-1] for row in res4functional]

def find_dom_range(ontology: Graph):
    query4domrange = '''
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT
      ?property
      (GROUP_CONCAT(DISTINCT STR(?domain); separator=" | ") AS ?domains)
      (GROUP_CONCAT(DISTINCT STR(?range); separator=" | ") AS ?ranges)
    WHERE {
      ?property rdfs:domain|rdfs:range [] .
      OPTIONAL { ?property rdfs:domain ?domain . }
      OPTIONAL { ?property rdfs:range ?range . }
    }
    GROUP BY ?property

    ORDER BY ?property
    '''

    res4domrange = ontology.query(query4domrange)

    domain_range_dict = dict()
    for res in res4domrange:
        # prop_dict[res.property] = (URIRef(res.domains),URIRef(res.ranges))
        domain_range_dict[str(res.property).split('/')[-1]] = (str(res.domains).split('/')[-1],
                                                               str(res.ranges).split('/')[-1])


    return domain_range_dict

def find_disjoint_classes(ontology: Graph):
    query_disjoint = '''
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?className ?dw
    WHERE {
    ?className owl:disjointWith ?dw
    }
    ORDER BY ?class ?dw
    '''
    res4disjoint = ontology.query(query_disjoint)

    disjoint_dict = defaultdict(lambda: []) #some classes are not disjoint with anything
    for dw_res in res4disjoint:
        className = str(dw_res["className"]).split('/')[-1]
        dw_class = str(dw_res["dw"]).split('/')[-1]
        if className not in disjoint_dict.keys():
            disjoint_dict[className] = [dw_class]
        else:
            disjoint_dict[className].append(dw_class)

    return disjoint_dict


def find_super_classes(ontology: Graph):
    query_super = '''
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?className ?super
    WHERE {
    ?className rdfs:subClassOf* ?super
    }
    ORDER BY ?class ?super
    '''
    res4super = ontology.query(query_super)

    disjoint_dict = defaultdict(lambda: []) #some classes are not disjoint with anything
    for sup_res in res4super:
        className = str(sup_res["className"]).split('/')[-1]
        super_class = str(sup_res["super"]).split('/')[-1]
        if className not in disjoint_dict.keys():
            disjoint_dict[className] = [super_class]
        else:
            disjoint_dict[className].append(super_class)

    return disjoint_dict


def find_asymmetric_properties(ontology: Graph):
    query = '''
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?prop
    WHERE {
    ?prop a owl:AsymmetricProperty .
    }
    '''

    res = ontology.query(query)
    return [str(row.prop).split('/')[-1] for row in res]

def find_symmetric_properties(ontology: Graph):
    query = '''
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?prop
    WHERE {
    ?prop a owl:SymmetricProperty .
    }
    '''

    res = ontology.query(query)
    return [str(row.prop).split('/')[-1] for row in res]



