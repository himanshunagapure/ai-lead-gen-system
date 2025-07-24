import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy import signals
from typing import List, Dict, Any

class TravelSpider(scrapy.Spider):
    name = "travel_spider"
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 8,
        'USER_AGENT': 'Mozilla/5.0 (compatible; TravelBot/1.0)'
    }

    def __init__(self, start_urls: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = start_urls
        self.results = []

    def parse(self, response):
        # Basic content extraction
        item = {
            'url': response.url,
            'status': response.status,
            'title': response.xpath('//title/text()').get(),
            'html': response.text,
        }
        self.results.append(item)
        # Pagination handling (example: next page link)
        next_page = response.xpath('//a[contains(text(), "Next")]/@href').get()
        if next_page:
            yield response.follow(next_page, self.parse)
        # Form detection (basic)
        forms = response.xpath('//form')
        if forms:
            item['has_form'] = True
        else:
            item['has_form'] = False
        yield item

def run_scrapy_spider(urls: List[str]) -> List[Dict[str, Any]]:
    process = CrawlerProcess(get_project_settings())
    results = []

    def collect_results(item, response, spider):
        results.append(item)

    for url in urls:
        crawler = process.create_crawler(TravelSpider)
        crawler.signals.connect(collect_results, signal=signals.item_scraped)
        process.crawl(crawler, start_urls=[url])

    process.start()
    return results 