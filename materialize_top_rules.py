# materialize top rules until n% triples are added

#explore anti patterns for targeted issues?

#anti patterns: functional, d/r

import networkx as nx


from rule_extender.utils import *
from rule_extender.generate_predictions import *
from pathlib import Path
from rule_extender.onto_processor import onto_processor
import time
from rule_extender.lookforgrounding import lookforgrounding
import json
from datetime import datetime

def materialize(config, output_triples_path, new_triples_path, checkSem,ruleset, N=0.1):
    '''
    Materializes the first N% rules
    :param config:
    :param output_triples_path:
    :param new_triples_path:
    :param N:
    :return:
    '''

    schema_path = config['schema']
    rules_file_path = config[f'{ruleset}_rules']
    train_path = config['train']
    valid_path = config['valid']
    test_path = config['test']
    def_uri = config['def_uri']
    schema_processing_start = time.time()

    onto_p = onto_processor(schema_path, def_uri, checkSem=checkSem, ruleset = ruleset)
    onto_p.find_direct_types(config['types_file'])
    rules, pred_rules_index = parse_rules_file(rules_file_path)
    print(f'schema processed in {time.time() - schema_processing_start} seconds')

    #build the graph
    base_graph = nx.MultiDiGraph()

    for fName in [train_path, valid_path, test_path]:
        with open(fName, 'r', encoding='utf-8') as rf:
            for line in rf.readlines():
                s, p, o = line.strip('\n').split('\t')
                base_graph.add_edge(s, o, key=p)

    new_triples = nx.MultiDiGraph()
    triggered_rules_cnt = 0
    # num_new_triples = 0
    start = time.time()
    for conf,rule in rules:
        groundings_found = 0
        #materialize about 10% triples
        if new_triples.number_of_edges() >= N*base_graph.number_of_edges():
            break
        for candidate_subject in base_graph.nodes():
            if check_sem:
                #it is always predicting ?o so check if s already causes any issue
                if onto_p.violates_dr_constraint(currentName=candidate_subject,pName=rule[0][0], checkRange=False):
                    # s already violates the domain
                    continue
                if onto_p.is_functional(prop=rule[0][0]):
                    # s is already in a s,p triple
                    if any(edge[2] == rule[0][0] for edge in base_graph.out_edges(candidate_subject, keys=True)):
                        onto_p.func_trigger()
                        continue
            all_valid_groundings = set()
            open_variables = list(set([t[1] for t in rule] + [t[2] for t in rule])) #variables to be assigned

            #graph already contains all known information, so filter is empty
            if lookforgrounding(kg=base_graph, filter=[], target_pattern={'base_var': rule[0][1], 'target_var':rule[0][2],'property':rule[0][0],'isObject':True},
                             remaining_rule=rule[1:], open_vars=[v for v in open_variables if v!= rule[0][1]],
                             grounded_vars={rule[0][1]:candidate_subject},
                             results_list=all_valid_groundings, onto_processor=onto_p, limit=-1):
                if len(all_valid_groundings) > 0:
                    groundings_found += 1
                    # num_new_triples += len(all_valid_groundings)
                    for o in all_valid_groundings:
                        new_triples.add_edge(candidate_subject, o, key=rule[0][0])
        if groundings_found > 0:
            triggered_rules_cnt += 1
        #print(f'rule: {rule}, groundings found: {groundings_found}, tot groundings: {new_triples.number_of_edges()}')
    print(f'elapsed: {time.time() - start}')
        # if groundings_found > 0:
        #     print(rule)
    print(f'triggered rules: {triggered_rules_cnt}, new triples: {new_triples.number_of_edges()}')
    onto_p.print_stats()
    # mat_graph = nx.compose(base_graph, new_triples)
    # with open(output_triples_path, 'w') as wf:
    #     for out_node, in_node, key in mat_graph.edges(keys=True):
    #         wf.write(f"<{out_node}> <{key}> <{in_node}> .\n")
    with open(new_triples_path, 'w', encoding='utf-8') as ntf:
        for out_node, in_node, key in new_triples.edges(keys=True):
            ntf.write(f"<{out_node}> <{key}> <{in_node}> .\n")


today = datetime.now()
print(today.strftime("%A, %B %d, %Y"))

# datasets = ['NELL995','hetionet','YAGO4.5']
# rulesets = ['anyburl','amie']
# checkSems = [False, True]
#
# datasets = ['NELL995','hetionet','YAGO4.5']
# rulesets = ['amie']
# checkSems = [False, True]
datasets =['CSKG2']
rulesets = ['anyburl']
checkSems = [True]
checkSems = [False, True]
N=0.3
for dataset in datasets:
    print(f'###\tdataset: {dataset}\t###\n')
    config_file = f'datasets/{dataset}/{dataset}.json'
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    for ruleset in rulesets:
        for check_sem in checkSems:

            print(f'materializing {dataset} with {ruleset} rules, check sem {check_sem}')


            materialize(config, output_triples_path=config['predictions_dir'] + f'{dataset}_{N}_materialized_graph_{ruleset}_checkSem_' + str(check_sem) + '.nt',
            new_triples_path=config['predictions_dir'] +f'{dataset}_{N}_new_triples_{ruleset}_checkSem_' + str(check_sem) + '.nt',checkSem=check_sem,ruleset=ruleset, N=N)
