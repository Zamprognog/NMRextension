# NMRextension

**NMRextension** is a framework designed to refine and extend logical rules mined from Knowledge Graphs. It integrates with rule mining systems like **AMIE** and **AnyBURL** to perform rule materialization and metric calculation.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
  - [1. Materialize rules](#1-materialize-rules)
  - [2. Apply rules](#2-apply-rule)
  - [3. Metrics](#3-metrics)
- [Inconsistent triples count](#inconsistent-triples-count)
- [Datasets](#datasets)
- [Acknowledgments](#acknowledgments)

## Prerequisites

This project utilizes both Python scripts and Java executables (`.jar`). Ensure you have the following installed:

* **Python 3.8+**
  * Pandas
  * rdflib
  * networkx
  * pykeen (for dataset splitting)
* **Java Runtime Environment (JRE)** (Required to run AMIE and AnyBURL)
* Any triple store (**GraphDB** has been used in the paper)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [this repository]()
    cd NMRextension
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Install rule miners**

   Currently supporting AnyBURL and AMIE3

4. **Download the datasets**
    You can download the dataset folder, as-is, at the following [address](https://doi.org/10.5281/zenodo.17854842).

If you are re-creating the datesets from datasets/<...>/data/
5. **Execute datasets/create_datasets.ipynb**

## Project Structure

* `datasets/<KG name>`: 
  * `data`: KG data, schema data, train/val/test splits 
  * `rules`: location where rule mining settings, and mined rules are stored
  * `predictions`: output location 
* `rule_extender/`: Core source code and logic for the extension algorithms.
* `materialize_top_rules.py`: Applies the rules to the dataset to infer new facts.
* `apply_rules.py`: Generates test predictions according to the chosen setting (monotonic/non-monotonic).
* `compute_metrics.py`: Calculates rank-based link prediction performance metrics.

## Usage

Warning: currently the files do not take command line input, the code needs to be modified accordingly in order to change the datasets/settings/rule sets

For mining AnyBURL rules, refer to the config-files in each dataset/rules folder
For mining AMIE rules run:
```console
java -jar amie3.5.1.jar -maxad 3 -mins -10 -minpca 0.1 -minc 0.1 -oute <train triples path> | tail -n +16 > datasets/<dataset>/rules/<dataset  name>_rules_amie.tsv
```
Then align them running align_rules.ipynb

### 1. Materialize rules
Run the extension script to process generate N% new triples (wrt the input size).

```bash
python materialize_top_rules.py
```

### 2. Apply rules
Run the script to generate top-100 predictions over the test set

```bash
python apply_rules.py
```

### 3. Metrics
Run the script to compute rank-based metrics over the test set

```bash
python compute_metrics.py
```
## Inconsistent triples count
In the reported results have been obtained in GraphDB, with rdfs-plus profile.

- Load the full graph + schema into the default graph
- Load the new triples in a named graph called 'newtriples'

### Queries
Functional count
```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT (COUNT(*) as ?total)
WHERE {
    select distinct ?s ?p ?o where {
      # Select the final triples ONLY from the <http://newtriples/> named graph.
      GRAPH <http://newtriples/> {
        ?s ?p ?o .
      }
      {
        SELECT ?s ?p
        WHERE {
          ?p rdf:type owl:FunctionalProperty .
          ?s ?p ?o_inner .
        }
        GROUP BY ?s ?p
        HAVING (COUNT(DISTINCT ?o_inner) > 1)
      }
	}
}
```
Domain/range count

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?domainCheckCount ?rangeCheckCount
WHERE {
    {
        SELECT (COUNT(*) AS ?domainCheckCount)
        WHERE {
            SELECT DISTINCT ?s ?p ?o 
            WHERE {
                GRAPH <http://newtriples/> {
                    ?s ?p ?o .
                }
                {
                    ?s a ?type1 .
                    ?p rdfs:domain ?dom .
                    ?type1 owl:disjointWith ?dom .
                }
            }
        }
    }
    {
        SELECT (COUNT(*) AS ?rangeCheckCount)
        WHERE {
            SELECT DISTINCT ?s ?p ?o 
            WHERE {
                GRAPH <http://newtriples/> {
                    ?s ?p ?o .
                }
                {
                    ?o a ?type2 .
                    ?p rdfs:range ?ran .
                    ?type2 owl:disjointWith ?ran .
                }
            }
        }
    }
}
```
Distinct inconsistent triples count
```sparlq 
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT (COUNT(*) AS ?totalDistinctTriples)
WHERE {
  {
    # --- INNER QUERY: FIND THE TRIPLES ---
    SELECT DISTINCT ?s ?p ?o
    WHERE {
      {
        # 1. Functional Property
        GRAPH <http://newtriples/> { ?s ?p ?o . }
        {
           SELECT ?s ?p WHERE {
             ?p a owl:FunctionalProperty .
             ?s ?p ?val .
           }
           GROUP BY ?s ?p
           HAVING (COUNT(DISTINCT ?val) > 1)
        }
      }
      UNION
      {
        # 2. Domain Violation
        GRAPH <http://newtriples/> { ?s ?p ?o . }
        ?s a ?type1 .
        ?p rdfs:domain ?dom .
        ?type1 owl:disjointWith ?dom .
      }
      UNION
      {
        # 3. Range Violation
        GRAPH <http://newtriples/> { ?s ?p ?o . }
        ?o a ?type2 .
        ?p rdfs:range ?ran .
        ?type2 owl:disjointWith ?ran .
      }
    }
  }
}
```


## Datasets
### Nell995
 - schema and ontology reachable [here](https://github.com/bagindokemas/SAIKGC?tab=readme-ov-file)

### CSKG2.0
 - dataset and benchmark reachable [here](https://doi.org/10.5281/zenodo.14167682)
 - schema reachable [here](https://scholkg.kmi.open.ac.uk/cskg/ontology)

### Hetionet
 - Splits are generated from the pykeen.datasets.hetionet dataset
 - Metaedges from hetionet [release](https://github.com/hetio/hetionet/blob/main/describe/edges/metaedges.tsv)

### YAGO4.5-10
- Data from the official [release](https://yago-knowledge.org/downloads/yago-4-5)
- Preprocessing:
  - yago-disjoints.ttl manually extracted from yago-schema.ttl
  - properties_d_r_f.csv manually extracted from yago-schema.ttl
  - convert yago-facts.hdt into .nt (rdf2hdt library)
  - remove all literals and triples not relevant for LP via preprocessing_scripts/filterOut_literals, obtaining yago4.5_triples.txt(or nt)
  - run filter_ntfile.ipynb to obtain yago4.5-10