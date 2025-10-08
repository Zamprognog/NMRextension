#todo: this likely is repetitive codes from utils, merge the files
#todo: this is still a metric, for now can leave separate, then unify


from rdflib import Graph
import random

disjointsQ = '''PREFIX owl: <http://www.w3.org/2002/07/owl#>
select ?s ?c1 ?c2 where {
    ?class1 owl:disjointWith ?class2 .
    ?s1 a ?class1 .
    ?s1 a ?class2 .
}'''

functionalQ= '''PREFIX owl: <http://www.w3.org/2002/07/owl#>
select ?fp ?s1 ?o1 ?o2 where {
    ?fp a owl:FunctionalProperty .
    ?s1 ?fp ?o1 .
    ?s1 ?fp ?o2 .
    FILTER(?o1 != ?o2) .
} '''

invFunctionalQ= '''PREFIX owl: <http://www.w3.org/2002/07/owl#>
select ?fp ?s1 ?s2 ?o where {
    ?fp a owl:InverseFunctionalProperty .
    ?s1 ?fp ?o .
    ?s2 ?fp ?o .
    FILTER(?s1 != ?s2) .
}'''

symmetricQ = '''PREFIX owl: <http://www.w3.org/2002/07/owl#>
select ?prop ?s1 ?s2 ?o where {
    ?prop a owl:SymmetricProperty .
    ?s1 ?prop ?o1 .
    FILTER NOT EXISTS{?o1 ?prop ?s1}
}'''

asymmetricQ = '''PREFIX owl: <http://www.w3.org/2002/07/owl#>
select ?prop ?s1 ?o1 where {
    ?prop a owl:AsymmetricProperty .
    ?s1 ?prop ?o1 .
    ?o1 ?prop ?s1 .
    FILTER(?s1 != ?o1)
}'''

#ontology
print('### BASE ###')
g= Graph().parse('../datasets/NELL995/NELL.ontology.ttl')
#facts
g.parse('../temp/base_NELL_facts_materialized.nt', format='nt')

print('start querying')
for query in [disjointsQ, functionalQ, invFunctionalQ, symmetricQ, asymmetricQ]:
    res = g.query(query)
    print(len(res))

print('### Non monotonic extension ###')
g= Graph().parse('../datasets/NELL995/NELL.ontology.ttl')
#facts
g.parse('../temp/nmr_NELL_facts_materialized.nt', format='nt')

print('start querying')
for query in [disjointsQ, functionalQ, invFunctionalQ, symmetricQ, asymmetricQ]:
    res = g.query(query)
    print(len(res))