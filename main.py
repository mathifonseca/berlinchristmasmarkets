import requests
from bs4 import BeautifulSoup
from ppretty import ppretty
import csv


BASE_URL = "https://www.berlin.de/"
INDEX_PATH = "en/christmas-markets/"

SELECTOR_MARKET_LIST = "list--split"  # unfortunately, they don't use better ids
SELECTOR_ADDRESS = 'location-publictransport'
SELECTOR_INFO = 'info-container-list'

OUTPUT_FILENAME = 'out/markets.csv'


class Market:
    name = ''
    link = ''
    address = ''
    dates = ''
    hours = ''
    price = ''

    def __init__(self, name, link):
        self.name = name
        self.link = link

    def __str__(self):
        return ppretty(self, seq_length=10)


def parse_market(li_market):
    name = li_market.string.strip()
    link = BASE_URL + li_market.contents[0]['href'][1:]
    market = Market(name, link)
    parse_market_deep(market)
    return market


def clean_address(address):
    address = address.replace('\n', ', ')
    address = address.replace(', , City map', '')
    address = address.replace('  City map', '')
    return address


def parse_market_deep(market):
    market_page = requests.get(market.link)
    market_soup = BeautifulSoup(market_page.content, "html.parser")

    found_address = False
    if not market.address:
        dl_market_address = market_soup.find('div', class_=SELECTOR_ADDRESS)
        if dl_market_address and dl_market_address.findNext('dd'):
            market.address = clean_address(dl_market_address.findNext('dd').text.strip())
            found_address = True

    dl_market_info = market_soup.find('dl', class_=SELECTOR_INFO)

    if dl_market_info:
        for dt in dl_market_info.find_all('dt'):
            term = dt.text.strip()
            value = dt.findNext('dd').text.strip().replace('\n', ' ')

            if not found_address:
                if term.lower() == 'address':
                    market.address = clean_address(value)
                elif term.lower() == 'location':
                    market.address = value + ' - ' + market.address

            if term.lower() in ['dates', 'date']:
                market.dates = value
            elif term.lower() == 'start':
                market.dates = value
            elif term.lower() == 'end':
                market.dates = market.dates + ' - ' + value
            elif term.lower() == 'opening hours':
                market.hours = value
            elif term.lower() == 'admission fee':
                market.price = value


def write_csv(results):
    with open(OUTPUT_FILENAME, 'w') as file:
        wr = csv.writer(file, quoting=csv.QUOTE_ALL)
        for r in results:
            wr.writerow([r.name, r.link, r.address, r.dates, r.hours, r.price])


def main():
    page = requests.get(BASE_URL + INDEX_PATH)
    soup = BeautifulSoup(page.content, "html.parser")

    ul_markets = soup.find('ul', class_=SELECTOR_MARKET_LIST)

    total = len(ul_markets)
    print(f'Processing {total} results...')

    results = []
    for idx, li_market in enumerate(ul_markets):
        market = parse_market(li_market)
        results.append(market)
        print(f'{idx+1}/{total}')

    write_csv(results)

    print('Done!')


if __name__ == '__main__':
    main()
