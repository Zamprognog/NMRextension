import itertools
from pathlib import Path
import json
import networkx as nx
from rule_extender.onto_processor import onto_processor
import pandas as pd
from IPython.core.completerlib import magic_run_re

dataset= 'hetionet'
config_file = f'datasets/{dataset}/{dataset}.json'
with open(config_file, 'r') as f:
    config = json.load(f)


N = 3000
check_sem =True
ruleset= 'anyburl'
rules_file = config[f'{ruleset}_rules']
onto_p = onto_processor(config['schema'], config['def_uri'], checkSem=check_sem)
kg = nx.MultiDiGraph()
known_triples = set()
with open(config['train'], 'r') as rf:
    for line in rf.readlines():
        s, p, o = line.strip('\n').split('\t')
        kg.add_edge(s, o, key=p)
        known_triples.add((s,p,o))

for ds in [config['valid'], config['test']]:
    with open(ds, 'r') as rf:
        for line in rf.readlines():
            s, p, o = line.strip('\n').split('\t')
            known_triples.add((s, p, o))

for ruletype in ['.txt', '_nm.txt']:
    pfilename = config['predictions_dir']+dataset+'_'+ruleset+ruletype
    print(pfilename)
    ks = [1,5,10]
    hits= [0.0,0.0,0.0]
    mrr = 0.0
    sem10s =0.0
    sem10o = 0.0
    i= 0

    with open(pfilename, 'r') as predictions_file:
        triples_with_pred_s = 0
        triples_with_pred_o = 0
        for tripleLine, subjectsLine, objectsLine in itertools.zip_longest(*[predictions_file] * 3, fillvalue=''):
            i = i + 1
            s,p,o = tripleLine.strip('\n').split()

            predictions_subjects = list(set(subjectsLine.strip().split()[1::2]))
            predictions_objects = list(set(objectsLine.strip().split()[1::2]))

            #compute filtered ranks
            rank_s = 1
            for ps in predictions_subjects:
                if ps == s:
                    break

                if (ps, p, o) in known_triples:
                    continue

                rank_s += 1
            if rank_s == len(predictions_subjects):
                rank_s = 1e6

            rank_o = 1
            for po in predictions_objects:
                if po == o:
                    break

                if (s, p, po) in known_triples:
                    continue

                rank_o += 1
            if rank_o == len(predictions_objects):
                rank_o = 1e6


            #hits and mrr
            for idx,k in enumerate(ks) :
                if rank_s <= k:
                    hits[idx] += 1
                if rank_o <= k:
                    hits[idx] += 1
            mrr += 1.0/rank_s +1.0/rank_o


            # #keept it simple at sem@10
            # if len(predictions_subjects)>0:
            #     triples_with_pred_s += 1
            #     sem_s = onto_p.sem_at_k(kg,(s,p,o), predictions_subjects[:10], False)/min(len(predictions_subjects),10)
            #     sem10s += sem_s
            # if len(predictions_objects)>0:
            #     triples_with_pred_o += 1
            #     sem_o = onto_p.sem_at_k(kg,(s, p, o), predictions_objects[:10], True)/min(len(predictions_objects),10)
            #     sem10o += sem_o
        for idx,k in enumerate(ks):
            print(f'hits@{k}: {hits[idx]/(2*i)}')
        print(f'mrr: {mrr/(2*i)}')
        # print(f'sem10s: {sem10s/triples_with_pred_s}\tsem10o: {sem10o/triples_with_pred_o}')
        # print(f'sem10: {(sem10s/triples_with_pred_s + sem10o/triples_with_pred_o)/2}')
