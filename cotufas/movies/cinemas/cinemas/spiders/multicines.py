import scrapy


class MulticinesSpider(scrapy.Spider):
    name = 'multicines'
    start_urls = ['https://multicinestenerife.com/cartelera-tenerife/']

    def parse(self, response):
        for movie_url in response.css(
            'div.amy-movie-item-inner div.amy-movie-item-poster > a::attr(href)'
        ).getall():

            if movie_url:
                yield response.follow(movie_url, callback=self.parse_movie)

    def parse_movie(self, response):
        actors = []
        directors = []
        genres = []
        showings = {}

        title_raw = response.css('a.u-url.url::text').get()

        cover_url = response.css('div.entry-poster > img::attr(src)').get()

        synopsis = (
            response.css('div.entry-content.e-content > p > span::text').get()
            or response.css('div.entry-content.e-content > p::text').get()
            or response.css('div.entry-content.e-content > div.row > span::text').get()
        )

        movie_length_raw = response.css('span.duration::text').getall()
        try:
            movie_length = movie_length_raw[1].strip()
        except IndexError:
            movie_length = ''

        for line in response.css('ul.info-list > li'):
            label = line.css('label::text').get().strip().lower()
            names = line.css('span > a::text').getall()

            if 'actor' in label:
                actors.extend(names)
            elif 'director' in label:
                directors.extend(names)
            elif 'género' in label:
                genres.extend(names)

        showings_raw = response.css(
            'div.showtime-item.single-cinema.__web-inspector-hide-shortcut__ > div.st-item'
        ) or response.css('div.showtime-item.single-cinema > div.st-item')

        for showing in showings_raw:
            if showing.css('div.st-title > label::text').get():
                showings[showing.css('div.st-title > label::text').get()] = showing.css(
                    'ul > li::text'
                ).getall()

        yield {
            'title': title_raw.strip(),
            'length': movie_length,
            'age': response.css('span.pg::text').get(),
            'theater': 'multicines',
            'showings': showings,
            'actors': actors,
            'directors': directors,
            'genres': genres,
            'synopsis': synopsis,
            'url': response.url,
            'cover_url': cover_url,
        }
