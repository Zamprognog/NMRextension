import json
from rule_extender.utils import *
from rule_extender.generate_predictions import *
from pathlib import Path
from rule_extender.onto_processor import onto_processor
import time

dataset= 'NELL995'
config_file = f'datasets/{dataset}/{dataset}.json'
with open(config_file, 'r') as f:
    config = json.load(f)

N = 3000
check_sem =False
ruleset= 'anyburl'

if check_sem:
    output_file = config['predictions_dir'] + dataset + '_' + ruleset + '_nm.txt'
else:
    output_file  = config['predictions_dir'] + dataset + '_' + ruleset + '.txt'

rules_file = config[f'{ruleset}_rules']

start_time = time.time()
onto_p = onto_processor(config['schema'], config['def_uri'], checkSem=check_sem)
onto_p.find_direct_types(config['types_file'])
print(f'parsed_ontology: {time.time()-start_time}s')

rules,  pred_rules_index = parse_rules_file(rules_file)

graph_train = nx.MultiDiGraph()
with open(config['train'], 'r') as rf:
    for line in rf.readlines():
        s, p, o = line.strip('\n').split('\t')
        graph_train.add_edge(s, o, key=p)

start = time.time()
generate_predictions(train_kg=graph_train, test_file=config['test'], out_file=output_file,
                     onto_processor = onto_p, pred_rules_index=pred_rules_index, limit=1000, debug=False)
print(time.time() - start)
print(onto_p.get_stats())