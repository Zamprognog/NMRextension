import networkx as nx
from rule_extender.utils import *
from rule_extender.apply_rules import *
from pathlib import Path
from rule_extender.onto_processor import onto_processor
import time

ROOT_DIR = Path(__file__).resolve().parent
#todo: is to be parsed programmatically in the future
dataset_folder = ROOT_DIR / 'datasets'
dataset_name= 'NELL995'
# rules_file= ROOT_DIR / "rule_mining" / dataset_name / "split_mined_rules-100"
rules_file= ROOT_DIR / "rule_mining" / dataset_name / "amie_mined_rules_aligned.tsv"
train = dataset_folder / dataset_name / "NELL995_train.tsv"
valid =  dataset_folder / dataset_name /  "NELL995_valid.tsv"
test =   dataset_folder / dataset_name /  "NELL995_test.tsv"
schema_path = dataset_folder / dataset_name / "NELL.ontology.ttl"
temp_dir = ROOT_DIR / 'temp'
def_uri = 'http://ste-lod-crew.fr/nell/ontology/'
N = 3000


onto_p = onto_processor(str(schema_path), def_uri, checkSem=True)
rules,  pred_rules_index = parse_rules_file(str(rules_file))



graph_train = nx.MultiDiGraph()
with open(train, 'r') as rf:
    for line in rf.readlines():
        s, p, o = line.strip('\n').split('\t')
        graph_train.add_edge(s, o, key=p)

#todo: problem: classification/taxonomy is incorrect, need to improve the logic (person vs personus)
start = time.time()
generate_predictions(train_kg=graph_train, test_file=test, out_file=str(temp_dir / 'amie_test_predictions.txt'),
                     onto_processor = onto_p, pred_rules_index=pred_rules_index, limit=100, debug=True)
print(time.time() - start)
print(onto_p.get_stats())