import redis
import requests
import scrapy.log
import time
import ujson

from scrapy.spider import BaseSpider
from scrapy.selector import Selector


MAX_PRICE = 45000
MAX_MILES = 75000


class BaseCarSpider(BaseSpider):
    LISTING_INFO_KEY = 'listing:%s'
    RAW_VIN_INFO_KEY = 'rawvin:%s'

    def __init__(self, **kwargs):
        super(BaseCarSpider, self).__init__(**kwargs)

        self._redis = redis.Redis(host='downloader')

    def _store_in_redis(self, car_info):
        if car_info['vin']:
            vehicle_info, options = self._get_vin_info_from_bmwarchive(car_info['vin'])

            car_info['vehicle'] = vehicle_info
            car_info['options'] = options

        payload = ujson.dumps(dict(car_info))
        redis_key = self.LISTING_INFO_KEY % car_info['listing_id']
        self._redis.set(redis_key, payload)

    def _get_cached_bmwarchive_response(self, vin):
        response = self._redis.get(self.RAW_VIN_INFO_KEY % vin)
        if not response:
            return

        if 'Sicherheitscode' not in response:
            return response

        self.log('cached response has no valid data, dismissing', scrapy.log.WARNING)
        return

    def _get_vin_info_from_bmwarchive(self, vin):
        response = self._get_cached_bmwarchive_response(vin)
        if response:
            selector = Selector(text=response)
            tables = selector.xpath('//table')
            if len(tables) == 3:
                vehicle_table, standard_table, options_table = tables[:3]
            else:
                response = None

        if not response:
            body = 'vin=%s' % vin[-7:]
            while True:
                response = requests.post(
                    url='http://www.bmwarchiv.de/vin/bmw-vin-decoder.html',
                    data=body,
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Content-Length': str(len(body)),
                    },
                )

                body = response.content
                if 'Sicherheitscode' in body:
                    self.log('got captchad, sleeping to try again...', level=scrapy.log.WARNING)
                    time.sleep(600)
                    continue
                self._redis.set(self.RAW_VIN_INFO_KEY % vin, body)

                if 'Kein Datensatz zu ' in body:
                    self.log('no records found', level=scrapy.log.WARNING)
                    return [], []

                selector = Selector(text=body)
                tables = selector.xpath('//table')
                if len(tables) >= 3:
                    vehicle_table, standard_table, options_table = tables[:3]
                    break

                self.log('invalid response, going to try again...', level=scrapy.log.WARNING)

        def parse_codes(table):
            rows = table.xpath('tbody/tr')
            for row in rows:
                code, german, english = row.xpath('td')
                code = code.xpath('center/text()').extract()[0]
                english = english.xpath('text()').extract()
                if len(english) > 0:
                    english = english[0]
                else:
                    english = german.xpath('text()').extract()[0]

                yield code, english

        def parse_info(data):
            rows = data.xpath('tbody/tr')
            for row in rows:
                key, value = row.xpath('td')
                key = ''.join(key.xpath('.//text()').extract()[0].rstrip(':'))
                value = ''.join(value.xpath('.//text()').extract())
                yield key, value

        options = {key: value for key, value in parse_codes(options_table)}
        vehicle_info = list(parse_info(vehicle_table))

        return vehicle_info, options

