import ujson
import urllib

from scrapy.http.request import Request
from scrapy.selector import Selector

from bmw_finder.spiders import MAX_MILES, MAX_PRICE
from bmw_finder.items import CarInfo
from bmw_finder.spiders import BaseCarSpider


class CarGurusSpider(BaseCarSpider):
    name = 'cargurus.com'

    def _create_index_query(self, page_index):
        query = [
            ('zip', '94301'),
            ('address', 'Palo Alto, CA'),
            ('latitude', '37.443'),
            ('longitude', '-122.151'),
            ('distance', 'NATIONWIDE'),
            ('selectedEntity', 'd1628'),    # 5 series
            ('minPrice', ''),
            ('maxPrice', str(MAX_PRICE)),
            ('minMileage', ''),
            ('maxMileage', str(MAX_MILES)),
            ('transmission', 'M'),
            ('bodyStyle', ''),
            ('serviceProvider', ''),
            ('page', str(page_index)),
            ('filterBySourcesString', ''),
            ('filterFeaturedBySourcesString', ''),
            ('displayFeaturedListings', 'true'),
            ('inventorySearchSeoPageType', ''),
            ('inventorySearchWidgetType', 'AUTO'),
            ('allYearsForTrimName', 'false'),
            ('trimNames', '550i'),
            ('newUsed', '2'),   # used
            ('newUsed', '3'),   # cpo
        ]

        body = urllib.urlencode(query)

        return Request(
            url='http://www.cargurus.com/Cars/inventorylisting/ajaxFetchSubsetInventoryListing.action?'
                'sourceContext=carGurusHomePage_false_0&cgLocale=en',
            method='POST',
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': str(len(body)),
            },
            body=body,
            callback=self._parse_index,
            meta={
                'make': 'BMW',
            }
        )

    def start_requests(self):
        yield self._create_index_query(1)

    def _parse_index(self, response):
        json_body = ujson.loads(response.body)

        for listing in json_body['listings']:
            if listing['trimName'] != '550i':
                continue

            if listing.get('transmission') != 'M':
                continue

            listing_id = listing['id']

            yield Request(
                url='http://www.cargurus.com/Cars/inventorylisting/viewListingDetailAjax.action'
                    '?inventoryListing=%s' % listing_id,
                callback=self._parse_details,
                meta={
                    'listing_id': listing_id,
                    'url': 'http://www.cargurus.com/Cars/inventorylisting/'
                           'viewDetailsFilterViewInventoryListing.action#listing=%s' % listing_id,
                    'price': listing['price'],
                    'mileage': listing['mileage'],
                    'make': response.meta['make'],
                    'model': listing['trimName'],
                    'year': listing['carYear'],
                },
            )

        if json_body['remainingResults']:
            yield self._create_index_query(json_body['page'] + 1)

    def _parse_details(self, response):
        selector = Selector(response)

        car_info = CarInfo()
        car_info['make'] = response.meta['make']
        car_info['model'] = response.meta['model']
        car_info['year'] = response.meta['year']
        car_info['listing_id'] = response.meta['listing_id']
        car_info['price'] = response.meta['price']
        car_info['mileage'] = response.meta['mileage']
        car_info['url'] = response.meta['url']

        vins = selector.xpath('//div[@class="cg-listingDetail-specsWrap"]/table/tr[td[@class="attributeLabel"]'
                              '/text()="VIN:"]/td[@class="attributeValue"]/text()').extract()
        if vins:
            car_info['vin'] = vins[0]

        self._store_in_redis(car_info)
        return car_info