import json

import pandas as pd

cinemas = ['yelmo', 'multicines', 'zentralcenter', 'xsur']

INPUT_MULTICINES = 'data_raw/multicines.json'
INPUT_XSUR = 'data_raw/xsur.json'
INPUT_YELMO = 'data_raw/yelmo.json'
INPUT_ZENTRALCENTER = 'data_raw/zentralcenter.json'
OUTPUT_PATH = 'data/data_join.csv'


def normalize_yelmo(output1: str):
    '''Join json files and add theater attribute'''
    df = pd.read_json(INPUT_YELMO)

    data = {}
    i = 0
    for detail in df['detail']:
        data[i] = {
            'title': df['detail'][i]['title'],
            'length': df['detail'][i]['length'],
            'age': df['detail'][i]['age'],
            'genres': df['detail'][i]['genres'],
            'actors': df['detail'][i]['details'].get('Actores:', None),
            'directors': df['detail'][i]['details'].get('Directores:', None),
            'producers': df['detail'][i]['details'].get('Productores:', None),
            'synopsis': df['detail'][i]['synopsis'],
            'url': df['detail'][i]['url'][i],
            'theater': df['theater'][i],
            'showings': df['showings'][i],
        }
        i += 1

        df_output = pd.DataFrame()
        for column in data.values():
            for key in column.keys():
                df_output[key] = [value[key] for value in data.values()]

        df_output.to_csv(output1)


def normalize_zentralcenter(output1: str):
    '''Join json files and add theater attribute'''
    df = pd.read_json(INPUT_ZENTRALCENTER)

    data = {}


def join_files(input1: str, input2: str, input3: str, input4: str, output1: str):
    '''Join json files and add theater attribute'''
    df1 = pd.read_json(input1)
    df2 = pd.read_json(input2)
    df3 = pd.read_json(input3)
    df4 = pd.read_json(input4)

    for df in df1, df2:
        pass

    df_out = pd.concat([df1, df2], ignore_index=True)
    df_out.to_csv(output1)


# def normalize_data(path1: str, path2: str):
#     '''Función que normaliza y selecciona los datos
#     a utilizar entre todos los cines y sesiones'''
#     pass

# df_input = pd.read_json

# normalize_columns(INPUT_YELMO, INPUT_ZENTRALCENTER, OUTPUT_PATH)
# join_files(INPUT_MULTICINES, INPUT_XSUR, INPUT_YELMO, INPUT_ZENTRALCENTER, OUTPUT_PATH)
# normalize_yelmo(OUTPUT_PATH)
normalize_zentralcenter(OUTPUT_PATH)
