import urllib

from scrapy.http.request import Request
from scrapy.selector import Selector

from bmw_finder.items import CarInfo
from bmw_finder.spiders import BaseCarSpider


class BmwComSpider(BaseCarSpider):
    name = 'bmw.com'

    def start_requests(self):
        query = [
            ('normalTransmission', 'Manual'),
            ('year', '2010-2012'),
            ('odometer', ''),
            ('highwayMpg', ''),
            ('superModel', '5 Series'),
            ('gvModel', '550i'),
            ('compositeType', 'used'),
            ('geoZip', '94301'),
            ('geoRadius', '0'),
            ('searchLinkText', 'SEARCH'),
            ('showSelections', 'true'),
            ('facetbrowse', 'true'),
            ('showFacetCounts', 'true'),
            ('showSubmit', 'true'),
            ('showRadius', 'true'),
        ]
        yield Request(
            url='http://cpo.bmwusa.com/used-inventory/index.htm?%s' % urllib.urlencode(query),
            callback=self._parse_index,
        )

    def _parse_index(self, response):
        selector = Selector(response)

        for detail_url in selector.xpath('//a[@class="url"]/@href'):
            yield Request(
                url='http://cpo.bmwusa.com%s' % detail_url.extract(),
                callback=self._parse_detail,
            )

    def _parse_detail(self, response):
        selector = Selector(response)

        car_info = CarInfo()
        car_info['listing_id'] = response.request.url.split('/')[5].split('-')[3].split('.')[0]
        car_info['price'] = selector.xpath('//strong[@class="h1 price"]/text()').extract()[0].replace('$', '')
        car_info['url'] = response.request.url

        title_parts = selector.xpath('//h1/text()').extract()[0].split()
        car_info['make'] = title_parts[1]
        car_info['model'] = ' '.join(title_parts[2:])

        detail_rows = selector.xpath('//ul[@class="details"]/li[@class]')
        for row in detail_rows:
            detail_type = row.xpath('@class').extract()[0]
            value = row.xpath('span[@class="value"]/text()').extract()[0]

            if detail_type == "vin":
                car_info['vin'] = value
            elif detail_type == "odometer":
                car_info['mileage'] = value
            elif detail_type == "year":
                car_info['year'] = value

        self._store_in_redis(car_info)
        return car_info