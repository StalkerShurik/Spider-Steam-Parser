import scrapy
from spider_steam.items import SpiderSteamItem

queries = ['Strategy', 'tanks', 'novel']


def format_price(price):
    price = price.replace('\r', '')
    price = price.replace('\t', '')
    price = price.replace('\n', '')
    price = price.replace('у', '')
    price = price.replace('б', '')
    return price


class SteamspiderSpider(scrapy.Spider):
    name = 'SteamSpider'
    allowed_domains = ['store.steampowered.com']
    start_urls = ['http://store.steampowered.com/']
    page = 0

    def start_requests(self):
        for query in queries:
            self.page = 0
            while self.page <= 2:
                self.page += 1
                url = 'https://store.steampowered.com/search/?&term=' + query + "&page=" + str(self.page)
                yield scrapy.Request(url=url, callback=self.parse_page)

    def parse_page(self, response):
        games = list()

        for game in response.xpath('//a[@class="search_result_row ds_collapse_flag "]/@href').extract():
            if "bundle" not in game:
                games.append(game)

        for game_link in games:
            yield scrapy.Request(url=game_link, callback=self.parse_game_page, \
                                 cookies={'birthtime': '420681234', 'lastagecheckage': '1-0-2000'})

    def parse_game_page(self, response):
        item = SpiderSteamItem()

        path = '/html/body/div[1]/div[7]/div[@id="responsive_page_template_content"]/' \
               'div[@class="game_page_background game"][1]/' \
               'div[@id="tabletGrid"][1]/div[1]/div[@class="page_title_area game_title_area page_content"]/' \
               'div[@class="apphub_HomeHeaderContent"]/div[@class="apphub_HeaderStandardTop"]/' \
               'div[@id="appHubAppName"]/text()'
        name = response.xpath(path).extract()
        path = '/html/body/div[1]/div[7]/div[@id="responsive_page_template_content"]/' \
               'div[@class="game_page_background game"][1]/' \
               'div[@id="tabletGrid"][1]/div[1]/div[@class="page_title_area game_title_area page_content"]/' \
               'div[@class="breadcrumbs"]/div[@class="blockbg"]/a/text()'
        category = response.xpath(path).extract()[1:]

        path = "/html/body/div[1]/div[7]//div[@class='date']/text()"

        date = response.xpath(path).extract()

        path = "/html/body//div[@id='developers_list']/a/text()"

        developer = response.xpath(path).extract()

        path = "/html/body//div[@class='glance_tags popular_tags']/a/text()"

        tags = response.xpath(path).extract()

        for i, tag in enumerate(tags):
            tags[i] = tags[i].replace('\r', '')
            tags[i] = tags[i].replace('\t', '')
            tags[i] = tags[i].replace('\n', '')

        path = "/html/body//div[@class='summary_section']/span[1]/text()"
        reviews_general = response.xpath(path).extract()[0]

        path = "/html/body//div[@class='summary_section']/span[2]/text()"
        reviews_count = response.xpath(path).extract()[0]

        path = "/html/body//div[@class='game_area_purchase_platform']/span/@class"
        platforms = response.xpath(path).extract()

        unique_platforms = set(platforms)
        platforms = list(unique_platforms)
        for i, platform in enumerate(platforms):
            platforms[i] = platforms[i].replace('platform_img ', '')

        path = "/html/body//div[@class='game_purchase_price price']/text()"
        price = response.xpath(path).extract()[0]
        price = format_price(price)

        item['name'] = name
        item['category'] = category
        item['date'] = date
        item['tags'] = tags
        item['developer'] = developer
        item['reviews'] = [reviews_general, reviews_count]
        item['platforms'] = platforms
        item['price'] = price

        yield item
