import streamlit as st
import pandas as pd
import numpy as np
from seacher import Searcher
from io import StringIO
import os
from system_status import SystemStatus
from config_columns import columns_type
from streamlit.delta_generator import DeltaGenerator

global_path = 'data.csv' #путь и название выходного файла
my_searcher = Searcher()

#выбираем колонки для отображения в интерфейсе
column_for_view =[s[0] for s in list(filter(lambda x: x[2], columns_type))]

st.set_page_config(layout="wide") # делает страницу в интерфейсе широкого формата

@st.cache_data(show_spinner=True)
def get_df_from_file(path):
    '''метод чтения файла, или если файл не существует создает пустую таблицу'''    
    df = None
    if os.path.exists(path):
        df=pd.read_csv(path,dtype={x[0]:x[1] for x in columns_type},sep='\t')
    else:
        df = pd.DataFrame(data=[],columns=[x[0] for x in columns_type])
    return df

df = get_df_from_file(global_path)

def upload_file():
    global df
    #форма для загрузки файла с ИНН
    with st.form("my-form", clear_on_submit=True):
        uploaded_file = st.file_uploader("upload file",key='file_uploader')
        print(f'{uploaded_file=}')
        if uploaded_file is not None:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            string_data = stringio.readlines()
            print(f'{string_data=}')
            for inn_line in string_data:
                inn = inn_line.replace('\r','').replace('\n','')
                
                if inn == '': continue

                if not (df['inn'] == inn).any():
                    new_row = {'inn':inn,
                            'status': SystemStatus.NEW}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    print(f'{df.shape=}')
        submitted = st.form_submit_button("Add to Table")  

# if st.button('inn'):
upload_file()
    

def save_table(df):
    df.to_csv(global_path, index=False, sep='\t')

df_part = df
def view_filters():
    global df_part
    #отрисовка двух фильтров
    col_filter1, col_filter2, col_filter3 = st.columns(3)

    with col_filter1:
        filter_text = st.text_input('filter:')
    count_row = 0
    if filter_text != '':
        try:
            df_part = df.query(filter_text)        
        except:
            pass

    options = []
    with col_filter2:
        indexies = list(df['index'].unique())
        options = st.multiselect('Index',indexies)
        if len(options)>0:
            df_part = df_part[df_part['index'].isin(options)]

    filter_status = []
    with col_filter3:    
        filter_status = st.multiselect('Status',SystemStatus.get_values())
        if len(filter_status)>0:
            df_part = df_part[df_part['status'].isin(filter_status)]

def view_table():
    #отрисовка таблицы
    st.dataframe(df_part[column_for_view],use_container_width=True)
    count_row = len(df_part)

progress_count = 0
progress_step = 0
progress_text = "Operation in progress. Please wait."
my_bar = None

def callback_progress():
    '''метод, который срабатывает каждый раз после обработки одного инн, для обновления прогресса'''
    global progress_count,progress_step,my_bar
    progress_count += progress_step
    if progress_count > 1.0:
        progress_count = 1.0
    my_bar.progress(progress_count)

def start_search():
    '''начало поиска по инн'''
    global progress_count,progress_step,my_bar,df,filter_text,uploaded_file
    my_bar = st.progress(0, text=progress_text)
    progress_count = 0
    progress_max = 0
    uploaded_file = None

    #получаем данные для обновления
    df_part = df[df['status'] == SystemStatus.UPDATE]
    
    #подсчет уникального количества ИНН, по которым будет происходить поиск
    progress_max = len(df_part['inn'].unique())
    
    progress_step = 1.0 / progress_max
    
    #поиск по данным
    df_result = my_searcher.start_search(df_part, callback_progress)
    #print(f'{df_result.shape=}')

    #по результату должны по каждому ИНН, который был отправлен в поиск, сделать обновление в исходной таблице
    for inn in df_part['inn'].unique():        

        df_result_inn = df_result[df_result['inn'] == inn]

        if (df_result_inn['status'] != SystemStatus.ERROR).any():
            # если обновление получено со статусом успешно, тогда удаляем строчки из исходной таблицы, чтобы потом вставить заново
            df.drop(index=df[df['inn'] == inn].index, inplace=True)
        else:
            # если обновление получено со статусом ошибки, тогда в исходной таблице помечаем статус с ошибкой и пишем информацию почему.
            one_line = df_result_inn[df_result_inn['status'] == SystemStatus.ERROR]
            df.loc[df['inn'] == inn,'status'] = SystemStatus.ERROR
            df.loc[df['inn'] == inn,'info'] = one_line['info'].values[0]
            

    # в исходную таблицу из результата добавляем всё что было со статусом успешно
    df = pd.concat([df, df_result[df_result['status'] != SystemStatus.ERROR]])
    save_table(df)
    
    if 'file_uploader' in  st.session_state:
        del st.session_state['file_uploader']
    my_bar.empty()
    st.cache_data.clear()


def to_update_search():
    '''метод для проставления статуса update для выбранных строк по фильтрам или для только что загруженных инн из файла'''
    global df, df_part
    df.loc[df[df['status'] == SystemStatus.NEW].index,'status'] = SystemStatus.UPDATE

    df.loc[df_part.index,'status'] = SystemStatus.UPDATE

    save_table(df)
    st.cache_data.clear()

def delete_by_filter():
    df.drop(index = df_part.index,inplace=True)    
    save_table(df)
    st.cache_data.clear()

def confirm_delete_by_filter():    
    st.button(f"Confirm Delete {len(df_part)} rows",on_click=delete_by_filter)    


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('1251')

def view_toolbar():
    global df_part, df
    #отрисовка кнопок после таблицы
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.button('To Update',on_click=to_update_search)

    with col2:
        st.button('Start Search',on_click=start_search)

    with col3:
        res = st.button('Delete')
        if res:
            confirm_delete_by_filter()

    with col4:
        st.download_button(label='Download csv', data= convert_df(df_part),file_name='data.csv',mime='text/csv')

    #with col5:
        
    with col6:
        st.write(f'count row - {len(df_part)}')


     
    
           
        
# if st.button('Load from inn'):
#     load_from_inn()
            
view_toolbar()

view_filters()

view_table()
