from rule_extender.lookforgrounding import lookforgrounding
import pandas as pd
from rdflib import URIRef #todo: maybe remove this
import networkx as nx
from rule_extender.onto_processor import onto_processor

def generate_triple_predictions(kg: nx.MultiDiGraph, filter: list, triple:pd.tseries, target_loc: int, candidate_rules:list,
                                limit:int,onto_processor:onto_processor,mask_object:bool = True):
    known_entity = triple.iloc[2-target_loc]
    predictions = dict()
    unique_predictions = set()

    for conf,cand in candidate_rules:
        if len(unique_predictions) > limit:
            # rationale is that the rankings and prediction are accurate up to N, usually 100
            break
        all_valid_groundings = set() #this is the results of all possible groundings of the target variable
        open_variables = list(set([t[1] for t in cand] + [t[2] for t in cand])) #variables to be assigned

        if mask_object:
            base_var = cand[0][1]
            target_var = cand[0][2]
        else:
            base_var = cand[0][2]
            target_var = cand[0][1]
        if onto_processor.checkSem :
            #these are 'in graph' checks
            if onto_processor.violates_dr_constraint(currentName=known_entity, pName=triple.iloc[1], checkRange=not mask_object):
                return predictions

            if mask_object and onto_processor.is_functional(prop=triple.iloc[1]):
                if any(edge[2] == triple.iloc[1] for edge in kg.out_edges(base_var, keys=True)):
                    onto_processor.func_trigger()
                    return predictions

            if not mask_object and onto_processor.is_inverse_functional(prop=triple.iloc[1]):
                if any(edge[2] == triple.iloc[1] for edge in kg.in_edges(base_var, keys=True)):
                    onto_processor.ifunc_trigger()
                    return predictions



        rule_groundings_are_valid = lookforgrounding(kg=kg, filter=filter,
                              remaining_rule=cand[1:],
                              target_pattern={'base_var': base_var, 'target_var': target_var,
                                              'property': triple.iloc[1], 'isObject': mask_object},
                              open_vars=[v for v in open_variables if v != base_var],
                              grounded_vars={base_var: known_entity},
                              results_list=all_valid_groundings, onto_processor=onto_processor,
                              limit=limit)
        if rule_groundings_are_valid and len(all_valid_groundings) > 0:  # counts == True if not exception triggered
            # update the list of predictions and the list of unique predictions
            if conf in predictions.keys():
                predictions[conf] = predictions[conf].union(all_valid_groundings)
            else:
                predictions[conf] = set(all_valid_groundings)
            unique_predictions = unique_predictions.union(all_valid_groundings)

    return predictions

def generate_predictions(train_kg, known_triples: nx.MultiDiGraph, test_file, out_file, onto_processor, pred_rules_index:dict,limit:int = 100,debug=False):

    test_triples = pd.read_csv(test_file, sep= '\t', header = None, names = ['s','p','o'])
    if debug: test_triples = test_triples[:100]
    with open(out_file, 'w') as of: #following the approach from anyburl
        for i, trip in test_triples.iterrows():
            p = trip.iloc[1]
            s = trip.iloc[0]
            o = trip.iloc[2]
            if i % 5000 == 0:
                print(i)

            candidate_rules = pred_rules_index[p] if p in pred_rules_index.keys() else []
            known_objects = [ent for ent, key_dict in known_triples[s].items() if p in key_dict and ent != o]
            sorted_o_predictions = generate_triple_predictions(kg=train_kg,filter=known_objects, triple=trip, target_loc=2,
                                                                          candidate_rules=candidate_rules, limit=limit,
                                                                          mask_object=True,onto_processor=onto_processor)
            known_subjects = [ent for ent, key_dict in known_triples.pred[o].items() if p in key_dict and ent != s]
            sorted_s_predictions = generate_triple_predictions(kg = train_kg,filter=known_subjects, triple=trip, target_loc=0,
                                                                      candidate_rules = candidate_rules, limit = limit,
                                                                      mask_object=False,onto_processor=onto_processor)
            of.write(f'{s}\t{p}\t{o}\n')

            of.write('subjects:\t' +  "".join(f"{pred}\t{key}\t" for key, string_list in sorted_s_predictions.items() for pred in string_list)+'\n')
            of.write('objects:\t' +  "".join(f"{pred}\t{key}\t" for key, string_list in sorted_o_predictions.items() for pred in string_list)+'\n')

            #these lines are required if we want to evaluate with anyburl.Eval
            # do.write(f'{s}\t{p}\t{o}\n')
            # do.write('subjects:\t' + "".join(f"{pred}\t{key}\t" for key, string_list in aggregate_max(sorted_s_predictions).items() for pred in string_list) + '\n')
            # do.write('objects:\t' + "".join( f"{pred}\t{key}\t" for key, string_list in aggregate_max(sorted_o_predictions).items() for pred in string_list) + '\n')



def aggregate_max(sorted_s_predictions):
    """
    Creates a new prediction ditcionary (conf:[predictions]) filtered according to max aggregation.
    Used if anyburl.Eval is to be used
    Args:
        sorted_s_predictions (dict): A dictionary where keys are confidence scores (float)
                                     and values are lists of predictions.
    Returns:
        dict: A new dictionary with the same structure, but filtered via the max aggregation approach.
    """
    filtered_predictions = {}
    seen_strings = set()
    for score, predictions_list in sorted_s_predictions.items():
        filtered_predictions[score] = []
        for item_string in predictions_list:
            if item_string not in seen_strings:
                filtered_predictions[score].append(item_string)
                seen_strings.add(item_string)
    return {k: v for k, v in filtered_predictions.items() if v}
