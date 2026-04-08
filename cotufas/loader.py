import os
import subprocess

theaters = ['multicines', 'xsur', 'zentralcenter', 'yelmo']
data_pipeline = [
    ['python', 'normalizer.py'],
    ['python', 'merger.py'],
]
load_pipeline = [
    ['python', 'manage.py', 'load_cinema_data', 'movies/data/merged.json', '--clear'],
    ['python', 'manage.py', 'clean_cinema_data'],
]
tests = []

os.chdir('movies/cinemas/')

for theater in theaters:
    print(f'Scraping {theater}')
    try:
        subprocess.run(
            ['scrapy', 'crawl', theater, '-O', f'../data_raw/{theater}_raw.json'], check=True
        )
    except subprocess.CalledProcessError:
        print(f'Command failed: {theater}')
        break

os.chdir('..')

for cmd in data_pipeline:
    print('Running:', cmd)
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print(f'Command failed: {cmd}')
        break

os.chdir('..')

for cmd in load_pipeline:
    print('Running:', cmd)
    try:
        subprocess.run(
            ['python', 'manage.py', 'load_cinema_data', 'movies/data/merged.json', '--clear'],
            check=True,
        )
    except subprocess.CalledProcessError:
        print(f'Command failed: {cmd}')
        break
