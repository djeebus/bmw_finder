# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class VinInfo(Item):
    vin = Field()


class CarInfo(Item):
    vin = Field()
    listing_id = Field()
    price = Field()
    options = Field()
    vehicle = Field()
    mileage = Field()
    url = Field()
