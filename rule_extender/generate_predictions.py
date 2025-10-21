from rule_extender.lookforpath import lookforpath
from rule_extender.lookforgrounding import lookforgrounding
import pandas as pd
from rdflib import URIRef #todo: maybe remove this
import networkx as nx
from rule_extender.onto_processor import onto_processor

def generate_triple_predictions(kg: nx.MultiDiGraph, triple:pd.tseries, target_loc: int, candidate_rules:list,
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
        if onto_processor.checkSem and onto_processor.violates_dr_constraint(currentName=known_entity, pName=triple.iloc[1], checkRange=not mask_object):
            # if objects are masked, subject is known, so check if the subject aligns with the head property's domain requirement
            # if subjects are masked, object is known so check for range2
            rule_groundings_are_valid = False
        else:

            rule_groundings_are_valid = lookforgrounding(kg=kg,
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
        # build the ranking
        sorted_predictions = [pred for key in sorted(predictions.keys(), reverse=True) for pred in predictions[key]]
        # aggregate according to 'max rank' criterion: only consider the highest conf rule for each predicted target
        if predictions is None:
            print('None here')
    return predictions

def generate_predictions(train_kg, test_file, out_file, onto_processor, pred_rules_index:dict,limit:int = 100,debug=False):

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

            sorted_o_predictions = generate_triple_predictions(kg=train_kg, triple=trip, target_loc=2,
                                                                          candidate_rules=candidate_rules, limit=limit,
                                                                          mask_object=True,onto_processor=onto_processor)

            sorted_s_predictions = generate_triple_predictions(kg = train_kg, triple=trip, target_loc=0,
                                                                      candidate_rules = candidate_rules, limit = limit,
                                                                      mask_object=False,onto_processor=onto_processor)
            of.write(f'{s}\t{p}\t{o}\n')

            of.write('subjects:\t' +  "".join(f"{pred}\t{key}\t" for key, string_list in sorted_s_predictions.items() for pred in string_list)+'\n')
            of.write('objects:\t' +  "".join(f"{pred}\t{key}\t" for key, string_list in sorted_o_predictions.items() for pred in string_list)+'\n')

