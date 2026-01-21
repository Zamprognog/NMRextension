import networkx as nx
from rdflib import Graph
from collections import defaultdict
import re

def parse_rule(line:str):
    groundings, correct, conf, rule = line.replace('<=', '').split('\t')[:]
    # pattern = re.compile(r'(<\w+>)\((\w+),(\w+)\)')
    # pattern = re.compile(r'(<[^>]+>)\s*\(([^,]+),([^)]+)\)')
    # pattern = re.compile(r'(\w+)\((\w+),(\w+)\)') #this was for NELL
    # pattern = re.compile(r'(\S+?)\((\w+),(\w+)\)')
    pattern = re.compile(r'(\S+?)\((\S+?),(\S+?)\)')

    #conf = float(conf)
    applied_conf = float(correct)/(float(groundings)+5)
    matches = pattern.findall(rule)
    return float(conf), float(applied_conf), matches

def parse_rules_file(rules_file : str):
    rules = []
    pred_rules_index = dict()
    debug_tot = 0
    debug_cnt = 0
    with open(rules_file, encoding='utf-8') as rf:
        for line in rf.readlines():
            debug_tot += 1
            c, ac, matches = parse_rule(line)
            if c < 0.999:
                debug_cnt += 1
                rules.append((ac, matches))

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
    prefix owl:     <http://www.w3.org/2002/07/owl#>
    prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
    prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    select distinct ?prop where {
        ?prop a owl:FunctionalProperty .
    }
    '''
    res4functional = ontology.query(query4functional)
    return [str(row.prop) for row in res4functional]

def find_inverse_functional_prop(ontology:Graph):
    query4functional = '''
        prefix xsd:     <http://www.w3.org/2001/XMLSchema#>
        prefix owl:     <http://www.w3.org/2002/07/owl#>
        prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
        prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        select distinct ?prop where {
            ?prop a owl:InverseFunctionalProperty .
        }
        '''
    res4functional = ontology.query(query4functional)
    return [str(row.prop) for row in res4functional]
    # return [str(row.prop).split('/')[-1] for row in res4functional]


def dom_range_init():
    return ([], [])

def find_dom_range(ontology: Graph):
    query4dom= '''PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        
        SELECT DISTINCT ?property ?domain
        WHERE {
          ?property rdfs:domain ?domainNode .
        
          OPTIONAL {
            ?domainNode owl:unionOf/rdf:rest*/rdf:first ?member .
          }
          BIND(IF(BOUND(?member), ?member, ?domainNode) AS ?domain)
          FILTER(ISURI(?domain))
        }
        ORDER BY ?property ?domain'''

    query4range  = '''PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        
        SELECT DISTINCT ?property ?range
        WHERE {
          ?property rdfs:range ?rangeNode .
        
          OPTIONAL {
            ?rangeNode owl:unionOf/rdf:rest*/rdf:first ?member .
          }
          BIND(IF(BOUND(?member), ?member, ?rangeNode) AS ?range)
          FILTER(ISURI(?range))
        }
        ORDER BY ?property ?range'''
    #res4domrange = ontology.query(query4domrange)
    res4dom = ontology.query(query4dom)
    res4range = ontology.query(query4range)

    # domain_range_dict = defaultdict(lambda: ([], []))
    domain_range_dict = defaultdict(dom_range_init)
    for res in res4dom:

        # prop_dict[res.property] = (URIRef(res.domains),URIRef(res.ranges))
        # domain_range_dict[str(res.property).split('/')[-1]] = (str(res.domains).split('/')[-1],  str(res.ranges).split('/')[-1])
        domain_range_dict[str(res.property)][0].append(str(res.domain))
    for res in res4range:
        domain_range_dict[str(res.property)][1].append(str(res.range))

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

    # disjoint_dict = defaultdict(lambda: []) #some classes are not disjoint with anything
    disjoint_dict = defaultdict(list)
    for dw_res in res4disjoint:
        className = str(dw_res["className"])
        dw_class = str(dw_res["dw"])
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

    sc_dict = defaultdict(list)
    for sup_res in res4super:
        className = str(sup_res["className"])
        super_class = str(sup_res["super"])
        if className not in sc_dict.keys():
            sc_dict[className] = [super_class]
        else:
            sc_dict[className].append(super_class)

    return sc_dict


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
    return [str(row.prop) for row in res]

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
    return [str(row.prop) for row in res]


