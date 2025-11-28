import json
from rule_extender.utils import *
from rule_extender.new_generate_predictions import *
# from rule_extender.generate_predictions import *
from pathlib import Path
from rule_extender.onto_processor import onto_processor
import time

# N = 3000

if __name__ == '__main__':
    # try:
    #     multiprocessing.set_start_method('fork')
    # except RuntimeError:
    #     pass
    multiprocessing.freeze_support()

    datasets = ['YAGO4.5']
    rulesets = ['anyburl']
    semantics = [True,False]

    for dataset in datasets:
        print(f'Computing predictions for dataset {dataset}')

        #loading configurations
        config_file = f'datasets/{dataset}/{dataset}.json'
        with open(config_file, 'r') as f:
            config = json.load(f)

        #loading train kg and known triples
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

        for ruleset in rulesets:
            print(f'Using ruleset {ruleset}')
            rules_file = config[f'{ruleset}_rules']
            rules, pred_rules_index = parse_rules_file(rules_file)

            for check_sem in semantics:
                print(f'non monotonic extension: {check_sem}')

                if check_sem:
                    output_file = config['predictions_dir'] + dataset + '_' + ruleset + '_nm.txt'
                else:
                    output_file  = config['predictions_dir'] + dataset + '_' + ruleset + '.txt'

                onto_p = onto_processor(config['schema'], config['def_uri'], checkSem=check_sem, ruleset = ruleset)
                onto_p.find_direct_types(config['types_file'])


                start = time.time()
                # generate_predictions(train_kg=graph_train,known_triples=known_triples, test_file=config['test'], out_file=output_file,
                #                      onto_processor = onto_p, pred_rules_index=pred_rules_index, limit=100, debug=False)
                new_generate_predictions(train_kg=graph_train,known_triples=known_triples, test_file=config['test'], out_file=output_file+'multicore',
                                      onto_p=onto_p, config = config, pred_rules_index=pred_rules_index, limit=100, debug=False, check_sem = check_sem, ruleset=ruleset)

                print(f'predictions computed in {time.time() - start} seconds')
            #onto_p.print_stats()