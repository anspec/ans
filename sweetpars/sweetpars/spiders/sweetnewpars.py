import scrapy


class SweetnewparsSpider(scrapy.Spider):
    name = "sweetnewpars"
    allowed_domains = ["https://divan.ru"]
    #start_urls = ["https://www.divan.ru/category/divany-i-kresla"]
    start_urls = ["https://www.divan.ru/category/svet"]

    def parse(self, response):
        # товары на странице
        products = response.css('div._Ud0k')

        for product in products:
            yield {
                'name': product.css('div.lsooF span::text').get(),
                'price': product.css('div.pY3d2 span::text').get(),
                'url': product.css('a').attrib['href']
            }

        # # пагинация
        # next_page = response.css('a.Pagination__next::attr(href)').get()
        #
        #  if next_page:
        #     yield response.follow(next_page, callback=self.parse)

