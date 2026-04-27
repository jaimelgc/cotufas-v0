from collections import defaultdict

import scrapy
from scrapy_playwright.page import PageMethod


class YelmoSpider(scrapy.Spider):
    name = 'yelmo'
    start_urls = ['https://www.yelmocines.es/cartelera/santa-cruz-tenerife/']

    # Limit concurrent requests to avoid overwhelming the server
    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 1,
    }

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
                        PageMethod('wait_for_load_state', 'networkidle'),
                    ],
                    'playwright_include_page': True,
                },
            )

    async def parse_movie(self, response):
        page = response.meta['playwright_page']

        try:
            # Get movie details
            details = {}
            synopsis = ''
            if 'Sinopsis' in response.css('div.info > h4::text').getall():
                synopsis = response.css('div.info > p::text').get()
            for info in response.css('div.info > p.bolder.cf'):
                key = info.css('span::text').get()
                value = info.css('small::text').get()
                if key and value:
                    details[key] = value.split(', ')

            movie_detail = {
                'title': response.css('div.infoPelicula > h3::text').get(),
                'length': response.css('span.duracion::text').get(),
                'age': response.css('span.clasificacion::text').get(),
                'genres': response.css('span.genero::text').get(),
                'details': details,
                'synopsis': synopsis,
                'url': response.url,
                'cover_url': response.css('div.imgPelicula > figure > img::attr(src)').get(),
            }

            # Wait a bit for the page to fully settle
            await page.wait_for_timeout(1000)

            # Get days using JavaScript with retry logic
            days = []
            for attempt in range(3):  # Try 3 times
                try:
                    days = await page.evaluate(
                        '''() => {
                        const select = document.querySelector('#ddlDate');
                        if (!select) return [];
                        return Array.from(select.options)
                            .map(opt => opt.value)
                            .filter(v => v && v.trim() !== '');
                    }'''
                    )
                    if days:
                        break
                    await page.wait_for_timeout(1000)
                except Exception as e:
                    self.logger.warning(f"Attempt {attempt + 1} failed to get days: {e}")
                    if attempt < 2:
                        await page.wait_for_timeout(1000)

            self.logger.info(f"Found {len(days)} days for {movie_detail['title']}")

            # Collect showings for all days
            all_showings = defaultdict(lambda: defaultdict(dict))

            for day in days:
                self.logger.info(f"Processing day: {day}")

                try:
                    # Select the day option
                    await page.select_option('#ddlDate', day)
                    await page.wait_for_timeout(2500)  # Increased wait time

                    # Get updated content
                    content = await page.content()
                    updated_response = scrapy.http.HtmlResponse(
                        url=response.url, body=content, encoding='utf-8'
                    )

                    # Parse showings for this day
                    showings_count = 0
                    for div in updated_response.css('div.horariosDesc > div'):
                        cinema = div.css('::attr(data-cinema)').get()
                        format_type = div.css('label::text').get()
                        times = div.css('time > a::text').getall()
                        if cinema and format_type and times:
                            all_showings[cinema][format_type][day] = times
                            showings_count += 1

                    self.logger.info(f"Found {showings_count} showings for day {day}")
                except Exception as e:
                    self.logger.error(f"Error processing day {day}: {e}")

            # Yield everything together
            yield {
                'detail': movie_detail,
                'theater': 'yelmo',
                'showings': {k: dict(v) for k, v in all_showings.items()},
            }

        except Exception as e:
            self.logger.error(f"Error processing movie {response.url}: {e}")
        finally:
            await page.close()
