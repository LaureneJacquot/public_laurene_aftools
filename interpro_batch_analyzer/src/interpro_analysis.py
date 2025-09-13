from pathlib import Path
import json
from dataclasses import dataclass
from typing import List, Optional
from concurrent.futures import as_completed , ThreadPoolExecutor
import os 

from .config import WORKPLACE , INTERPRO_RESULTS_DIR , display

@dataclass
class AnalysisConfig:
    results_dir: Optional[str] = None
    workplace: Optional[str] = None
    keywords: List[str] = None

class InterproAnalyzer:

    def __init__(self, config: AnalysisConfig):
        self.config = config
        
        if self.config.results_dir is not None:
            self.results_dir = Path(self.config.results_dir)
        else:
            self.results_dir = Path(INTERPRO_RESULTS_DIR)  
            
        if self.config.workplace is not None:
            self.workplace = Path(self.config.workplace)
        else:
            self.workplace = Path(WORKPLACE)  

        self.keywords = list(self.config.keywords)

    
        self.log_path = self.workplace / 'interpro_log.json'
        self.ids_path = Path(WORKPLACE) / 'ids.txt'
        
        init = {
            "list": [
                ]
            }
        
        if self.config.keywords:
            for keyword in self.config.keywords : 
                path = Path(WORKPLACE) / f'summary_{keyword.lower()}.json'
                setattr(self, keyword.lower(), path)

                if not path.exists():  
                    with open(path, 'w') as f:
                        json.dump(init, f, indent=2) 
                        #display.warning(f'Warning : we have created a file for {keyword.lower()} at location : {path} because it did not exist')



    def find_keywords(self, json_file) : 
        files = os.listdir(self.results_dir)
        all = {
            keyword.lower() : False for keyword in self.keywords
        }

        name = json_file

        #this needs to be tested
        if json_file not in files :  
            display.warning(f'{json_file} not in {self.results_dir}. Data analysis for this system will be skipped.')
            all = {
                keyword.lower() : 'File not found' for keyword in self.keywords
            }
            return all
        
        path = self.results_dir.joinpath(json_file)
        with open(path, 'r') as json_file : 
            data = json.load(json_file)
            for keyword in self.keywords : 
                for item in data['results'][0]['matches'] : 
                        if keyword in item['signature']['accession'] : 
                            all[keyword.lower()] = True

        return all




    def analysis(self, title, mode) :
        analysis_data = self.find_keywords(f'{title}.json')
        if mode == 'analysis' : 
            with open(self.log_path, 'r+') as log : 
                data = json.load(log)
                for item in data["list"] : 
                    if item ['title'] == title : 
                        item['analysis'] = analysis_data
                log.seek(0)
                json.dump(data, log, indent=2)

        return analysis_data




    def batch_analysis(self, mode) :
        titles = []
        all_analysis_data = {}

        with open(self.log_path, 'r+') as log : 
            all = json.load(log)
            for item in all['list'] : 
                if len(item['title'].split('|')) > 1 : title = item['title'].split('|')[1]
                else : title = item['title']
                titles.append(title)

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(self.analysis, title, mode): title 
                    for title in titles}
            for future in as_completed(futures) : 
                analysis_data = future.result()
                all_analysis_data[futures[future]] = analysis_data
        
        with open(self.log_path, 'r+') as log : 
            all = json.load(log)

            for item in all['list'] : 
                if len(item['title'].split('|')) > 1 : 
                    title = item['title'].split('|')[1]
                else : 
                    title = item['title']

                if title in all_analysis_data:
                    item['analysis'] = all_analysis_data[title]
            
            log.seek(0)
            log.truncate()
            json.dump(all, log, indent=2)



    def summary(self) : 
        lists_dict = {
            keyword.lower() : [] for keyword in self.keywords
        }

        with open(self.log_path, 'r') as log : 
            all = json.load(log)
            for item in all['list'] : 
                for keyword in self.keywords : 
                    if keyword.lower() in item['analysis'] and item['analysis'][keyword.lower()] == True : 
                        lists_dict[keyword.lower()].append(item)
                        continue


        for keyword in self.keywords : 
            summary_path = getattr(self, keyword.lower())
            with open(summary_path, 'r+') as summary : 
                data = json.load(summary)
                for item in lists_dict[keyword.lower()] : 
                    data['list'].append(item)
                summary.seek(0)
                json.dump(data, summary, indent=2)

    
    def writes_ids_txt(self) : 
        ids = []

        for keyword in self.keywords : 
            ids.append(f'#{keyword}')
            summary_path = getattr(self, keyword.lower())
            with open(summary_path, 'r') as summary : 
                data = json.load(summary)
                for item in data['list'] :
                    if len(item['title'].split('|')) > 1 : id = item['title'].split('|')[1]
                    else : id = item['title']
                    ids.append(id)


        
        with open(self.ids_path, 'w') as file : 
            for id in ids : file.write(f'{id}\n')


    def counts_ids_txt(self) : 
        with open(self.ids_path, 'r') as ids : 

            count = {
                keyword.lower() : 0 for keyword in self.keywords
            }
            mode = None
            
            while True : 
                line = ids.readline().strip()
                if not line : break
                if line.startswith('#') :
                    mode = str(line.strip()[1:]).lower()
                elif line and not line.startswith('#') : 
                    if mode in count : count[mode] += 1
                    else : display.error('Error : current mode not matching dictionnary. Go debug in interpro_analysis.py / InterproAnalyzer / counts_ids_txt . Moving on.')
            
        for item in count : 
            display.info(f'{item} : {count[item]}')
