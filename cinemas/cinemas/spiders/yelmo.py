import scrapy
from scrapy_playwright.page import PageMethod
from collections import defaultdict


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
            yield response.follow(
                url,
                callback=self.parse_movie,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', '#ddlDate')
                    ],
                }
            )

    def parse_movie(self, response):
        # title, length, age, showings{day: [hours]},
        # actors, directors, genres, synopsis, url

        days = response.css("#ddlDate option::attr(value)").getall()
        print(days)
        details = {}
        synopsis = ''

        for day in days:
            yield scrapy.Request(
                response.url,
                callback=self.parse_day,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('select_option', '#ddlDate', day),
                        PageMethod('wait_for_timeout', 500),
                    ],
                    'day': day
                }
            )

        if response.css('div.info > h4::text') == 'Sinopsis':
            synopsis = response.css('div.info > p::text').get()

        # with open('test.txt', 'w') as f:
        #     for t1 in response.css('div.info > h4::text').get():
        #         f.write('\n T1 \n ' + t1 + '\n')
        #     for t2 in response.css('div.info').getall():
        #         f.write('\n T2 \n ' + t2 + '\n')
        #     for t3 in response.css('div.info > p > span + small').getall():
        #         f.write('\n T3 \n ' + t3 + '\n')
        #     for t4 in response.css('div.info > p'):
        #         f.write('\n T4 \n ' + t4 + '\n').getall()

        for info in response.css('div.info > p > span + small'):
            details[info.css('span::text').get()] = info.css('small::text').get().split(', ')
        print(details)

        yield {
            'title': response.css('div.infoPelicula > h3').get(),
            'length': response.css('span.duracion::text').get(),
            'age': response.css('span.clasificacion::text').get(),
            'details': details,
            'synopsis': synopsis,
            'url': response.url,
        }

    def parse_day(self, response):
        day = response.meta["day"]
        showings = defaultdict(lambda: defaultdict(dict))

        for div in response.css('div.horariosDesc > div'):
            showings[
                div.css('::attr(data-cinema)').get()
            ][
                div.css('label::text').get()
            ][
                day
            ] = div.css('time > a::text').getall()

        yield {
            'url_specific': response.url,
            'showings': showings
        }

# if 'la-villa-de-orotava' in location:
#     if '2D ESPAÑOL' in label:
#         showings_villa[day: shows]
#     elif '2D INGLÉS SUBTITULADO EN ESPAÑOL (VOSE)':
#         showings_vose_villa[day: shows]
#     elif '3D ESPAÑOL' in label:
#         showings_3d_villa[day: shows]
#     elif '3D INGLÉS SUBTITULADO EN ESPAÑOL (VOSE)':
#         showings_vose_3d_villa[day: shows]
# elif 'meridiano' in location:
#     if '2D ESPAÑOL' in label:
#         showings_meridiano[day: shows]
#     elif '2D INGLÉS SUBTITULADO EN ESPAÑOL (VOSE)':
#         showings_vose_meridiano[day: shows]
#     elif '3D ESPAÑOL' in label:
#         showings_3d_meridiano[day: shows]
#     elif '3D INGLÉS SUBTITULADO EN ESPAÑOL (VOSE)':
#         showings_vose_3d_meridiano[day: shows]
