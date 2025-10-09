import networkx as nx
from rule_extender.onto_processor import onto_processor
def lookforgrounding(kg:nx.MultiDiGraph,target_pattern:dict,remaining_rule:list,
                open_vars:list, grounded_vars:dict, results_list:set, onto_processor:onto_processor,
                limit:int):
    '''

    :param kg: the input graph
    :param target_pattern: target variable, property, variable positon(s or o)
    :param remaining_rule: remaining patterns in the CP rule
    :param open_vars: list of variables yet to be assigned
    :param grounded_vars: dictionary of grounded variables
    :param results_list: list of current acceptable assignments of target_var
    :param onto_processor: functionalities to do semantic checks
    :param limit: limit to the additional assignments to be explored (limits search and won't be noticed in the hits@k measure)

    :return:
    '''

    #base case: all variables found a grounding, we check if it is valid
    if len(open_vars) ==0: # all variables are grounded
        to_add = grounded_vars[target_pattern['target_var']]
        if onto_processor.checkSem:
            if onto_processor.is_functional(target_pattern['property']) and target_pattern['isObject'] and len(results_list)>2:
                # functional exception condition: prop is functional, we are predicting objects, we have 2 different groundings
                onto_processor.func_trigger()
                return False
            if onto_processor.is_functional(target_pattern['property']) and not target_pattern['isObject'] and any(edge[2] == target_pattern['property'] for edge in kg.out_edges(to_add, keys=True)):
                # functional exception condition: prop is functional, we are predicting subjects, the subject has already a different s p edge
                onto_processor.func_trigger()
                return False
            if onto_processor.violates_dr_constraint(cName=to_add.split('_')[0], pName=target_pattern['property'], checkRange=target_pattern['isObject']):
                # dom/range exception condition
                return False
            if onto_processor.is_symmetric((target_pattern['property'])):
                #this is a STRONG commitment but follows from cwa
                if target_pattern['isObject'] and not kg.has_edge(target_pattern['target_var'], target_pattern['base_var']):
                    return False
                if not target_pattern['isObject'] and not kg.has_edge(target_pattern['base_var'],
                                                                  target_pattern['target_var']):
                    return False
            if onto_processor.is_asymmetric((target_pattern['property'])):
                if target_pattern['isObject'] and kg.has_edge(target_pattern['target_var'], target_pattern['base_var']):
                    return False
                if not target_pattern['isObject'] and kg.has_edge(target_pattern['base_var'], target_pattern['target_var']):
                    return False
        if  to_add not in results_list:
            #congrats, no exceptions: add to allowed groundings for the rule
            results_list.add(to_add)
        return True

    #iteration case: due to AMIE having different types of rules, we rotate the rule until we get one atom that is already instantiated
    if remaining_rule[0][1] not in grounded_vars.keys() and remaining_rule[0][2] not in grounded_vars.keys():
        starting_i = next((i for i, sublist in enumerate(remaining_rule) if not grounded_vars.keys().isdisjoint(sublist[1:])),None)
        shifted_cand  = remaining_rule[starting_i:] + remaining_rule[:starting_i]
    else:
        shifted_cand = remaining_rule
    target_prop = shifted_cand[0][0] #the type of edge

    # Option1: the subject was previously grounded, the object is not
    if shifted_cand[0][2] not in grounded_vars.keys():
        try:
            out_edges = kg.out_edges(grounded_vars[shifted_cand[0][1]], keys=True)
        except KeyError as e:
            print(e)
        except IndexError as e:
            print(e)

        if len(out_edges) == 0:
            return True

        target_out_edges = [edge for edge in out_edges if edge[2] == target_prop]
        current_variable = shifted_cand[0][2]  # trying to ground the object
        for oe in target_out_edges:
            if len(results_list) > limit:
                return True
            if oe[1] not in grounded_vars.values():  # no going back, and also not picking an entity already assigned
                if not lookforgrounding(kg=kg, target_pattern=target_pattern,
                                   remaining_rule=shifted_cand[1:],
                                   open_vars=[v for v in open_vars if v != current_variable],
                                   grounded_vars={**grounded_vars, current_variable: oe[1]},
                                   results_list=results_list, onto_processor=onto_processor,
                                   limit=limit):
                    return False

    #Option 2: the object was previously grounded, the subject is not
    elif shifted_cand[0][1] not in grounded_vars.keys():
        in_edges = kg.in_edges(grounded_vars[shifted_cand[0][2]], keys=True)
        if len(in_edges) == 0:
            return True
        target_in_edges = [edge for edge in in_edges if edge[2] == target_prop]

        current_variable = shifted_cand[0][1]
        for ie in target_in_edges:
            if len(results_list) > limit:
                return True
            if ie[0] not in grounded_vars.values():
                if not lookforgrounding(kg=kg, target_pattern=target_pattern,
                                   remaining_rule=shifted_cand[1:],
                                   open_vars=[v for v in open_vars if v != current_variable],
                                   grounded_vars={**grounded_vars, current_variable: ie[0]},
                                   results_list=results_list, onto_processor=onto_processor, limit=limit):
                    return False

    #Option 3: both are grounded, check if this link also exists
    else :
        if not kg.has_edge(grounded_vars[shifted_cand[0][1]], grounded_vars[shifted_cand[0][2]], key=target_prop):
            return False
        else:
            return lookforgrounding(kg=kg, target_pattern=target_pattern,
                                   remaining_rule=shifted_cand[1:],
                                   open_vars=open_vars,
                                   grounded_vars=grounded_vars,
                                   results_list=results_list, onto_processor=onto_processor, limit=limit)

    return True
#%%
