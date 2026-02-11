import subprocess

theaters = ['multicines', 'yelmo', 'xsur', 'zentralcenter']

for theater in theaters:
    subprocess.run(['scrapy', 'crawl', theater, '-O', f'./raw_data/{theater}.json'])
