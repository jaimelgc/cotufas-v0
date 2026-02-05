import scrapy
from scrapy_playwright.page import PageMethod


class YelmoSpider(scrapy.Spider):
    name = 'yelmo'
    start_urls = ['https://www.yelmocines.es/cartelera/santa-cruz-tenerife/']

    def start_requests(self):
        yield scrapy.Request(
            self.start_urls[0],
            meta={
                'playwright': True,
                'playwright_page_methods': [
                    PageMethod('wait_for_selector', 'article.tituloPelicula')
                ],
            },
        )

    def parse(self, response):
        urls = response.css('article.tituloPelicula > figure > a::attr(href)').getall()
        for url in urls:
            yield response.follow(url, callback=self.parse_movie)

    def parse_movie(self, response):
        # title, length, age, showings{day: [hours]},
        # actors, directors, genres, synopsis, url

        showings_villa = {}
        showings_meridiano = {}

        showings_raw_villa = response.css('')
        showings_raw_meridiano = response.css('')

        yield {
            'title': response.css('div.infoPelicula > h3').get(),
            'length': response.css('span.duracion::text').get(),
            'age': response.css('span.clasificacion::text').get(),

        }
