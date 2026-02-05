import scrapy


class YelmoSpider(scrapy.Spider):
    name = 'yelmo'
    start_urls = ['https://www.yelmocines.es/cartelera/santa-cruz-tenerife/']

    def parse(self, response):
        movies = response.css('article.cf.tituloPelicula-now__movie').getall()
        print(movies)
        yield movies
