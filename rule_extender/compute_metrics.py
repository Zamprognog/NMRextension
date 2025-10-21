import itertools
from pathlib import Path

import networkx as nx
from rule_extender.onto_processor import onto_processor
from IPython.core.completerlib import magic_run_re


def aggregate_max(line:str):
    return line.strip().split()[1::2]

ROOT_DIR = Path(__file__).resolve().parent.parent
#todo: is to be parsed programmatically in the future
dataset_folder = ROOT_DIR / 'datasets'
dataset_name= 'NELL995'
# rules_file= ROOT_DIR / "rule_mining" / dataset_name / "split_mined_rules-100"
# train = dataset_folder / dataset_name / "NELL995_train.tsv"
# valid =  dataset_folder / dataset_name /  "NELL995_valid.tsv"
# test =   dataset_folder / dataset_name /  "NELL995_test.tsv"
# schema_path = dataset_folder / dataset_name / "NELL.ontology.ttl"
# temp_dir = ROOT_DIR / 'temp'
# def_uri = 'http://ste-lod-crew.fr/nell/ontology/'
N = 3000
rules_file= '../hetionet_demo/rules_nice-100'
train = '../hetionet_demo/hetionet/hetio_train_nice.tsv'
valid =  '../hetionet_demo/hetionet/hetio_validation_nice.tsv'
test =   '../hetionet_demo/hetionet/hetio_test_nice.tsv'
schema_path = '../hetionet_demo/hetionet/hetionet_tbox.nt'
output_file= '../hetionet_demo/hetionet/predictions_noCheck.txt'
types_file = '../hetionet_demo/hetionet/hetionet_entity_types.nt'
def_uri = 'http://ste-lod-crew.fr/nell/ontology/' #not really used

onto_p = onto_processor(str(schema_path), def_uri, checkSem=True)

kg = nx.MultiDiGraph()
with open(train, 'r') as rf:
    for line in rf.readlines():
        s, p, o = line.strip('\n').split('\t')
        kg.add_edge(s, o, key=p)
#for pfilename in ['../temp/amie_base_test_predictions.txt','../temp/amie_test_predictions.txt','../temp/anyburl_base_test_predictions.txt', '../temp/anyburl_test_predictions.txt']:
for pfilename in ['../hetionet_demo/hetionet/predictions_checkSem.txt', '../hetionet_demo/hetionet/predictions_noCheck.txt']:
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
            predictions_subjects = aggregate_max(subjectsLine)
            predictions_objects = aggregate_max(objectsLine)

            rank_s = predictions_subjects.index(s)+1 if s in predictions_subjects else 1e6
            rank_o = predictions_objects.index(o)+1 if o in predictions_objects else 1e6
            #hits and mrr
            for idx,k in enumerate(ks) :
                if rank_s <= k:
                    hits[idx] += 1
                if rank_o <= k:
                    hits[idx] += 1
                mrr += 1.0/rank_s +1.0/rank_o


            #keept it simple at sem@10
            if len(predictions_subjects)>0:
                triples_with_pred_s += 1
                sem_s = onto_p.sem_at_k(kg,(s,p,o), predictions_subjects[:10], False)/min(len(predictions_subjects),10)
                sem10s += sem_s
            if len(predictions_objects)>0:
                triples_with_pred_o += 1
                sem_o = onto_p.sem_at_k(kg,(s, p, o), predictions_objects[:10], True)/min(len(predictions_objects),10)
                sem10o += sem_o
        for idx,k in enumerate(ks):
            print(f'hits@{k}: {hits[idx]/(2*i)}')
        print(f'mrr: {mrr/(2*i)}')
        print(f'sem10s: {sem10s/triples_with_pred_s}\tsem10o: {sem10o/triples_with_pred_o}')
        print(f'sem10: {(sem10s/triples_with_pred_s + sem10o/triples_with_pred_o)/2}')
