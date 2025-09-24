from src.interpro_client import InterproClient , ClientConfig
from src.interpro_analysis import InterproAnalyzer, AnalysisConfig
from src.config import INTERPRO_RESULTS_DIR , WORKPLACE
from src.config import display

import argparse
from pathlib import Path
import sys
from Bio import SeqIO
import ast



def reads_fasta(file) : 
    file = Path(WORKPLACE) / file
    sequences = SeqIO.parse(open(file), 'fasta')
    d = {}
    for fasta in sequences : 
        name, sequence = fasta.id, str(fasta.seq)
        d[name.strip()] = sequence.strip()
    return d



if __name__ == '__main__' : 

    #Setup

    results_dir = Path(INTERPRO_RESULTS_DIR)
    workplace = Path(WORKPLACE)
    display.header("Toolwr for interacting with the Interpro server.\nDeveloped by Laurène in Pr. Doye's group at the University of Oxford\n")

    parser = argparse.ArgumentParser('Script for interacting with the Interpro server')
    parser.add_argument('-s', '--sequence', default = None, help = 'a sequence you want to submit to the Interpro server')
    parser.add_argument('-t', '--title', default = None, help = 'the title of the job you want to interact with')
    parser.add_argument('runmode', choices = ['submit', 'submitall', 'refresh', 'autorefresh', 'analysis', 'analysisall', 'summary', 'write', 'pipeline'], help = 'The mode you want to operate in')
    parser.add_argument('-f', '--file', default = None, help = 'a fasta file for all your systems. this should be faster than just running this entire script in submit mode with a single title/sequence each time')
    parser.add_argument('-k', '--keywords', type=ast.literal_eval , default= ['SIGNAL_PEPTIDE'], help='A list of each keyword you want to parse your files for.')
    args=parser.parse_args()

    keywords = args.keywords

    client_config = ClientConfig(
        batch_size=100 , 
        results_dir=results_dir , 
        workplace=workplace , 
    )

    analysis_config = AnalysisConfig(
        results_dir=results_dir,
        workplace=workplace,
        keywords=keywords
        )

    client = InterproClient(client_config)
    analyzer = InterproAnalyzer(analysis_config)

    sequence = args.sequence
    title = args.title
    mode = args.runmode
    file = args.file

    display.info(f'Running in mode : {mode}\n')
    
    #Treating the modes one by one

    if mode == 'submit' : 
        if not sequence or not title : 
            display.error('A sequence and a title are needed in submit mode')
            sys.exit()
        single_info={}
        job_id = client.submit(title, sequence)
        display.info(f'Submitting {title} with job id : {job_id}')
        single_info[title] = [sequence, id]
        client.writes_interpro_log(single_info)

    elif mode == 'submitall' : 
        if file is None : 
            display.error('A fasta file is needed for submitall mode')
            sys.exit()
        d = reads_fasta(file)
        infos = client.batch_submits(d)

    elif mode == 'refresh' : 
        client.refresh()
        client.updates_data()

    elif mode == 'autorefresh' : 
        client.auto_refresh()
        client.updates_data()

    elif mode == 'analysis' : 
        if title == None : 
            display.error('You need a title for analysis mode')
            sys.exit()
        analyzer.analysis(title, mode)
    
    elif mode == 'analysisall' : 
        analyzer.batch_analysis(mode)
    
    elif mode == 'summary' : 
        analyzer.summary()

    elif mode == 'write' : 
        analyzer.writes_ids_txt()
        analyzer.counts_ids_txt()

    elif mode == 'pipeline' : 
        if file is None : 
            display.error('A fasta file is needed for submitall mode')
            sys.exit()
        d = reads_fasta(file)
        infos = client.batch_submits(d)

        client.auto_refresh()
        client.updates_data()

        analyzer.batch_analysis(mode)

        analyzer.summary()

        analyzer.writes_ids_txt()
        analyzer.counts_ids_txt()



