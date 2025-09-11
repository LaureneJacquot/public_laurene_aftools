# Oxford Bioinformatics Tools

Tools developed in my first year of master's at PSL, during my internship at the University of Oxford.

## InterPro Batch Analyzer

A Python tool for high-throughput protein functional analysis using the InterPro API. Automates submission, monitoring, and results retrieval for large protein datasets.

### Features
- Concurrent processing of multiple protein sequences
- Automated job status monitoring and result retrieval
- Configurable analysis parameters (signal peptides, transmembrane domains, etc.)
- Comprehensive logging and error handling

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
python main.py pipeline -f your_proteins.fasta -k ['KEYWORD_1', 'KEYWORD_2', 'KEYWORD_3']
python main.py autorefresh
python main.py analysisall
python main.py summary #Optional
python main.py write #Optional
```

Test example : 
in interpro_batch_analyzer :
```
mkdir -p test/results
export INTERPRO_RESULTS_DIR=$(pwd)/test/results
python main.py pipeline -f test.fasta
```
There is an exports.sh file in interpro_batch_analyzer : you can modify it and then just source at the start of every shell session (or add it to your PATH)
```
source exports.sh
```
You also need to make sure that you are passing an INTERPRO_COOKIES value in order to run the code. One is provided in exports.sh by default, however it might expire at some point. To find your own cookie, you can go to DevTools. 





