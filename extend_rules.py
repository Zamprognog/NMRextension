import networkx as nx
from rule_extender.utils import *
from rule_extender.generate_predictions import *
from pathlib import Path
from rule_extender.onto_processor import onto_processor
import time


ROOT_DIR = Path(__file__).resolve().parent
#todo: is to be parsed programmatically in the future
dataset_folder = ROOT_DIR / 'datasets'
dataset_name= 'NELL995'
#rules_file= ROOT_DIR / "rule_mining" / dataset_name / "split_mined_rules-1000"
#rules_file= str(ROOT_DIR / "rule_mining" / dataset_name / "amie_mined_rules_aligned.tsv")
# train = str(dataset_folder / dataset_name / "NELL995_train.tsv")
# valid =  str(dataset_folder / dataset_name /  "NELL995_valid.tsv")
# test =   str(dataset_folder / dataset_name /  "NELL995_test.tsv")
# schema_path = str(dataset_folder / dataset_name / "NELL.ontology.ttl")
# output_file= str(ROOT_DIR / 'temp'/'amie_base_test_predictions.txt')
# def_uri = 'http://ste-lod-crew.fr/nell/ontology/' #not really used

rules_file= 'hetionet_demo/rules_nice-100'
train = 'hetionet_demo/hetionet/hetio_train_nice.tsv'
valid =  'hetionet_demo/hetionet/hetio_validation_nice.tsv'
test =   'hetionet_demo/hetionet/debug_hetio_test.tsv'
test =   'hetionet_demo/hetionet/hetio_test_nice.tsv'
schema_path = 'hetionet_demo/hetionet/hetionet_tbox.nt'
output_file= 'hetionet_demo/hetionet/predictions_noCheck.txt'
types_file = 'hetionet_demo/hetionet/hetionet_entity_types.nt'
def_uri = 'http://ste-lod-crew.fr/nell/ontology/' #not really used
N = 3000

start_time = time.time()
onto_p = onto_processor(str(schema_path), def_uri, checkSem=False)
onto_p.find_direct_types(types_file)
print(f'parsed_ontology: {time.time()-start_time}s')
rules,  pred_rules_index = parse_rules_file(str(rules_file))



graph_train = nx.MultiDiGraph()
with open(train, 'r') as rf:
    for line in rf.readlines():
        s, p, o = line.strip('\n').split('\t')
        graph_train.add_edge(s, o, key=p)


start = time.time()
generate_predictions(train_kg=graph_train, test_file=test, out_file=output_file,
                     onto_processor = onto_p, pred_rules_index=pred_rules_index, limit=100, debug=False)
print(time.time() - start)
print(onto_p.get_stats())