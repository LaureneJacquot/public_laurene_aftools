This repository is still in development - some mistakes might still exist in the README or in the codes themselves. Please signal any issue you find !

# Oxford Bioinformatics Tools

Tools made in my first year of master's at PSL, during my internship at the University of Oxford.

## InterPro Batch Analyzer

This is a Python tool to analyse protein data using the InterPro API. It automates submission, monitoring, and results retrieval for large protein datasets.

### Features
- Concurrent processing of multiple protein sequences
- Automated job status monitoring and result retrieval
- Configurable analysis parameters

### Installation

1. Clone the repository:
```bash
git clone https://github.com/LaureneJacquot/public_laurene_aftools.git
cd public_laurene_aftools/interpro_batch_analyzer
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Export your variables:
```bash
export WORKPLACE=/path/to/your/workspace
export INTERPRO_RESULTS_DIR=/path/to/results
```
### Usage :
1. Full pipeline : 
```
python main.py pipeline -f your_proteins.fasta
```
and with custom keywords : 
```
python main.py pipeline -f your_proteins.fasta -k ['KEYWORD_1', 'KEYWORD_2', 'KEYWORD_3']
```
2. Step-by-step :
```
python main.py submitall -f your_proteins.fasta -k ['KEYWORD_1', 'KEYWORD_2', 'KEYWORD_3']
python main.py autorefresh
python main.py analysisall
python main.py summary #Optional
python main.py write #Optional
```

Test example : 
in interpro_batch_analyzer :
```
mkdir -p test/results
export INTERPRO_RESULTS_DIR="$(pwd)/test/results"
export WORKPLACE="$(pwd)/test"
python main.py pipeline -f test.fasta
```
There is an exports.sh file in interpro_batch_analyzer : you can modify it and then just source at the start of every shell session (or add the content to your PATH)
```
source exports.sh
```
You also need to make sure that you are passing an INTERPRO_COOKIES value in order to run the code. You can put it in the exports.sh file, as INTERPRO_COOKIES='[your cookie here]'
To find the cookie you can just go on the Interpro website and open DevTools. 



## NCBI BLAST Submission and UniProt Data Retrieval Tools

This is a set of Python tools for automating BLAST queries against the NCBI database and retrieving protein information from UniProt. 

### Features

#### BLAST Submission Tool (`blast_client.py`)
- Submit single or batch BLAST queries to NCBI
- Support for UniProt ID lookup or direct sequence input

#### UniProt Data Retrieval (`uniprot.py`)
- Fetch protein information from UniProt REST API
- Batch processing with concurrent requests
- Extract protein names, sequences, and lengths
- Filter proteins by name patterns

### Requirements

```bash
pip install biopython requests urllib3
```

### Setup
1. Ensure the results directory exists:
```bash
mkdir -p /path/to/blast/results
```

### Usage

#### BLAST Submission Tool

##### Single Query Mode

**Using UniProt ID:**
```bash
python blast_client.py single --id P12345
```

**Using custom sequence:**
```bash
python blast_client.py single --sequence "MKLLVVGVGVGVGVG..." --name "my_protein"
```

##### Batch Mode

**Using UniProt ID file:**
```bash
python blast_client.py batch --id_file uniprot_ids.txt
```

**Using sequence file:**
```bash
python blast_client.py batch --seq_file sequences.txt
```

##### Command Line Options

- `--rewrite`: Reprocess existing results (default: skip existing)
- `--delay`: Delay between batch submissions in seconds (default: 5)
- `--id`: UniProt ID for single mode
- `--sequence`: Protein sequence for single mode
- `--name`: Job name when using custom sequence
- `--id_file`: File containing UniProt IDs for batch mode
- `--seq_file`: File containing sequences for batch mode

#### File Formats

##### UniProt ID File (`uniprot_ids.txt`)
```
P12345
Q67890
A11111
B22222
```

##### Sequence File (`sequences.txt`)
```
protein1: MKLLVVGVGVGVGVGVGAAA...
protein2: ATVKFKYKGEEKEVDISKIKK...
protein3: MKKLLAAATTVVGGHHII...
```


### Output

#### BLAST Results
- Results saved as XML files in the configured results directory
- Filename format: `{job_id}.xml`
- Compatible with BioPython BLAST parsers













