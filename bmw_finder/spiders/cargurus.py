import ujson
import urllib

from scrapy.http.request import Request
from scrapy.selector import Selector

from bmw_finder.items import CarInfo
from bmw_finder.spiders import BaseCarSpider


class CarGurusSpider(BaseCarSpider):
    name = 'cargurus.com'

    def start_requests(self):
        # d1628 == 5 series
        # m3 == bmw
        query = [
            ('zip', '94301'),
            ('address', 'Palo Alto, CA'),
            ('latitude', '37.443'),
            ('longitude', '-122.151'),
            ('distance', 'NATIONWIDE'),
            ('selectedEntity', 'd1628'),
            ('minPrice', ''),
            ('maxPrice', '41000'),
            ('minMileage', ''),
            ('maxMileage', '75000'),
            ('transmission', 'M'),
            ('bodyStyle', ''),
            ('serviceProvider', ''),
            ('page', '1'),
            ('filterBySourcesString', ''),
            ('filterFeaturedBySourcesString', ''),
            ('displayFeaturedListings', 'true'),
            ('inventorySearchSeoPageType', ''),
            ('inventorySearchWidgetType', 'AUTO'),
            ('allYearsForTrimName', 'false'),
            ('trimNames', '550i'),
        ]

        body = urllib.urlencode(query)

        yield Request(
            url='http://www.cargurus.com/Cars/inventorylisting/ajaxFetchSubsetInventoryListing.action?'
                'sourceContext=carGurusHomePage_false_0&cgLocale=en',
            method='POST',
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': str(len(body)),
            },
            body=body,
            callback=self._parse_index,
        )

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
                }
            )

    def _parse_details(self, response):
        selector = Selector(response)

        car_info = CarInfo()
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