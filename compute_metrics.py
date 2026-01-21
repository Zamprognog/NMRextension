import itertools
from pathlib import Path
import json
import networkx as nx
from rule_extender.onto_processor import onto_processor
from collections import Counter, defaultdict
import pandas as pd
from IPython.core.completerlib import magic_run_re

def max_inclusive_sort(line):

    scores_map = defaultdict(list)

    for i in range(0, len(line), 2):
        prediction = line[i]
        confidence = float(line[i + 1])
        scores_map[prediction].append(confidence)


    grouped_by_confs = defaultdict(list)

    for prediction, confidences in scores_map.items():

        confidences.sort(reverse=True)
        score_signature = tuple(confidences)
        grouped_by_confs[score_signature].append(prediction)


    sorted_signatures = sorted(grouped_by_confs.keys(), reverse=True)

    final_result = []
    for signature in sorted_signatures:
        predictions_in_tie = sorted(grouped_by_confs[signature])
        #final_result.append(predictions_in_tie)
        final_result.extend(predictions_in_tie)

    return final_result

#for dataset in ['NELL995','hetionet']:
for dataset in ['NELL995']:

    print(f'Computing metrics for {dataset}')
    config_file = f'datasets/{dataset}/{dataset}.json'
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    #bot needed because they are pre-filtered
    kg = nx.MultiDiGraph()
    # known_triples = set()
    # with open(config['train'], 'r', encoding='utf-8') as rf:
    #     for line in rf.readlines():
    #         s, p, o = line.strip('\n').split('\t')
    #         kg.add_edge(s, o, key=p)
    #         known_triples.add((s, p, o))
    #
    # for ds in [config['valid'], config['test']]:
    #     with open(ds, 'r', encoding='utf-8') as rf:
    #         for line in rf.readlines():
    #             s, p, o = line.strip('\n').split('\t')
    #             known_triples.add((s, p, o))

    for ruleset in ['anyburl']:
    # for ruleset in ['amie']:
        print(f'ruleset: {ruleset}')
        rules_file = config[f'{ruleset}_rules']
        #for check_sem, extension in [(False,'.txtmulticore'), (True, '_nm.txtmulticore')]:
        for check_sem, extension in [(True, '_nm_debug.txt')]:
            print(f'with exceptions: {check_sem}')

            onto_p = onto_processor(config['schema'], config['def_uri'], checkSem=check_sem, ruleset = ruleset)
            onto_p.find_direct_types(config['types_file'])

            #todo fix the naming similarly to 'materialized graph'
            # for ruletype in ['.txt', '_nm.txt']:
            pfilename = config['predictions_dir']+dataset+'_'+ruleset+extension
            #pfilename = '/Users/thezamp/Desktop/VU/codeProjects/NMRextension/datasets/hetionet/predictions/hetionet_original_anyburl_predictions'
            print(pfilename)
            ks = [1,3,10, 100]

            hits= defaultdict(lambda:0)
            hits_s= defaultdict(lambda:0)
            hits_o= defaultdict(lambda:0)
            mrr = 0.0
            sem10s =0.0
            sem10o = 0.0
            sem100s = 0.0
            sem100o = 0.0
            i= 0

            with open(pfilename, 'r', encoding='utf-8') as predictions_file:

                triples_with_pred_s = 0
                triples_with_pred_o = 0
                ocnt=0
                scnt=0
                for tripleLine, subjectsLine, objectsLine in itertools.zip_longest(*[predictions_file] * 3, fillvalue=''):
                    i = i + 1
                    s,p,o = tripleLine.strip('\n').split()

                    # predictions_subjects = list(dict.fromkeys(subjectsLine.strip().split()[1::2]))[:101]
                    # predictions_objects = list(dict.fromkeys(objectsLine.strip().split()[1::2]))[:101]
                    predictions_subjects = max_inclusive_sort(subjectsLine.strip().split()[1:])
                    predictions_objects = max_inclusive_sort(objectsLine.strip().split()[1:])

                    #compute filtered ranks
                    rank_s = 1
                    s_found = False
                    for ps in predictions_subjects:
                        if s == ps:
                            s_found = True
                            break
                        rank_s += 1
                    if not s_found:
                        rank_s = 1e6
                        scnt += 1

                    rank_o = 1
                    o_found = False
                    for po in predictions_objects:
                        if o ==po:
                            o_found = True
                            break
                        rank_o += 1
                    if not o_found:
                        rank_o = 1e6
                        ocnt+=1


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
                        sem_s = onto_p.sem_at_k(kg, (s, p, o), predictions_subjects[:10], False)
                        sem10s += sem_s

                        sem_s100 = onto_p.sem_at_k(kg, (s, p, o), predictions_subjects[:100], False)
                        sem100s +=sem_s100

                    if len(predictions_objects) > 0:
                        triples_with_pred_o += 1
                        sem_o = onto_p.sem_at_k(kg, (s, p, o), predictions_objects[:10], True)
                        sem10o += sem_o

                        sem_o100 = onto_p.sem_at_k(kg, (s, p, o), predictions_objects[:100], True)
                        sem100o += sem_o100


                for idx in [0,9]:
                    print(f'{hits[idx]/(2*i)}')
                print(f'mrr: {mrr/(2*i)}')
                print(f'sem10: {((sem10s/triples_with_pred_s) + (sem10o/triples_with_pred_o))/2}\n')
                print(f'sem100: {((sem100s / triples_with_pred_s) + (sem100o / triples_with_pred_o)) / 2}\n')

                print(f'{scnt}\t{ocnt}\t{i}')



def max_sort(line):
    scores_map = defaultdict(list)
    for i in range(0, len(line), 2):
        name = line[i]

        value = float(line[i + 1])
        scores_map[name].append(value)
    for name in scores_map:
        scores_map[name].sort(reverse=True)
    sorted_predictions = sorted(
        scores_map.keys(),
        key=lambda k: scores_map[k],
        reverse=True
    )
    return sorted_predictions
