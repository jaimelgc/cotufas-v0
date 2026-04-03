import os
import subprocess

# commands = [
#     ['cd', 'movies/cinemas/'],
#     ['scrapy', 'crawl', 'multicines', '-O', '../data_raw/multicines_raw.json'],
#     ['scrapy', 'crawl', 'xsur', '-O', '../data_raw/xsur_raw.json'],
#     ['scrapy', 'crawl', 'zentralcenter', '-O', '../data_raw/zentralcenter_raw.json'],
#     ['scrapy', 'crawl', 'yelmo', '-O', '../data_raw/yelmo_raw.json'],
#     ['cd', '../'],
#     ['python', 'normalizer.py'],
#     ['python', 'merger.py'],
#     ['python', 'manage.py', 'load_cinema_data', 'movies/data/merged.json', '--clear'],
# ]

theaters = ['multicines', 'xsur', 'zentralcenter', 'yelmo']
data_pipeline = [
    ['python', 'normalizer.py'],
    ['python', 'merger.py'],
]
loader = (['python', 'manage.py', 'load_cinema_data', 'movies/data/merged.json', '--clear'],)

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

try:
    subprocess.run(
        ['python', 'manage.py', 'load_cinema_data', 'movies/data/merged.json', '--clear'],
        check=True,
    )
except subprocess.CalledProcessError:
    print(f'Command failed: {cmd}')
