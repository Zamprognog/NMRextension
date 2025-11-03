import itertools
from pathlib import Path
import json
import networkx as nx
from rule_extender.onto_processor import onto_processor
from collections import Counter, defaultdict
import pandas as pd
from IPython.core.completerlib import magic_run_re


for dataset in ['NELL995','hetionet']:

    print(f'Computing metrics for {dataset}')
    config_file = f'datasets/{dataset}/{dataset}.json'
    with open(config_file, 'r') as f:
        config = json.load(f)

    kg = nx.MultiDiGraph()
    known_triples = set()
    with open(config['train'], 'r') as rf:
        for line in rf.readlines():
            s, p, o = line.strip('\n').split('\t')
            kg.add_edge(s, o, key=p)
            known_triples.add((s, p, o))

    for ds in [config['valid'], config['test']]:
        with open(ds, 'r') as rf:
            for line in rf.readlines():
                s, p, o = line.strip('\n').split('\t')
                known_triples.add((s, p, o))

    for ruleset in ['anyburl', 'amie']:
        print(f'ruleset: {ruleset}')
        rules_file = config[f'{ruleset}_rules']
        for check_sem, extension in [(False,'.txt'), (True, '_nm.txt')]:
            print(f'with exceptions: {check_sem}')

            onto_p = onto_processor(config['schema'], config['def_uri'], checkSem=check_sem)
            onto_p.find_direct_types(config['types_file'])

            #todo fix the naming similarly to 'materialized graph'
            # for ruletype in ['.txt', '_nm.txt']:
            pfilename = config['predictions_dir']+dataset+'_'+ruleset+extension
            print(pfilename)
            ks = [1,3,10]

            hits= defaultdict(lambda:0)
            hits_s= defaultdict(lambda:0)
            hits_o= defaultdict(lambda:0)
            mrr = 0.0
            sem10s =0.0
            sem10o = 0.0
            i= 0

            with open(pfilename, 'r') as predictions_file:

                triples_with_pred_s = 0
                triples_with_pred_o = 0
                cnt=0 #counting how many are filtered
                for tripleLine, subjectsLine, objectsLine in itertools.zip_longest(*[predictions_file] * 3, fillvalue=''):
                    i = i + 1
                    s,p,o = tripleLine.strip('\n').split()

                    predictions_subjects = list(dict.fromkeys(subjectsLine.strip().split()[1::2]))[:100]
                    predictions_objects = list(dict.fromkeys(objectsLine.strip().split()[1::2]))[:100]


                    #compute filtered ranks
                    rank_s = 1
                    for ps in predictions_subjects:
                        if ps == s:
                            break

                        if (ps, p, o) in known_triples:
                            cnt = cnt + 1
                            continue

                        rank_s += 1
                    if rank_s == len(predictions_subjects)+1:
                        rank_s = 1e6

                    rank_o = 1
                    for po in predictions_objects:
                        if po == o:
                            break
                        if (s, p,po) in known_triples:
                            cnt = cnt + 1
                            continue
                        rank_o += 1

                    if rank_o == len(predictions_objects)+1:
                        rank_o = 1e6


                    #hits and mrr
                    # for idx,k in enumerate(ks) :
                    for idx in range(10):
                        if rank_s <= idx +1:
                            hits[idx] += 1
                            hits_s[idx] +=1
                        if rank_o <= idx+1:
                            hits[idx] += 1
                            hits_o[idx] +=1
                    mrr += 1.0/rank_s +1.0/rank_o

                    # kept it simple at sem@10
                    if len(predictions_subjects) > 0:
                        triples_with_pred_s += 1
                        sem_s = onto_p.sem_at_k(kg, (s, p, o), predictions_subjects[:10], False) / min(
                            len(predictions_subjects), 10)
                        sem10s += sem_s
                    if len(predictions_objects) > 0:
                        triples_with_pred_o += 1
                        sem_o = onto_p.sem_at_k(kg, (s, p, o), predictions_objects[:10], True) / min(
                            len(predictions_objects), 10)
                        sem10o += sem_o


                for idx in [0,2,9]:
                    print(f'{hits[idx]/(2*i)}')
                print(f'mrr: {mrr/(2*i)}')
                print(f'sem10: {((sem10s/triples_with_pred_s) + (sem10o/triples_with_pred_o))/2}\n')


