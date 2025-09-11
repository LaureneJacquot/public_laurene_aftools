This is a repository for some of the tools I developed in Oxford. It is in active development, however feel free to clone it and to use it / fix issues if you see them !

For interpro_batch_analyzer : 
- You need to change the exports.sh file and to source it, in order to indicate the correct place for the code to run / save results to.
- You can run the test (after having sourced exports.sh) by running :

python main.py pipeline -f test.fasta 

- If you have a fasta of the protein(s) you are interested in, you can either run all the pipeline, or you can do it in differents steps (see main.py for the flags)
