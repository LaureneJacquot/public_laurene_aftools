from config import WORKPLACE, TOOLS , display
import requests
from concurrent.futures import as_completed, ThreadPoolExecutor
import re
from urllib3.util.retry import Retry
from pathlib import Path
from requests.adapters import HTTPAdapter
import urllib3
import ssl

class Uniprot : 
    def create_session_with_retry(self):

        session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        return session

    def gets_taxonomic_id_robust(self, uniprot_id, session=None):
        display.info(f'Getting {uniprot_id}')

        if session is None:
            session = self.create_session_with_retry()
        
        url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
        
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return uniprot_id, response.json()
        except requests.exceptions.SSLError:
            display.waring(f"SSL error for {uniprot_id}, trying without SSL verification...")

            try:
                response = session.get(url, verify=False, timeout=30)
                response.raise_for_status()
                return uniprot_id, response.json()
            except Exception as e:
                display.warning(f"Still failed for {uniprot_id} without SSL: {e}")
                
                try:
                    import ssl
                    session.mount('https://', HTTPAdapter(
                        socket_options=[(ssl.SOL_SOCKET, ssl.SO_KEEPALIVE, 1)]
                    ))
                    response = session.get(url, timeout=30)
                    response.raise_for_status()
                    return uniprot_id, response.json()
                except Exception as e2:
                    display.warning(f"Final attempt failed for {uniprot_id}: {e2}")
                    return uniprot_id, None

    def gets_taxonomic_id(id) : #L : this is for proteins
        
        id = id.strip()
        url = f"https://rest.uniprot.org/uniprotkb/{id}.json"
        #print(url)
        response = requests.get(url)
        if response.ok : 
            data = response.json()
        else:
            display.warning(f"Request for id {id} failed with status code {response.status_code}")
            data = None
        return id, data


    def gets_name_from_data(self, id, data):
        if not data:
            return None
        
        name = ''
        if 'proteinDescription' in data:
            protein_desc = data['proteinDescription']

            if 'recommendedName' in protein_desc:
                recommended = protein_desc['recommendedName']
                if 'fullName' in recommended and 'value' in recommended['fullName']:
                    name = recommended['fullName']['value']
                    return id, name

            if 'submissionNames' in protein_desc:
                submission_names = protein_desc['submissionNames']
                if isinstance(submission_names, list) and len(submission_names) > 0:
                    first_submission = submission_names[0]
                    if 'fullName' in first_submission and 'value' in first_submission['fullName']:
                        name = first_submission['fullName']['value']
                        return id, name
        return id, name

    def batch_gets_name(self, ids_path, names_path) : 
        ids = []
        all_data = {}
        store = {}

        with open(ids_path, 'r') as ids_file : 
            lines = ids_file.readlines()
            for id in lines : 
                id = id.strip()
                if not id.startswith('#') : ids.append(id)

        with ThreadPoolExecutor() as executor : 
            futures = {executor.submit(self.gets_taxonomic_id_robust, id) for id in ids}
            for future in as_completed(futures) : 
                id, data = future.result()
                all_data[id] = data

        with ThreadPoolExecutor() as executor : 
            futures = {executor.submit(self.gets_name_from_data, id, data) for id, data in all_data.items()}

            for future in as_completed(futures) : 
                if not future.result() == None  : id, f = future.result() 
                store[id] = f

        with open(names_path, 'w') as names_path : 
            for id, f in store.items() : 
                string = f'{id} : {f}\n'
                names_path.write(string)

    def gets_name_and_sequence_from_data(self, id, data):
        if not data:
            return None
        
        name = ''

        if 'sequence' in data : 
            if 'length' in data['sequence'] : 
                length = data['sequence']['length']
                if 'value' in data['sequence'] : sequence = data['sequence']['value']
                else : sequence = None
                #print(f'{id} : {length}')
            else : length = None

        if 'proteinDescription' in data:
            protein_desc = data['proteinDescription']

            if 'recommendedName' in protein_desc:
                recommended = protein_desc['recommendedName']
                if 'fullName' in recommended and 'value' in recommended['fullName']:
                    name = recommended['fullName']['value']
                    return id, name, length, sequence

            if 'submissionNames' in protein_desc:
                submission_names = protein_desc['submissionNames']
                if isinstance(submission_names, list) and len(submission_names) > 0:
                    first_submission = submission_names[0]
                    if 'fullName' in first_submission and 'value' in first_submission['fullName']:
                        name = first_submission['fullName']['value']
                        return id, name, length, sequence
                    

        return id, name, length, sequence

    def batch_gets_name_and_sequence(self, ids_path, names_path) : 
        ids = []
        all_data = {}
        lengths = {}
        store = {}
        sequences = {}

        with open(ids_path, 'r') as ids_file : 
            lines = ids_file.readlines()
            for id in lines : 
                id = id.split(':')[0].strip()
                if not id.startswith('#') : ids.append(id)


        with ThreadPoolExecutor() as executor : 
            futures = {executor.submit(self.gets_taxonomic_id_robust, id) for id in ids}
            for future in as_completed(futures) : 
                id, data = future.result()
                all_data[id] = data
                

        with ThreadPoolExecutor() as executor : 
            futures = {executor.submit(self.gets_name_and_sequence_from_data, id, data) for id, data in all_data.items()}

            for future in as_completed(futures) : 
                if not future.result() == None  : id, f, l, s = future.result() 
                store[id] = f
                lengths[id] = l
                sequences[id] = s

        with open(names_path, 'w') as names_path : 
            for id, f in store.items() : 
                if id in lengths : 
                    l = lengths[id]
                    string = f'{id} : {f} : {l}\n'
                    names_path.write(string)
        return sequences


    def looks_at_names() : 
        with open(names_path, 'r') as names : 
            lines = names.readlines()
        
        filtered = []

        for line in lines : 
            if len(line.split(':')) > 1 : name = line.split(':')[1].strip()
            # if 'Uncharacterized' in name or 'S-layer' in name : 
            #     filtered.append(line)

            if 'containing' in name or 'Domain' in name or 'Containing' in name or 'domain' in name : 
                filtered.append(line)
        
        print(len(filtered))
        
        with open(filtered_path, 'w') as file : 
            for f in filtered : 
                file.write(f)


            

if __name__ == '__main__' : 
    names_path = Path(WORKPLACE) / 'names.txt'
    ids_path = Path(WORKPLACE) / 'ids.txt'
    filtered_path = Path(WORKPLACE) / 'domain_containing.txt'

    uniprot = Uniprot()

    sequences = uniprot.batch_gets_name_and_sequence(ids_path, names_path)
    ids_path = Path(WORKPLACE) / 'domain_containing.txt'
    uniprot.looks_at_names()
    


