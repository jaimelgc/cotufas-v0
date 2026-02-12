import pandas as pd

INPUT_MULTICINES = 'data_raw/multicines_raw.json'
INPUT_XSUR = 'data_raw/xsur_raw.json'
INPUT_YELMO = 'data_raw/yelmo_raw.json'
INPUT_ZENTRALCENTER = 'data_raw/zentralcenter_raw.json'
OUTPUT_ZENTRALCENTER = 'data/zentralcenter.json'
OUTPUT_YELMO = 'data/yelmo.json'


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

        df_output.to_json(output1)


def normalize_zentralcenter(output1: str):
    '''Join json files and add theater attribute'''
    # {"date": "17/02/2026", "day_name": "Martes", "movies":
    # [{"title": "CUMBRES BORRASCOSAS", "duration": "130 min.",
    # "language": "SIN SUBTITULOS", "age_rating": "Desconocida",
    # "theater": "zentralcenter", "showings": {"SALA 2": ["16:15", "19:00", "21:45"]}}
    df = pd.read_json(INPUT_ZENTRALCENTER)

    # days = df['day_name'].unique() <- if row specified it goes down, if not iters columns,
    # for itering rows .iterrows

    data = {}
    titles = []
    for movies in df['movies']:
        titles += [f"{movie['title']} - {movie['language']}" for movie in movies]
    unique_titles = set(titles)

    for title in unique_titles:
        showings = {}
        length = ''
        age = ''
        for index, row in df.iterrows():
            date = row.loc['date']
            movies = row.loc['movies']
            for movie in movies:
                if f"{movie['title']} - {movie['language']}" == title:
                    if not showings:
                        length = movie['duration']
                        age = movie['age_rating']
                    showings[str(date)] = movie['showings']

        data[title] = {
            'length': length,
            'age': age,
            'showings': showings,
            'theater': 'zentralcenter',
        }

    df_output = pd.DataFrame()

    for key, value in data.items():  # only data iterates over the keys
        df_output[key] = [value]

    df_output.to_json(output1)


normalize_yelmo(OUTPUT_YELMO)
normalize_zentralcenter(OUTPUT_ZENTRALCENTER)
