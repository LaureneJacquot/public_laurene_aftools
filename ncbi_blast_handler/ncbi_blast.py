from config import display
from config import BLAST_RESULTS_DIR, WORKPLACE, TOOLS , display

import Bio
from Bio.Blast import NCBIWWW
from pathlib import Path
from uniprot import Uniprot
import time
from argparse import ArgumentParser
import os
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

uniprot = Uniprot()

@dataclass
class BlastJob:
    id: str
    sequence: str
    fasta: Optional[str] = None
    
    def __post_init__(self):
        if self.fasta is None:
            self.fasta = f">{self.id}\n{self.sequence}"


class BlastResultsManager : 
    def __init__(self, results_dir) : 
        self.results_dir = Path(results_dir)

    def result_exists(self, job_id) : 
        file = self.results_dir / f"{job_id}.xml"
        return file.exists()
    
    def save_result(self, result_handle, job_id) : 
        path = self.results_dir / f"{job_id}.xml"
        try : 
            with open(path, 'w') as output : 
                output.write(result_handle.read())
            display.info(f'Wrote job {job_id}')
            return output
        except Exception as e : 
            display.error(f'Failed to save job {job_id} to location {path}. Error : {e}')
            raise


class NCBIBlastClient :
    def __init__(self, results_dir, delay) : 
        self.results_manager = BlastResultsManager(results_dir)
        self.uniprot = Uniprot()
        self.delay = delay

    def submit_single(self, job, program : str = 'blastp', database : str = 'nr') : 
        try:
            display.info(f"Submitting BLAST for {job.id}")
            result_handle = NCBIWWW.qblast(program, database, job.fasta)
            return result_handle
        except Exception as e : 
            display.error(f'Job submission failed for {job.id} because of error : {e}')

    def create_job_from_uniprot(self, id) : 
        try :
            _ , data = uniprot.gets_taxonomic_id_robust(id)
            _, full_name, _, sequence = self.uniprot.gets_name_and_sequence_from_data(id, data)
            full_name.replace(' ', '_')
            return BlastJob(id=id or full_name, sequence=sequence)
        
        except Exception as e :
            display.error(f'Failed to retrieve data for Uniprot id : {id} : {e}')
            raise

    def process_single_job(self, id : Optional[str] = None, sequence : Optional[str]= None, skip = True) : 
        if id and not sequence : job = self.create_job_from_uniprot(id)
        elif sequence and id : job = BlastJob(id=id, sequence=sequence)
        else : raise ValueError("You should provide either an id, or a sequence and an id.")

        if skip and self.results_manager.result_exists(job.id) : 
            display.warning(f'Job {id} already exists. Skipping this job.')
            return self.results_manager.results_dir / f'{job.id}.xml'
        
        result_handle = self.submit_single(job)
        return self.results_manager.save_result(result_handle, job.id)

    def process_batch_jobs(self, jobs : List[BlastJob], skip : bool = True) : 
        results = []

        for i, job in enumerate(jobs) : 
            try :
                if skip and self.results_manager.result_exists(job.id) : 
                    display.warning(f'Job {id} already exists. Skipping this job.')
                    continue 

                result_handle = self.submit_single(job)
                result_path = self.results_manager.save_result(result_handle, job.id)
                results.append(result_path)
            
                if i < len(jobs) - 1 : 
                    display.info(f'Waiting {self.delay} before next submission.')
                    time.sleep(self.delay)

            except Exception as e:
                display.error(f"Failed to process job {job.id}: {e}")
                continue

        display.info(f"Batch is done. We have processed {len(results)} jobs.")
        return results


    


class JobFileParser : 

    def parse_id_file(id_file_path) : 
        try :
            with open(id_file_path, 'r') as file : 
                ids = [line.strip() for line in file.readlines() if line.strip()]
                display.info(f'We have loaded {len(ids)} ids from {id_file_path}')
                return ids 
        except Exception as e : 
            display.error(f'Loading of ids from {id_file_path} has failed : {e}')
            raise

    def parse_sequence_file(seq_file_path) :
        sequences = {}

        try:
            with open(seq_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split(':', 1)
                    if len(parts) != 2:
                        display.warning(f"Skipping malformed line {line_num}: {line}")
                        continue
                    
                    job_id, sequence = parts[0].strip(), parts[1].strip()
                    sequences[job_id] = sequence
            
            display.info(f"We have loaded {len(sequences)} sequences from {seq_file_path}")
            return sequences
        except Exception as e:
            display.error(f"We failed to parse sequence file {seq_file_path}: {e}")
            raise


def create_jobs_from_ids(uniprot_ids, client: NCBIBlastClient) -> List[BlastJob]:
    jobs = []
    for uniprot_id in uniprot_ids:
        try:
            job = client._create_job_from_uniprot_id(uniprot_id)
            jobs.append(job)
        except Exception as e:
            display.error(f"Skipping {uniprot_id} due to error: {e}")
    return jobs


def create_jobs_from_sequences(sequences) -> List[BlastJob]:
    return [BlastJob(id=job_id, sequence=seq) 
            for job_id, seq in sequences.items()]


def filter_existing_jobs(jobs: List[BlastJob], results_manager: BlastResultsManager) -> List[BlastJob]:
    filtered = [job for job in jobs if not results_manager.result_exists(job.id)]
    skipped_count = len(jobs) - len(filtered)
    
    if skipped_count > 0:
        display.info(f"Skipping {skipped_count} jobs with existing results")
    
    return filtered


def main() : 

    display.header("\nNCBI BLAST submission tool developed by Laurène in Pr. Doye's group in Oxford\n")

    parser = ArgumentParser('Script for sending BLAST queries onto the NCBI website and then retrieving everything and saving them to files')
    parser.add_argument(
        '--rewrite', 
        action='store_true',
        default = False, 
        help='Reprocess existing results (default: skip existing)'
    )
    parser.add_argument('mode', choices = ['single', 'batch'], help='If running in single you need to provide a uniprot id or a single sequence. In batch you need a file with a list of ids or a list of sequences.')
    parser.add_argument('-i', '--id', default = None ,help='The uniprot id of the protein you want to BLAST')
    parser.add_argument('-s', '--sequence', default = None , help='The sequence of the protein you want to BLAST')
    parser.add_argument('-n', '--name', default = None, help = 'A name for your job with the explicit sequence')
    parser.add_argument('-if', '--id_file', default = None, help = 'A file in your workplace containing a list of ids for when you run in batch mode')
    parser.add_argument('-sf', '--seq_file', default = None, help = 'A file in your workplace containing a list of sequences for when you run in batch mode')
    parser.add_argument('-d', '--delay', default = 5, help = 'The delay between job submissions')
    args = parser.parse_args()

    if args.mode == 'single':
        if not args.id and not args.sequence:
            parser.error("For single mode we require either --id or --sequence")
        if args.id and args.sequence:
            parser.error("Please provide either --id or --sequence, not both")
        if args.sequence and not args.name:
            parser.error("For sequence mode we require --name")
        if args.id_file or args.seq_file:
            parser.error("For single mode we don't use file arguments")
    
    elif args.mode == 'batch':
        if not args.id_file and not args.seq_file:
            parser.error("For batch mode we require either --id_file or --seq_file")
        if args.id_file and args.seq_file:
            parser.error("Please provide either --id_file or --seq_file, not both")
    
    results_dir = Path(BLAST_RESULTS_DIR)
    client = NCBIBlastClient(results_dir, delay=args.delay)
    
    try:
        if args.mode == 'single':
            job_id = args.id or args.name
            result_path = client.process_single_job(
                id=job_id,
                sequence=args.sequence,
                skip=not args.rewrite
            )
            display.info(f"Single job completed. We have saved the results saved to {result_path.name}")
            
        elif args.mode == 'batch':
            if args.id_file:
                file_path = Path(WORKPLACE) / args.id_file
                uniprot_ids = JobFileParser.parse_id_file(file_path)
                jobs = create_jobs_from_ids(uniprot_ids, client)
            else: 
                file_path = Path(WORKPLACE) / args.seq_file
                sequences = JobFileParser.parse_sequence_file(file_path)
                jobs = create_jobs_from_sequences(sequences)
            
            if not args.rewrite:
                jobs = filter_existing_jobs(jobs, client.results_manager)
            
            if jobs:
                result_paths = client.process_batch_jobs(jobs, skip=not args.rewrite)
                display.info(f"We have completed the batch processing. {len(result_paths)} results saved.")
            else:
                display.info("No jobs to process unfortunately :(")
                
    except Exception as e:
        display.error(f"Application error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())