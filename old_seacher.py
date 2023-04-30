from os import read
from pandas.core.arrays.sparse import dtype
import requests
import pandas as pd
import numpy as np
 
Headers = {'Host': 'websbor.gks.ru'}
Url = 'https://websbor.gks.ru/webstat/api/gs/organizations/'
Corp_name = ''
Corp_inn = ''
File = 'c:/temp/ur.xlsx'
 
 
def get_corp_id(inn,url=Url):
    global Corp_name
    body = {"okpo":"","inn":inn,"ogrn":""}    
    api = requests.post(url,headers=Headers,json=body)
    if api.status_code == 200:
        try:
            corp_id = api.json()[0]['id']
            Corp_name = api.json()[0]['name']
        except:
            corp_id = 'Status'        
        return corp_id
    else:
        return str('Status code: %d' % api.status_code)
 
def get_corp_okud(corp_id,url=Url):
    url = str(url+corp_id+'/forms')
    print('Request info about ' + Corp_name + '    INN = ' + Corp_inn)
    api = requests.get(url)
    return api.json()
 
def ret_corp_format(corp_okud):
    corp = {}
    corp['ИНН'] = Corp_inn
    corp['Организация'] = Corp_name    
    if corp_okud == 'None':        
        corp['Индекс формы'] = ''
        corp['Наименование формы'] = ''
        corp['ОКУД'] = ''
        corp['Периодичность формы'] = ''
        corp['Срок сдачи формы'] = ''
        corp['Отчетный период'] = ''
        corp['Комментарий'] = ''        
    else:
        corp['Индекс формы'] = corp_okud['index']
        corp['Наименование формы'] = corp_okud['name']
        corp['ОКУД'] = corp_okud['okud']
        corp['Периодичность формы'] = corp_okud['form_period']
        corp['Срок сдачи формы'] = corp_okud['end_time']
        corp['Отчетный период'] = corp_okud['reported_period']
        corp['Комментарий'] = corp_okud['comment']
    return corp
 
def main():
    global Corp_inn
    num_full = 0
    num_empty = 0
    corp_summary = []
    inns = pd.read_excel(File,usecols='C',skiprows=0,dtype=str)
    inns = inns.values.tolist()
    n=np.array(inns)
    inns = n.view().reshape(-1)
    #for o in inns:
    #    print(o)
    #return
    for inn in inns:
        if not pd.isna(inn):
            #inn = ''.join(inn)
            #try:
            #    inn=int(inn)
            #except:
            #    print("Неверное значение",inn)
            corp_id = 'Status'
            if type(inn)==np.str_:
                while corp_id.startswith('Status'):
                    try:
                        corp_id = get_corp_id(str(inn))
                    except:
                        continue
                    break
                #corp_id = get_corp_id(inn)
                Corp_inn = inn
                if not corp_id.startswith("Status"):
                    corp_okud = get_corp_okud(corp_id)
                    if len(corp_okud) > 0:
                        num_full += 1
                        for okud in corp_okud:
                            corp = ret_corp_format(okud)
                            corp_summary.append(corp)
                            print('Получены данные форм по клиенту ', corp_id)
                    else:
                            corp = ret_corp_format('None')
                            corp_summary.append(corp)
                            num_empty += 1
                else:
                    print('Ошибка подключения - ' ,corp_id , Corp_inn)
                    #corp_summary.append('ошибка в ИНН' +Corp_inn)
                    #print(corp_summary)
                    #return
            else:
                print('Значение ячейки %s не является числом' % inn)
        else:
            print('Пустая ячейка')
    #print(corp_summary)
    print('Получено данных по %d компаниям' % (num_full+num_empty))
    print('Компаний с отчетами: %d' % num_full)
    df = pd.DataFrame(data=corp_summary)
    df.to_excel('c:/temp/book.xlsx')
 
if __name__ == "__main__":
    main()
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
#def main():
#    global Corp_inn
#    corp_summary = []
#    with open("C:/temp/rosstat.csv","r",encoding='utf-8',newline='') as csv_file:
#        reader = csv.DictReader(csv_file)
#        with open("c:/temp/text.csv","w",encoding='utf-8',newline='') as csv_filew:
#            writer = csv.writer(csv_filew)
#            for i in reader:
#                Corp_inn = i['INN']
#                corp_id = get_corp_id(Url,Corp_inn)
#                if type(corp_id) == tuple:
#                    corp_okud = get_corp_okud(Url,corp_id)
#                    print(corp_okud)
#                    if len(corp_okud) > 0:
#                        for okud in corp_okud:
#                            corp = ret_corp_format(okud)
#                            corp_summary.append(corp)
#                    else:
#                        corp = ret_corp_format('None')
#                        corp_summary.append(corp)
#                else:
#                    print('Ошибка подключения - %s' % corp_id)
#    df = pd.DataFrame(data=corp_summary)
#    df.to_excel('c:/temp/book.xlsx')