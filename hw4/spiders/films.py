import scrapy
import re 


class FilmsSpider(scrapy.Spider):
    name = "films"
    allowed_domains = ["ru.wikipedia.org", "www.imdb.com"]

    start_urls = ["https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту", "https://www.imdb.com"]
   # download_delay = 1


    def parse(self, response):
        mw_pages_div = response.css('div#mw-pages')
        if mw_pages_div:
            for film in mw_pages_div.css('.mw-category-group li'):
                film_title = film.css('a::text').get()
                film_link = film.css('a::attr(href)').get()
                yield response.follow(url=response.urljoin(film_link), callback=self.parse_film_info, meta={'title': film_title})
               
        next_page = response.xpath('//div[@id="mw-pages"]//a[contains(text(), "Следующая страница")]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)


    def parse_film_info(self, response):

        def clean_digit(str): 
            cleaned_str = ', '.join(part.strip() for part in re.split(r',', str) if any(word[0].isdigit() for word in part.split()))
            return cleaned_str
        
        def clean_alpha(str): 
            cleaned_str = ', '.join(part.strip() for part in re.split(r',', str) if any(word[0].isalpha() for word in part.split()))
            return cleaned_str
        
        title = response.meta['title']
        infobox = response.css('table.infobox')
        if infobox:
            genres =infobox.css('tr:contains("Жанр") td span::text, tr:contains("Жанр") td a::text').getall()
            genres_str = ', '.join(map(str.strip, genres))
            directors = infobox.css('tr:contains("Режиссёр") td span::text, tr:contains("Режиссёр") td a::text, tr:contains("Режиссёр") td li::text').getall()
            directors_str = ', '.join(map(str.strip, directors))
            countries =infobox.css('tr:contains("Стран") td span::text, tr:contains("Стран") td a::text').getall()
            countries_str = ', '.join(map(str.strip, countries))

            years = infobox.css('tr:contains("Год") td').xpath('.//a//text()').getall() 
            years_str = ', '.join(map(str.strip, years))

            imdb_link = infobox.css('th:contains("IMDb") + td span a::attr(href)').get()
            imdb_rating = None
          
            if imdb_link:
                yield scrapy.Request(url=imdb_link, callback=self.parse_imdb_rating, 
                                     meta={'title': title, 'genres': clean_alpha(genres_str), 'directors': clean_alpha(directors_str), 'countries': clean_alpha(countries_str), 'years': clean_digit(years_str)})
            else:
                yield self.construct_output(title, clean_alpha(genres_str), clean_alpha(directors_str), clean_alpha(countries_str), clean_digit(years_str), imdb_rating)

    def parse_imdb_rating(self, response):
        title = response.meta['title']
        genres_str = response.meta['genres'] 
        directors_str = response.meta['directors'] 
        countries_str = response.meta['countries'] 
        years_str = response.meta['years']
        imdb_rating = response.css('div[data-testid="hero-rating-bar__aggregate-rating__score"] span::text').get()

        yield self.construct_output(title, genres_str, directors_str, countries_str, years_str, imdb_rating)

    def construct_output(self, title, genres_str, directors_str, countries_str, years_str, imdb_rating):
        return {
            'Название': title,
            'Жанр': genres_str,
            'Режиссер': directors_str,
            'Страны': countries_str,
            'Год': years_str,
            'IMDb': imdb_rating,
        }
