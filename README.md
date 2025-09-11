This is a repository for some of the tools I developed in Oxford. It is in ACTIVE development, however feel free to clone it and to use it / fix issues if you see them !

For interpro_batch_analyzer : 
- To use this tool, you need to change the interpro_batch_analyzer/exports.sh file and to source it, in order to indicate the correct place for the code to run / save results to.
- You can run the test by setting INTERPRO_RESULTS_DIR to [somewhere]/public_laurene_aftools/interpro_batch_analyzer/test/results (and creating that 'results' directory yourself since it is not included here). Then you can run :

python $TOOLS/main.py pipeline -f test.fasta 

which should analyze 16 proteins from Uniprot by parsing them for a signal peptide flag.

- If you have a fasta of the protein(s) you are interested in, you can either run all the pipeline, or you can do it in differents steps (see main.py for the flags)
- If you want to scan the proteins for other information than signal peptides, you can include that in the command line with the -k argument (pass the keywords you want to parse for as a list of strings, such as ['SIGNAL_PEPTIDE', 'TMHelix', 'NON_CYTOPLASMIC_DOMAINS'] ). You NEED to be sure that these exact same strings are going to show up in the Interpro output files (for example, do not pass 'TMhelix' instead of 'TMHelix' as the tool will then miss the information). 


