# Scrapy settings for bmw_finder project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'bmw_finder'

SPIDER_MODULES = ['bmw_finder.spiders']
NEWSPIDER_MODULE = 'bmw_finder.spiders'

CONCURRENT_REQUESTS = 1

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'
