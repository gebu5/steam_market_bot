import random
import time
import threading
import datetime

import utils
from core import *
from queue import Queue


class Parser(BotCore):
    def __init__(self, numbot, url, price_down, price_up, float_value_down, float_value_up, pattern_down, pattern_up, len_proxy, thread_name, config, numb_prox, sum_val):
        super().__init__(numb_prox - sum_val)
        self.numb_prox = numb_prox
        self.sum_val = sum_val
        self.config = config
        self.price_up = price_up
        self.price_down = price_down
        self.float_up = float_value_up
        self.float_down = float_value_down
        self.pattern_up = pattern_up
        self.pattern_down = pattern_down
        self.URL = url
        self.len_proxy = len_proxy
        self.thread_name = thread_name
        if 'filter' in self.URL:
            self.URL = self.URL[:self.URL.find('filter') - 1]
        self.q_add = Queue()
        self.q_del = Queue()
        self.terminate = False
        self.result = []
        self.prev_result = []
        self.count_item = 0
        self.sound = True
        self.bad_prox = []

    def body(self):
        time.sleep(5)
        while True:
            self.result = []
            if len(self.bad_prox) > self.sum_val - 10:
                #utils.lprint(self.thread_name + '  -  Большая часть прокси у данного потока испортились!')
                self.bad_prox = []
            if self.terminate:
                print(self.thread_name)
                print('Я домой')
                return False
            try:
                while self.numbot in self.bad_prox:
                    self.numbot = random.randint(self.numb_prox - self.sum_val, self.numb_prox)
                self.session = utils.ProxySession(self)
                self.start_parser()
                if self.terminate:
                    print(self.thread_name)
                    return False
            except Exception as error:
                utils.lprint(str(error))
                if 'HTTPSConnectionPool' in str(error):
                    if self.numbot not in self.bad_prox:
                        self.bad_prox.append(self.numbot)
                continue
            #utils.lprint(f'{self.thread_name} - Проход номер - {self.checker} | Спаршено - {len(self.result)}')
            if not self.result:
                continue

            if not self.prev_result:
                self.q_add.put(self.result)
                self.prev_result = self.result.copy()
                time.sleep(self.config['delay'])
                continue

            to_add, to_remove = self.check_differnce()
            if to_add:
                self.q_add.put(to_add)
            if to_remove:
                self.q_del.put(to_remove)

            self.prev_result = self.result.copy()
            time.sleep(self.config['delay'])

    def check_differnce(self):
        to_remove = []
        to_add = []
        for info in self.result:
            for prev_info in self.prev_result:
                if info[4] in prev_info:
                    break
            else:
                to_add.append(info)
        for info in self.prev_result:
            for cur_info in self.result:
                if info[4] in cur_info:
                    break
            else:
                to_remove.append(info)
        return to_add, to_remove

    def start_parser(self):
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
            'connection': 'keep-alive',
            'host': 'steamcommunity.com',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': self.user_agent
        }
        r = self.session.get(self.URL, headers=headers)
        if r.status_code != 200:
            #utils.lprint(f'{self.thread_name} - Ошибка при получении запроса! Смена IP')
            if self.numbot not in self.bad_prox:
                self.bad_prox.append(self.numbot)
            return False
        item_id = utils.double_split(r.text, 'Market_LoadOrderSpread( ', ' ')

        headers['X-Requested-With'] = 'XMLHttpRequest'
        url = f'https://steamcommunity.com/market/itemordershistogram?country=RU&language=russian&currency=5&item_nameid={item_id}&two_factor=0'
        r = self.session.get(url, headers=headers)
        if not r.json()['lowest_sell_order']:
            return False

        if int(r.json()['lowest_sell_order']) / 100 < self.price_down:
            utils.lprint(f'{self.thread_name} - Минимальная стоимость на маркете превышает допустимую')
            return False
        headers['X-Prototype-Version'] = '1.7'
        return self.get_items_market(headers)

    def get_items_market(self, headers, tries=2):
        threads = []
        url = f'{self.URL}/render/?query=&start=0&count=10&country=RU&language=russian&currency=5'
        r = self.session.get(url, headers=headers)
        if r.status_code != 200:
            if self.numbot not in self.bad_prox:
                self.bad_prox.append(self.numbot)
            #utils.lprint(f'{self.thread_name} - Ошибка при получении второго запроса! Смена IP')
            while self.numbot in self.bad_prox:
                self.numbot = random.randint(self.numb_prox - self.sum_val, self.numb_prox - 1)
            return self.get_items_market(headers, tries+1)
        total_count = (r.json()['total_count'])
        total = self.config['number_items'] if total_count > self.config['number_items'] else total_count
        self.count_item = 0
        for i in range(0, total, 100):
            thread = threading.Thread(target=self.thread_request, args=(i, headers))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        return True

    def thread_request(self, start, headers, tries=0):
        count_item = start
        thread_session = utils.ProxySession(self)
        url = f'{self.URL}/render/?query=&start={start}&count=100&country=RU&language=russian&currency=5'
        try:
            r = thread_session.get(url, headers=headers)
        except:
            if tries == 2:
                return
            if self.numbot not in self.bad_prox:
                self.bad_prox.append(self.numbot)
            while self.numbot in self.bad_prox:
                self.numbot = random.randint(self.numb_prox - self.sum_val, self.numb_prox - 1)
            return self.thread_request(start, headers, tries + 1)

        if r.status_code != 200:
            if tries == 2:
                return
            if self.numbot not in self.bad_prox:
                self.bad_prox.append(self.numbot)
            while self.numbot in self.bad_prox:
                self.numbot = random.randint(self.numb_prox - self.sum_val, self.numb_prox - 1)
            return self.thread_request(start, headers, tries + 1)
        text = r.text.replace(' ', '')
        divs = text.split(r'market_listing_rowmarket_recent_listing_rowlisting')
        divs.pop(0)
        assets_info = text[text.find('listinginfo'):]
        assets = utils.lrsplit(assets_info, '"asset"', "name")
        asset_dict = {}
        for asset in assets:
            a = utils.double_split(asset, '"id":"', '"')
            d = utils.double_split(asset, '%assetid%D', '"')
            asset_dict[a] = d
        self.parse_query(divs, asset_dict, count_item, thread_session)

    def parse_query(self, divs, asset_dict, count_item, thread_session):
        for div in divs:
            count_item += 1
            if 'Продано' in div:
                continue
            item_name = utils.double_split(div, r'market_listing_item_name\"', 'span')
            item_name = utils.double_split(item_name, '>', '<')
            price = float(
                utils.double_split(div, r'market_listing_pricemarket_listing_price_with_fee\">\r\n\t\t\t\t\t\t',
                                   'pуб').replace(',', '.'))
            if price < self.price_down or price > self.price_up:
                continue

            buy_info = utils.double_split(div, "javascript:BuyMarketListing('", ')').split(',')[-1].strip().replace("'",
                                                                                                                    '')
            m = utils.double_split(div, "javascript:BuyMarketListing('", ')').split(',')[-1].strip().replace("'", '')
            js_code = utils.double_split(div, r'ahref=\"', r'\"')

            url = f'https://api.csgofloat.com/?m={m}&a={buy_info}&d={asset_dict[buy_info]}'
            float_value, pattern = self.check_float(url, thread_session)
            if not float_value and not pattern:
                continue
            if self.float_down > float_value or float_value > self.float_up:
                if not self.pattern_up:
                    continue
            if self.float_down > pattern > self.pattern_up and not self.float_up:
                if not self.float_up:
                    continue
            if count_item <= 10:
                page = 0
            elif count_item % 10 == 0:
                page = self.count_item // 10 - 1
            else:
                page = (count_item // 10)

            info = [item_name, price, float_value, pattern, js_code, page]
            self.result.append(info)

    def check_float(self, url, thread_session):
        try:
            r = thread_session.get(url)
            float_value = r.json()['iteminfo']['floatvalue']
            pattern = r.json()['iteminfo']['paintseed']
        except:
            return None, None
        return float_value, pattern

