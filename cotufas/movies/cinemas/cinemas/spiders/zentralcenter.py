import scrapy


class ZentralcenterSpider(scrapy.Spider):
    name = 'zentralcenter'
    # Start without session - let the server create one
    start_urls = ['https://kinetike.com:83/views/init.aspx?cine=ZENTRALCENTER']

    custom_settings = {
        'COOKIES_ENABLED': True,  # CRITICAL
        'CONCURRENT_REQUESTS': 1,  # Keep it slow to maintain session
    }

    def parse(self, response):
        """Parse the first day"""
        # Extract current date and movies
        current_date = response.css('#lblContFecha font::text, #lblContFecha::text').get()
        day_name = response.css('#lblDiaFecha font::text, #lblDiaFecha::text').get()

        self.logger.info(f"Scraping {day_name} {current_date}")

        movies = self.extract_movies(response)

        yield {'date': current_date, 'day_name': day_name, 'movies': movies}

        # Click "next" to get more days
        yield self.click_next(response, day_count=1, max_days=7)

    def parse_next_day(self, response):
        """Parse subsequent days"""
        day_count = response.meta['day_count']
        max_days = response.meta['max_days']

        # Extract current date and movies
        current_date = response.css('#lblContFecha font::text, #lblContFecha::text').get()
        day_name = response.css('#lblDiaFecha font::text, #lblDiaFecha::text').get()

        self.logger.info(f"Scraping day {day_count}: {day_name} {current_date}")

        movies = self.extract_movies(response)

        yield {'date': current_date, 'day_name': day_name, 'movies': movies}

        # Continue to next day if not at limit
        if day_count < max_days:
            yield self.click_next(response, day_count + 1, max_days)

    def click_next(self, response, day_count, max_days):
        """Create a POST request to click the 'next' button"""
        formdata = {
            '__EVENTTARGET': 'imgSiguiente',  # The next button
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': response.css('input[name="__VIEWSTATE"]::attr(value)').get() or '',
            '__VIEWSTATEGENERATOR': response.css(
                'input[name="__VIEWSTATEGENERATOR"]::attr(value)'
            ).get()
            or '',
            '__EVENTVALIDATION': response.css('input[name="__EVENTVALIDATION"]::attr(value)').get()
            or '',
            '__PREVIOUSPAGE': response.css('input[name="__PREVIOUSPAGE"]::attr(value)').get() or '',
            'theScriptManager_HiddenField': response.css(
                'input[name="theScriptManager_HiddenField"]::attr(value)'
            ).get()
            or '',
            'clientScreenHeight': '1080',
            'clientScreenWidth': '1920',
        }

        return scrapy.FormRequest(
            url=response.url,  # Use the current URL (it has the session)
            formdata=formdata,
            callback=self.parse_next_day,
            meta={
                'day_count': day_count,
                'max_days': max_days,
            },
        )

    def extract_movies(self, response):
        """Extract movie data from the page"""
        movies = []

        for movie_div in response.css('div.panel_peli'):
            # Get title
            title = movie_div.css('span.info_negrita::text').get()
            if not title:
                continue

            title = title.strip()

            # Get duration and language
            duration = movie_div.css('div.infoPeliSesion span::text').get()
            language = movie_div.css('div.infoPeliSesion span:nth-of-type(2)::text').get()

            # Get age rating from image
            age_img = movie_div.css('div.infoPeliSesionRight img::attr(src)').get()
            age_rating = None
            if age_img:
                # Extract rating from filename like "Clasificacion16.png"
                if 'Clasificacion7' in age_img:
                    age_rating = '7'
                elif 'Clasificacion12' in age_img:
                    age_rating = '12'
                elif 'Clasificacion16' in age_img:
                    age_rating = '16'
                elif 'Clasificacion18' in age_img:
                    age_rating = '18'
                elif 'ClasificacionDesc' in age_img:
                    age_rating = 'Desconocida'

            # Extract showings by sala (room)
            showings = {}

            # Get the showing info div
            showing_divs = movie_div.css('div.infoPeliSesion')
            for showing_div in showing_divs:
                # Get all text and links
                parts = showing_div.css('*::text').getall()

                current_sala = None
                times = []

                for part in parts:
                    part = part.strip()
                    if 'SALA' in part:
                        # Save previous sala if exists
                        if current_sala and times:
                            showings[current_sala] = times
                            times = []
                        current_sala = part
                    elif ':' in part and len(part) <= 6:  # Time format like "16:30"
                        times.append(part)

                # Don't forget the last sala
                if current_sala and times:
                    showings[current_sala] = times

            movie_data = {
                'title': title,
                'duration': duration.strip() if duration else None,
                'language': language.strip() if language else None,
                'age_rating': age_rating,
                'theater': 'zentralcenter',
                'showings': showings,
            }

            movies.append(movie_data)

        return movies
