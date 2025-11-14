import json
from rule_extender.utils import *
from rule_extender.generate_predictions import *
from pathlib import Path
from rule_extender.onto_processor import onto_processor
import time

# N = 3000
# for dataset in ['NELL995','hetionet']:
for dataset in ['YAGO4.5']:
    print(f'Computing predictions for dataset {dataset}')

    #loading configurations
    config_file = f'datasets/{dataset}/{dataset}.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    #loading train kg and knwon triples
    graph_train = nx.MultiDiGraph()
    known_triples = nx.MultiDiGraph()
    with open(config['train'], 'r') as rf:
        for line in rf.readlines():
            s, p, o = line.strip('\n').split('\t')
            graph_train.add_edge(s, o, key=p)
            known_triples.add_edge(s, o, key=p)

    for ds in [config['valid'], config['test']]:
        with open(ds, 'r') as rf:
            for line in rf.readlines():
                s, p, o = line.strip('\n').split('\t')
                known_triples.add_edge(s, o, key=p)

    #we have two rulesets
    # for ruleset in ['anyburl','amie']:
    for ruleset in ['anyburl']:
        print(f'Using ruleset {ruleset}')
        rules_file = config[f'{ruleset}_rules']
        rules, pred_rules_index = parse_rules_file(rules_file)

        #monotonic and non-monotonic case
        for check_sem in [False, True]:
            print(f'non monotonic extension: {check_sem}')

            if check_sem:
                output_file = config['predictions_dir'] + dataset + '_' + ruleset + '_nm.txt'
            else:
                output_file  = config['predictions_dir'] + dataset + '_' + ruleset + '.txt'

            onto_p = onto_processor(config['schema'], config['def_uri'], checkSem=check_sem)
            onto_p.find_direct_types(config['types_file'])


            start = time.time()
            generate_predictions(train_kg=graph_train,known_triples=known_triples, test_file=config['test_debug'], out_file=output_file,
                                 onto_processor = onto_p, pred_rules_index=pred_rules_index, limit=100, debug=False)
            print(f'predictions computed in {time.time() - start} seconds')
            onto_p.print_stats()