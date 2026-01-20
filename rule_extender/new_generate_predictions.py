import pandas as pd
import networkx as nx
from concurrent.futures import ProcessPoolExecutor
from rule_extender.onto_processor import onto_processor
from tqdm import tqdm
import multiprocessing
import os

# Import your existing modules
from rule_extender.lookforgrounding import lookforgrounding
from rule_extender.onto_processor import onto_processor as OntoProcessorClass

global_train_kg = None
global_known_triples = None
global_pred_rules_index = None
global_onto_processor = None
global_limit = None


def worker_init(train_kg, known_triples, pred_rules_index, onto_p, limit,config, check_sem, ruleset):
    """Initializes the worker process with the heavy read-only data."""
    global global_train_kg, global_known_triples, global_pred_rules_index
    global global_onto_processor, global_limit

    global_train_kg = train_kg
    global_known_triples = known_triples
    global_pred_rules_index = pred_rules_index

    global_limit = limit
    # global_onto_processor =onto_processor(config['schema'], config['def_uri'], checkSem=check_sem, ruleset = ruleset)
    # global_onto_processor.find_direct_types(config['types_file'])
    global_onto_processor = onto_p


def generate_triple_predictions(kg: nx.MultiDiGraph, filter_list: list, triple: list, target_loc: int,
                                candidate_rules: list, limit: int, onto_p:onto_processor, mask_object: bool = True):

    known_entity = triple[2 - target_loc]
    predictions = dict()
    unique_predictions = set()

    for conf, cand in candidate_rules:
        if len(unique_predictions) >= limit:
            break

        all_valid_groundings = set()
        # Fix: Ensure tuples are accessed correctly for open variables
        open_variables = list(set([t[1] for t in cand] + [t[2] for t in cand]))

        rule_body = cand[1:]
        if mask_object:
            base_var = cand[0][1]
            target_var = cand[0][2]
        else:
            base_var = cand[0][2]
            target_var = cand[0][1]
            if onto_p.ruleset == 'anyburl':
                rule_body = rule_body[::-1]

        if onto_p.checkSem:
            if onto_p.violates_dr_constraint(currentName=known_entity, pName=triple[1],
                                                     checkRange=not mask_object):
                return predictions

            if mask_object and onto_p.is_functional(prop=triple[1]):
                if any(edge[2] == triple[1] for edge in kg.out_edges(base_var, keys=True)):
                    # Note: counters in workers won't sync back to main process automatically
                    onto_p.func_trigger()
                    return predictions

        rule_groundings_are_valid = lookforgrounding(
            kg=kg,
            filter=filter_list,
            remaining_rule=rule_body,
            target_pattern={'base_var': base_var, 'target_var': target_var,
                            'property': triple[1], 'isObject': mask_object},
            open_vars=[v for v in open_variables if v != base_var],
            grounded_vars={base_var: known_entity},
            results_list=all_valid_groundings,
            onto_processor=onto_p,
            limit=limit,
            limit_branching=1000
        )

        if rule_groundings_are_valid and len(all_valid_groundings) > 0:
            if conf in predictions.keys():
                predictions[conf] = predictions[conf].union(all_valid_groundings)
            else:
                predictions[conf] = set(all_valid_groundings)
            unique_predictions = unique_predictions.union(all_valid_groundings)

    return predictions


def process_single_triple(trip):

    p = trip[1]
    s = trip[0]
    o = trip[2]

    candidate_rules = global_pred_rules_index[p] if p in global_pred_rules_index.keys() else []

    known_objects = []
    if s in global_train_kg:
        known_objects.extend([ent for ent, key_dict in global_train_kg[s].items() if p in key_dict and ent != o])
    if s in global_known_triples:
        known_objects.extend([ent for ent, key_dict in global_known_triples[s].items() if p in key_dict and ent != o])

    sorted_o_predictions = generate_triple_predictions(
        kg=global_train_kg,
        filter_list=known_objects,
        triple=trip,
        target_loc=2,
        candidate_rules=candidate_rules,
        limit=global_limit,
        mask_object=True,
        onto_p=global_onto_processor
    )


    known_subjects = []
    if hasattr(global_train_kg, 'pred') and o in global_train_kg.pred:
        known_subjects.extend([ent for ent, key_dict in global_train_kg.pred[o].items() if p in key_dict and ent != s])

    if hasattr(global_known_triples, 'pred') and o in global_known_triples.pred:
        known_subjects.extend([ent for ent, key_dict in global_known_triples.pred[o].items() if p in key_dict and ent != s])

    sorted_s_predictions = generate_triple_predictions(
        kg=global_train_kg,
        filter_list=known_subjects,
        triple=trip,
        target_loc=0,
        candidate_rules=candidate_rules,
        limit=global_limit,
        mask_object=False,
        onto_p=global_onto_processor
    )
    #print('triple done')
    # Format Output String immediately in worker to save main process work
    header = f'{s}\t{p}\t{o}\n'
    subj_str = 'subjects:\t' + "".join(
        f"{pred}\t{key}\t" for key, string_list in sorted_s_predictions.items() for pred in string_list) + '\n'
    obj_str = 'objects:\t' + "".join(
        f"{pred}\t{key}\t" for key, string_list in sorted_o_predictions.items() for pred in string_list) + '\n'

    return header + subj_str + obj_str


def new_generate_predictions(train_kg, known_triples, test_file, out_file,
                             onto_p, config, check_sem, ruleset, pred_rules_index: dict, limit: int = 100, debug=False):
    test_triples = pd.read_csv(test_file, sep='\t', header=None, names=['s', 'p', 'o'])
    if debug:
        test_triples = test_triples[:1000]

    # num_workers = os.cpu_count()
    num_workers= 3
    print(f"Starting parallel prediction with {num_workers} cores...")


    triples_data = [[row.s,row.p, row.o] for i, row in test_triples.iterrows()]

    # chunk_size = max(1, len(triples_data) // ((os.cpu_count()) * 4))
    # Open file once
    with open(out_file, 'w', encoding='utf-8') as of:

        # Initialize Pool
        with ProcessPoolExecutor(max_workers=num_workers,
                                 initializer=worker_init,
                                 initargs=(train_kg, known_triples, pred_rules_index,onto_p,
                                           limit,config, check_sem, ruleset)) as executor:

            chunk_size = max(1, len(triples_data) // ((num_workers) * 4))
            print('chunk_size:', chunk_size)

            for i, result_string in tqdm(enumerate(executor.map(process_single_triple, triples_data, chunksize=chunk_size))):
                of.write(result_string)



    print("Prediction Complete.")