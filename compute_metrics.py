import itertools
from pathlib import Path
import json
import networkx as nx
from rule_extender.onto_processor import onto_processor
from collections import Counter, defaultdict
import pandas as pd
from IPython.core.completerlib import magic_run_re

#dataset= 'NELL995'
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
    ks = [1,3,9,10,11]
    # hits= Counter()
    # hits_s= Counter()
    # hits_o= Counter()
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

        for idx in [0,2,9]:
            print(f'{hits[idx]/(2*i)}')
        print(f'mrr: {mrr/(2*i)}')

