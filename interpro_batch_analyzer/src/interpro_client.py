from pathlib import Path
import json
from concurrent.futures import as_completed, ThreadPoolExecutor
import requests, time
import os
from typing import List, Optional
from dataclasses import dataclass

from .config import WORKPLACE , INTERPRO_RESULTS_DIR , INTERPRO_COOKIES, display


@dataclass
class ClientConfig:
    batch_size: Optional[int] = None
    results_dir: Optional[str] = None
    workplace: Optional[str] = None

class InterproClient : 

    def __init__(self, config : ClientConfig) : 
        self.config = config 

        if self.config.results_dir is not None:
            self.results_dir = Path(self.config.results_dir)
        else:
            self.results_dir = Path(INTERPRO_RESULTS_DIR)  
            
        if self.config.workplace is not None:
            self.workplace = Path(self.config.workplace)
        else:
            self.workplace = Path(WORKPLACE)  

        if self.config.batch_size is not None : 
            self.batch_size = self.config.batch_size
        else : self.batch_size = 100

        self.log_path = Path(WORKPLACE) / 'interpro_log.json'


        init = {
            "list": [
                ]
            }
        
        if not self.log_path.exists():  
            with open(self.log_path, 'w') as f:
                json.dump(init, f, indent=2) 

        
        cookie_string = INTERPRO_COOKIES


        self.cookies = dict(
            item.strip().split("=", 1)
            for item in cookie_string.split(";")
        )

        self.__request = {
            "headers": {
            'content-type': 'application/x-www-form-urlencoded',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
            },
            "data": {
                'email': 'interpro-team@ebi.ac.uk',
                'title': '',
                'sequence' : '' ,
                'stype' : 'p' , 
                'appl': [
            "CDD", "HAMAP", "NCBIfam", "Panther", "PrositeProfiles", "PrositePatterns", "PRINTS", "PfamA",
            "PIRSF", "SFLD", "SMART", "Gene3d", "SuperFamily", "AntiFam", "Coils", "FunFam", "MobiDBLite",
            "Phobius", "PIRSR", "SignalP_EUK", "SignalP_GRAM_POSITIVE", "SignalP_GRAM_NEGATIVE", "TMHMM"
                ] ,
                'goterms' : 'true' , 
                'pathways' : 'true'

            }
        }


    def submit(self, title, sequence) -> str:
        data = self.__request['data']
        data['title'] = title
        data['sequence'] = sequence
        response = requests.post(
            'https://www.ebi.ac.uk/Tools/services/rest/iprscan5/run',
            cookies = self.cookies,
            headers = self.__request['headers'],
            data = data
        )

        if response.status_code != 200 : 
            display.error(f"Error submitting {title} : {response.text}")
            return None
        return response.text
    
    def batch_submits(self, d) : 
        display.info(f"Starting batch submit with {len(d)} proteins:")
        for title in sorted(d.keys()):  
            display.info(f"  - {title}")

        print()
        infos = {}
        batch_size = self.batch_size 

        def splits_d_into_dictionnary(d):
            dictionnary = {}
            i = 0
            name = 'd0'
            dictionnary[name] = {}
            for item in d:
                if len(item.split('|')) > 1:
                    clean_title = item.split('|')[1]
                else:
                    clean_title = item
                sequence = d[item]
                i += 1
                if i % batch_size == 0:
                    name = str(f'd{int(name[1:]) + 1}')
                    dictionnary[name] = {}
                dictionnary[name][clean_title] = sequence 
            return dictionnary
        
        dictionnary = splits_d_into_dictionnary(d)

        p = Path(WORKPLACE) / 'dictionnary.txt'
        with open(p, 'w') as p : 
            json.dump(dictionnary, p, indent=2)


        #d being a dictionnary like : title : sequence
        with ThreadPoolExecutor(max_workers=20) as executor : 
        
            for name in dictionnary : 
                #display.info(f'Submitting {name} part of dictionnary')
                futures = {}
                for title, sequence in dictionnary[name].items() : 
                    e = executor.submit(self.submit, title, sequence)
                    futures[e] = title

                batch_infos = {}
                for future in as_completed(futures):
                    id = future.result()
                    if id is not None : 
                        title = futures[future]
                        sequence = dictionnary[name][title]
                        batch_infos[title] = [sequence, id]
                
                infos.update(batch_infos)

                #display.info(f'Saving batch {name} : {len(batch_infos)} items submitted')
                try:
                    self.writes_interpro_log(batch_infos)
                    #display.info(f'Wrote log file for batch {name}')
                except Exception as e:
                    display.warning(f'Cannot write log file for batch {name}: {e}')
                batch_infos = {}

        return infos

    
    def gets_status(self, id) : 
        url = f'https://www.ebi.ac.uk/Tools/services/rest/iprscan5/status/{id}'
        response = requests.get(url)
        return response.text
    
    def gets_data_json(self, id) : 
        url = f'https://www.ebi.ac.uk/Tools/services/rest/iprscan5/result/{id}/json'
        #display.info(url)
        response = requests.get(url)
        if response.status_code != 200 : 
            display.error(f"Error getting data from {id} : {response.text}")
            return None
        return response.json()
    
    def refresh(self):
        changed = []
        with open(self.log_path, 'r') as log:
            all_data = json.load(log)
        
        running = {item['title']: item['id'] for item in all_data['list'] 
                if item['status'] == 'RUNNING' or item['status'] == 'QUEUED'}
        
        def refresh_one(item_id):
            #display.info(f'Status of job {item_id} : {self.gets_status(item_id)}')
            return self.gets_status(item_id)

        with ThreadPoolExecutor() as executor:  
            futures = {executor.submit(refresh_one, id): title 
                    for title, id in running.items()}

            for future in as_completed(futures):
                title = futures[future]
                new_status = future.result()

                for item in all_data['list']:
                    if item['title'] == title:
                        store = item['status']
                        item['status'] = new_status
                        if new_status != store :
                            changed.append(title)
                        break

        with open(self.log_path, 'w') as log:
            json.dump(all_data, log, indent=2)
        
        return changed
    
    def auto_refresh(self) : 

        def is_all_finished() : 
            finished = True 
            with open(self.log_path, 'r') as log : 
                data = json.load(log)
                for item in data['list'] : 
                    if item['status'] not in ['FINISHED', 'FAILED', 'ERROR']:
                        finished = False
            if finished == False : display.error(f'Finished : {finished}')
            elif finished == True : display.ok(f'Finished : {finished}')

            return finished

        finished = False
        while not finished:
            self.refresh()
            finished = is_all_finished()
            if not finished:  
                display.info('\nSleeping for 10 more seconds\n')
                time.sleep(10)

    def writes_interpro_log(self, infos):
    # Format of infos should be title : [sequence, id]
        with open(self.log_path, 'r+') as log:
            all_data = json.load(log)
        
        existing_titles = {item['title'] for item in all_data['list']}
        
        for original_title in infos:
            clean_title = original_title.split('|')[1] if '|' in original_title else original_title
            
            if clean_title in existing_titles:
                display.warning(f"Duplicate submission detected: {clean_title}")
                continue
            
            sequence = infos[original_title][0]
            job_id = infos[original_title][1]
            
            if job_id is None:
                display.warning(f'Skipping {clean_title}: submission failed')
                continue
            
            new = {
                'title': clean_title,
                'status': 'RUNNING',
                'id': job_id,
                'sequence': sequence,
                'analysis': {}
            }
            all_data['list'].append(new)
        
        with open(self.log_path, 'w') as log:
            json.dump(all_data, log, indent=2)


    def updates_data(self) : 
        files = os.listdir(self.results_dir)
        to_update = {}

        with open(self.log_path, 'r') as log : 
            all = json.load(log)
            for item in all['list'] :
                if item['status'] == 'FINISHED' and f'{item["title"]}.json' not in files : to_update[item['title']] = item['id']

        def updates_one(title, id, result_dir) : 
            data = self.gets_data_json(id)
            if data : 
                path = result_dir.joinpath(f'{title}.json')
                with open(path, 'w') as file : json.dump(data, file, indent=2)
                #display.info(f'Created data json file for {title}')
        
        with ThreadPoolExecutor() as executor : 
            futures = {executor.submit(updates_one, title, id, self.results_dir): title 
                    for title, id in to_update.items()}
            for future in as_completed(futures):
                future.result()
