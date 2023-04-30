from os import read
from pandas.core.arrays.sparse import dtype
import requests
import pandas as pd
import numpy as np
import traceback
import time
import sys
from config_columns import columns_type
from system_status import SystemStatus

class Searcher:
    def __init__(self) -> None:
        self.Headers = {'Host': 'websbor.gks.ru'}
        self.Url = 'https://websbor.gks.ru/webstat/api/gs/organizations/'
    
    def get_corp_okud(self,corp_id):
        url = str(self.Url+corp_id+'/forms')
        api = requests.get(url,verify=False)        
        return api.json()

    def get_corp_id_and_name(self,inn):        
        body = {"okpo":"","inn":inn,"ogrn":""}    
        api = requests.post(self.Url,headers=self.Headers,json=body,verify=False)
        corp_id = ''
        corp_name = ''
        if api.status_code == 200:            
            corp_id = api.json()[0]['id']
            corp_name = api.json()[0]['name']            
            return corp_id, corp_name
        else:
            raise Exception(f'Status code: {api.status_code} text - {api.text}')
        
    
        

    def get_data_by_inn(self, inn):
        
        if pd.isna(inn):
            raise Exception('Пустая ячейка')
        
        if not isinstance(inn,str):
            raise Exception(f'Значение ячейки {inn} не является числом')
        
        corp_id = ''
        corp_name = ''
        max_retry = 3
        retry = 0
        exception_text =''
        while True:
            try:
                corp_id, corp_name = self.get_corp_id_and_name(str(inn))
            except Exception as e: 
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print(f'{retry=}, {exc_value=}')
                exception_text = str(exc_value)
                retry +=1
                if retry > max_retry:
                    print('break try')
                    break
                continue
            break

        if corp_id == '':
            raise Exception(exception_text)
        
        print('Request info about ' + corp_name + '    INN = ' + inn)

        corp_okud = self.get_corp_okud(corp_id)        

        return corp_id, corp_name, corp_okud


    def result_dict(self,inn, corp_id,corp_name,new_data):        
        res = []
        for line in new_data:
            d = {}            
            d['inn'] = inn
            d['corp_id'] = corp_id
            d['company'] = corp_name
            for c_name,_,_,_ in filter(lambda x:x[3],columns_type):
                value = line[c_name]
                d[c_name] = value
            d['status'] = SystemStatus.SUCCESS
            d['info'] = ''
            res.append(d)
        return res
        


    def start_search(self, df:pd.DataFrame,call_back = None) -> pd.DataFrame:
        
        df_result = pd.DataFrame(data=[],columns=[x[0] for x in columns_type])

        for inn in df['inn'].unique():
            try:
                corp_id, corp_name, corp_data = self.get_data_by_inn(inn)
                d = self.result_dict(inn, corp_id, corp_name, corp_data)
                df_result = df_result.append(d,ignore_index=True)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                text =  str(exc_value)
                new_row = {'inn':inn,
                           'status': SystemStatus.ERROR,
                           'info':text
                           }
                
                df_result = df_result.append(new_row, ignore_index=True)

            if call_back is not None:
                call_back()
        return df_result


if __name__ == "__main__":
    s = Searcher()
    df_res = s.start_search(pd.DataFrame(data=[['9731036697','','','','','','','','']],
                        columns=['inn'
                                ,'company'
                                ,'index'
                                ,'name'
                                ,'okud'
                                ,'form_period'
                                ,'end_time'
                                ,'reported_period'
                                ,'comment']
                                )
                   )
    print(df_res)