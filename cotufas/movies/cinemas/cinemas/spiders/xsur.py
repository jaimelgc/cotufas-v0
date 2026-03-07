import scrapy


class XsurSpider(scrapy.Spider):
    name = 'xsur'
    start_urls = ['https://x-surcine.com/']

    def parse(self, response):
        for movie_url in response.css('h4.mfn-woo-product-title > a::attr(href)').getall():

            if movie_url:
                yield response.follow(
                    movie_url,
                    callback=self.parse_movie
                )

    def parse_movie(self, response):
        data = [d.strip() for d in response.css('div.the_content_wrapper > h4::text').getall()]

        yield {
            'title': response.css('h3.page-title::text').get(),
            'synopsis': response.css('div.the_content_wrapper > p::text').getall()[0].strip(),
            'length': data[0].split(': ')[1],
            'age': data[1].split(':  ')[1],
            'theater': 'xsur',
            'showings': data[3:],
            'url': response.url,
        }
