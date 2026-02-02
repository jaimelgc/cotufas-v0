import scrapy


class MulticinesSpider(scrapy.Spider):
    name = 'yelmo'
    start_urls = ['https://multicinestenerife.com/cartelera-tenerife/']

    