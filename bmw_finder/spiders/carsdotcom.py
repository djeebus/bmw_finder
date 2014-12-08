import urllib
import ujson

from itertools import izip_longest
from scrapy.selector import Selector
from scrapy.http.request import Request

from bmw_finder.items import CarInfo
from bmw_finder.spiders import BaseCarSpider, MAX_PRICE

make_model_year_url = 'http://www.cars.com/core-editorial/crp/mmyCrp.json'

HUD_CODE = 'S610A'


class CarsDotComSpider(BaseCarSpider):
    name = 'cars.com'

    def __init__(self, **kwargs):
        super(CarsDotComSpider, self).__init__(**kwargs)

        self._php_session_id = None

        self._models = {
            '20487': '550i',
            '21392': 'm3',
        }

    def _create_request(self, model_ids, year_ids):
        pass

    def start_requests(self):
        query = [
            ('bsId', '20211'),          # body style == sedan
            ('stkTyp', 'U'),            # used cars
            ('mkId', '20005'),          # make id == bmw
            ('mdId', '20487'),          # model id == 550i
            ('mdId', '21392'),          # model id == m3
            ('prMx', str(MAX_PRICE)),   # max price
            ('rd', '100000'),           # radius == all
            ('zc', '94301'),            # zip code
            ('transTypeId', '28112'),   # manual transmission
            ('yrId', '34923'),          # year: 2011
            ('yrId', '39723'),          # year: 2012
            ('rpp', '250'),             # 250 results per page
            ('bsId', '20211'),          # sedan
        ]

        yield Request(
            url='http://www.cars.com/for-sale/searchresults.action?%s' % urllib.urlencode(query),
            callback=self._parse_index,
        )

        query.append(('cpo', 'Y'))

        yield Request(
            url='http://www.cars.com/for-sale/searchresults.action?%s' % urllib.urlencode(query),
            callback=self._parse_index,
            meta={
                'make': 'BMW',
                'model': '550i',
            }
        )

    def _parse_index(self, response):
        selector = Selector(response)
        vehicles = selector.xpath('//div[contains(@class, "vehicle")]/@data-js-vehicle-row')
        for vehicle in vehicles:
            json = vehicle.extract()
            car_data = ujson.loads(json)

            listing_id = car_data['listingId']

            yield Request('http://www.cars.com/vehicledetail/detail/%s/overview/' % listing_id,
                          callback=self._parse_overview,
                          meta={
                              'listing_id': listing_id,
                              'price': car_data['price'],
                              'make': 'BMW',
                              'model': self._models[str(car_data['modelId'])],
                          })

        right_arrows = selector.xpath('//div[contains(@class, "simple-pagination")]/a[@class="right"]/@href')
        for right_arrow in right_arrows:
            yield Request(right_arrow.extract()[0], callback=self._parse_overview)

    def _parse_overview(self, response):
        selector = Selector(response)

        year = int(selector.xpath('//h1/text()').extract()[0].split()[0])
        details = selector.xpath('//ul[contains(@class, "vehicle-details")]/li')

        car_info = CarInfo()
        for name_li, value_li in _grouper(details, 2):
            name = name_li.xpath('.//text()').extract()[0]
            value = value_li.xpath('.//text()').extract()[0]

            if name == 'Mileage':
                car_info['mileage'] = value

            if name == 'VIN':
                car_info['vin'] = value

        car_info['year'] = year
        car_info['make'] = response.meta['make']
        car_info['model'] = response.meta['model']
        car_info['price'] = response.meta['price']
        car_info['listing_id'] = response.meta['listing_id']
        car_info['url'] = 'http://www.cars.com/vehicledetail/detail/%s/overview/' % response.meta['listing_id']

        self._store_in_redis(car_info)
        return car_info


def _grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)