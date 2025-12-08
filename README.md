# NMRextension

**NMRextension** is a framework designed to refine and extend logical rules mined from Knowledge Graphs. It integrates with rule mining systems like **AMIE** and **AnyBURL** to perform rule materialization and metric calculation.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
  - [1. Rule Extension](#1-rule-extension)
  - [2. Materialization](#2-materialization)
  - [3. Evaluation](#3-evaluation)
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
### 1. Materialize rules
Run the extension script to process generate N% new triples (wrt the input size).

```bash
python materialize_top_rules.py
```

### 2. Apply rule
Run the script to generate top-100 predictions over the test set

```bash
python apply_rules.py
```

### 3. Metrics
Run the script to compute rank-based metrics over the test set

```bash
python compute_metrics.py
```

## Further details
### Nell995
 - schema and ontology reachable [here](https://github.com/bagindokemas/SAIKGC?tab=readme-ov-file)

### CSKG2.0
 - dataset and benchmark reachable [here](https://doi.org/10.5281/zenodo.14167682)
 - schema reachable [here](https://scholkg.kmi.open.ac.uk/cskg/ontology)

### Hetionet
 - Splits are generated from the pykeen.datasets.hetionet dataset
 - Metaedges from hetionet [release](https://github.com/hetio/hetionet/blob/main/describe/edges/metaedges.tsv)