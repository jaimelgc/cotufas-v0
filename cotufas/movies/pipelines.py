import json

import pandas as pd

cinemas = ['yelmo', 'multicines', 'zentralcenter', 'xsur']

INPUT_MULTICINES = 'data_raw/multicines.json'
INPUT_XSUR = 'data_raw/xsur.json'
INPUT_YELMO = 'data_raw/yelmo.json'
INPUT_ZENTRALCENTER = 'data_raw/zentralcenter.json'
OUTPUT_PATH = 'data/data_join.json'


def normalize_columns(input1: str, input2: str, input3: str, input4: str, output1: str):
    '''Join json files and add theater attribute'''
    df1 = pd.read_json(input1)
    df2 = pd.read_json(input2)
    df3 = pd.read_json(input3)
    df4 = pd.read_json(input4)


def join_files(input1: str, input2: str, input3: str, input4: str, output1: str):
    '''Join json files and add theater attribute'''
    df1 = pd.read_json(input1)
    df2 = pd.read_json(input2)
    df3 = pd.read_json(input3)
    df4 = pd.read_json(input4)

    titles = []
    for df in df1, df2:
        titles.extend(df['title'].tolist())


def normalize_data(path1: str, path2: str):
    '''Función que normaliza y selecciona los datos
    a utilizar entre todos los cines y sesiones'''
    pass

    # df_input = pd.read_json


normalize_columns(INPUT_MULTICINES, INPUT_XSUR, INPUT_YELMO, INPUT_ZENTRALCENTER, OUTPUT_PATH)
normalize_columns(INPUT_MULTICINES, INPUT_XSUR, INPUT_YELMO, INPUT_ZENTRALCENTER, OUTPUT_PATH)
