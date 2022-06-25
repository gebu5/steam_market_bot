import execjs
import time
import os
import requests

import utils
from core import *


class SteamAuth(BotCore):
    def __init__(self, numbot, account, password):
        super().__init__(numbot)
        self.session = requests.Session()
        self.login_data = {}
        self.headers = {}
        self.account = account
        self.password = password

    def get_key(self):
        key_url = 'https://steamcommunity.com/login/getrsakey/'
        self.headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'ru,en-US;q=0.9,en;q=0.8',
            'connection': 'keep-alive',
            'content-length': '43',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'host': 'steamcommunity.com',
            'origin': 'https://steamcommunity.com',
            'referer': 'https://steamcommunity.com/login/home/?goto=',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': SteamAuth.user_agent,
            'x-requested-with': 'XMLHttpRequest'
        }

        data = {
            'donotcache': str(int(time.time() * 1000)),
            'username': self.account
        }
        r = self.session.get('https://steamcommunity.com/login/home/?goto=')

        r = self.session.post(key_url, data=data, headers=self.headers)
        mod = r.json()['publickey_mod']
        exp = r.json()['publickey_exp']
        timestamp = r.json()['timestamp']

        with open('rsa.js', encoding='utf-8') as f:
            jsdata = f.read()
        password_encrypt = execjs.compile(jsdata).call('getPwd', self.password, mod, exp)
        return password_encrypt, timestamp

    def login_steam(self):
        passw, stamp = self.get_key()
        login_url = 'https://steamcommunity.com/login/dologin/'
        self.login_data = {
            'donotcache': str(int(time.time() * 1000)),
            'username': self.account,
            'password': passw,
            'twofactorcode': '',
            'emailauth': '',
            'loginfriendlyname': '',
            'captchagid': '-1',
            'captcha_text': '',
            'emailsteamid': '',
            'rsatimestamp': stamp,
            'remember_login': 'false',
        }

        r = self.session.post(login_url, data=self.login_data, headers=self.headers)
        if r.json()['message']:
            utils.lprint(r.json()['message'])
        return True

    def steam_guard(self, code):
        login_url = 'https://steamcommunity.com/login/dologin/'
        self.login_data['twofactorcode'] = code
        r = self.session.post(login_url, data=self.login_data, headers=self.headers)
        if not r.json()['success']:
            return False, False
        r = self.session.get('https://steamcommunity.com/login/home/?goto=')
        user_name = utils.double_split(r.text, 'class="actual_persona_name">', '<').strip()
        with open('cookies.json', 'w') as f:
            cookies = self.session.cookies.get_dict()
            file_info = {'cookies': cookies, 'headers': self.headers, 'user':user_name}
            json.dump(file_info, f, indent=4, ensure_ascii=False)
        return True, self.session

    def get_user_and_jpg(self):
        r = self.session.get('https://steamcommunity.com/login/home/?goto=')
        user_name = utils.double_split(r.text, 'class="actual_persona_name">', '<').strip()
        jpg_req = utils.double_split(r.text, '<link rel="image_src" href="', '"')
        r = self.session.get(jpg_req)
        dir = os.path.abspath(os.curdir).replace('\\', '/')
        with open(f"{dir}/images/icon.jpg", 'wb') as f:
            f.write(r.content)
        return user_name



