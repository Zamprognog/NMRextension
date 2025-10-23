# materialize top rules until n% triples are added

#explore anti patterns for targeted issues?

#anti patterns: functional, d/r

import networkx as nx
from IPython.core.magic import on_off
from html5rdf.constants import entities

from rule_extender.utils import *
from rule_extender.generate_predictions import *
from pathlib import Path
from rule_extender.onto_processor import onto_processor
import time
from rule_extender.lookforgrounding import lookforgrounding



def materialize(schema_path, rules_file_path, train_path, valid_path, test_path, output_triples_path, new_triples_path, checkSem, N=100):
    '''
    Materializes the first N rules
    :param schema_path:
    :param rules_file_path:
    :param train_path:
    :param valid_path:
    :param test_path:
    :param output_triples_path:
    :param N:
    :return:
    '''
    onto_p = onto_processor(schema_path, def_uri, checkSem=checkSem)
    onto_p.find_direct_types(schema_path)
    rules, pred_rules_index = parse_rules_file(rules_file_path)

    #build the graph
    base_graph = nx.MultiDiGraph()

    for fName in [train_path, valid_path, test_path]:
        with open(fName, 'r') as rf:
            for line in rf.readlines():
                s, p, o = line.strip('\n').split('\t')
                base_graph.add_edge(s, o, key=p)

    new_triples = nx.MultiDiGraph()
    num_new_triples = 0
    for conf,rule in rules[:N]:
        for candidate_subject in base_graph.nodes():
            if checkSem and onto_p.violates_dr_constraint(currentName=candidate_subject,pName=rule[0][0], checkRange=False):
                continue
            all_valid_groundings = set()
            open_variables = list(set([t[1] for t in rule] + [t[2] for t in rule])) #variables to be assigned
            # lookforpath(kg=base_graph, target_pattern= {'base_var': rule[0][1], 'target_var':rule[0][2],'property':rule[0][0],'isObject':True},
            #             remaining_rule=rule[1:], last_assigned_variable=rule[0][1],
            #             open_vars=[v for v in open_variables if v!= rule[0][1]],
            #             grounded_vars={rule[0][1]:candidate_subject},
            #             results_list= all_valid_groundings, onto_processor=onto_p, limit=400)
            lookforgrounding(kg=base_graph, target_pattern={'base_var': rule[0][1], 'target_var':rule[0][2],'property':rule[0][0],'isObject':True},
                             remaining_rule=rule[1:], open_vars=[v for v in open_variables if v!= rule[0][1]],
                             grounded_vars={rule[0][1]:candidate_subject},
                             results_list=all_valid_groundings, onto_processor=onto_p, limit=400)
            if len(all_valid_groundings) > 0:
                num_new_triples += len(all_valid_groundings)
                for o in all_valid_groundings:
                    new_triples.add_edge(candidate_subject, o, key=rule[0][0])
            #todo: need to modify lookforgrounding so that it prunes the search after having found one s,p,o. this is probably much more complicated
    print(num_new_triples)

    mat_graph = nx.compose(base_graph, new_triples)
    with open(output_triples_path.replace('.txt',f'_{checkSem}.txt'), 'w') as wf:
        for out_node, in_node, key in mat_graph.edges(keys=True):
            wf.write(f"{out_node} {key} {in_node} .\n")
    with open(new_triples_path.replace('.txt',f'_{checkSem}.txt'), 'w') as ntf:
        for out_node, in_node, key in new_triples.edges(keys=True):
            ntf.write(f"{out_node} {key} {in_node} .\n")
def nell_to_triples(materialized_nell_file, nell_facts_file):
    '''
    Converts the new triples from materializing the rules into a nt file adding the appropriate IRIs and typing.
    :param materialized_nell_file: path of the output of the 'materialize' function
    :param nell_facts_file: name of the new nt file
    :return:
    '''
    onto_iri ='http://ste-lod-crew.fr/nell/ontology/'
    entities_iri = 'http://ste-lod-crew.fr/nell/resources/'
    with open(materialized_nell_file, 'r') as rf:
        with open(nell_facts_file, 'w') as wf:
            entities_done = set()
            for line in rf.readlines():
                s, p, o, _ = line.strip('\n').split(' ')
                stype, sname = s.split('_',1)
                otype, oname = o.split('_',1)
                if s not in entities_done:
                    wf.write(f"<{entities_iri}{s}>  <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <{onto_iri}{stype}> .\n")
                    #wf.write(f"<{entities_iri}{sname}>  <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <{onto_iri}{stype}> .\n")

                    entities_done.add(s)
                if o not in entities_done:
                    wf.write(f"<{entities_iri}{o}>  <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <{onto_iri}{otype}> .\n")
                    #wf.write(f"<{entities_iri}{oname}>  <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <{onto_iri}{otype}> .\n")
                    entities_done.add(o)
                wf.write(f"<{entities_iri}{s}> <{onto_iri}{p}> <{entities_iri}{o}> .\n")
                #wf.write(f"<{entities_iri}{sname}> <{onto_iri}{p}> <{entities_iri}{oname}> .\n")






ROOT_DIR = Path(__file__).resolve().parent.parent
#todo: is to be parsed programmatically in the future
dataset_folder = ROOT_DIR / 'datasets'
dataset_name= 'NELL995'

# train = str(dataset_folder / dataset_name / "NELL995_train.tsv")
# valid =  str(dataset_folder / dataset_name /  "NELL995_valid.tsv")
# test =   str(dataset_folder / dataset_name /  "NELL995_test.tsv")
# schema_path = str(dataset_folder / dataset_name / "NELL.ontology.ttl")
# temp_dir = str(ROOT_DIR / 'temp')
def_uri = 'http://ste-lod-crew.fr/nell/ontology/'

materialize('../hetionet_demo/hetio_train_graph.nt', '../hetionet_demo/rules_demo',
            '../hetionet_demo/hetio_train_nice.tsv', '../hetionet_demo/hetio_validation_nice.tsv',
            '../hetionet_demo/hetio_test_nice.tsv', '../hetionet_demo/materialized_graph.txt',
            '../hetionet_demo/new_triples.txt',checkSem=True, N=10)

# for expname,rules_file_name, check in [('NELL_anyburl_nmr','split_mined_rules-1000', True),('NELL_anyburl','split_mined_rules-1000', False),
#                                        ('NELL_amie_nmr','amie_mined_rules_aligned.tsv',True), ('NELL_amie','amie_mined_rules_aligned.tsv',False)]:
#     output_triples = '../temp/' + expname + '_materialized_graph.txt'
#     nt_facts_file= '../temp/' + expname + '_facts_materialized.nt'
#     rules_file_path = str(ROOT_DIR / "rule_mining" / dataset_name / rules_file_name)
#     materialize(schema_path, rules_file_path, train, valid, test, output_triples, checkSem=check)
#     nell_to_triples(output_triples, nt_facts_file)
# materialize(schema_path, rules_file, train, valid, test, '../temp/NELL_amie_materialized_graph.txt', checkSem=False)
# nell_to_triples('../temp/NELL_amie_nmr_materialized_graph.txt', '../temp/NELL_amie_nmr_facts_materialized.nt')
# materialize(schema_path, rules_file, train, valid, test, '../temp/base_NELL_materialized_graph.txt', checkSem=False)
# nell_to_triples('../temp/base_NELL_materialized_graph.txt', '../temp/base_NELL_facts_materialized.nt')