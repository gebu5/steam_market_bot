import requests
import datetime


class ProxySession(requests.Session):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    def get(self, *args, **kwargs):
        kwargs['proxies'] = self.bot.requests_proxies()
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        kwargs['proxies'] = self.bot.requests_proxies()
        return super().post(*args, **kwargs)

    def put(self, *args, **kwargs):
        kwargs['proxies'] = self.bot.requests_proxies()
        return super().put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        kwargs['proxies'] = self.bot.requests_proxies()
        return super().delete(*args, **kwargs)


def parse_proxy(proxy):
    proxy_type = 'http'
    if type(proxy).__name__ == 'str':
        proxy_user = ''
        proxy_pass = ''
        if r'://' in proxy:
            proxy_type, proxy = proxy.split(r'://')
        if '@' in proxy:
            proxy, logpass = proxy.split('@')
            proxy_user, proxy_pass = logpass.split(':')
        spl_proxy = proxy.split(':')
        proxy_host = spl_proxy[0]
        proxy_port = int(spl_proxy[1])
    elif len(proxy) == 5:
        proxy_type, proxy_host, proxy_port, proxy_user, proxy_pass = proxy
    elif len(proxy) == 4:
        proxy_host, proxy_port, proxy_user, proxy_pass = proxy
    elif len(proxy) == 3:
        proxy_type, proxy_host, proxy_port = proxy
        proxy_user = ''
        proxy_pass = ''
    elif len(proxy) == 2:
        proxy_host, proxy_port = proxy
        proxy_user = ''
        proxy_pass = ''
    else:
        print('WTF: proxies.json')
        return None
    return proxy_type, proxy_host, proxy_port, proxy_user, proxy_pass


def double_split(source, lstr, rstr, n=0):
    SplPage = source.split(lstr, 1)[n + 1]
    SplSplPage = SplPage.split(rstr)[0]
    return SplSplPage


def lrsplit(source, lstr, rstr):
    # Возвращает массив эелементов
    if not lstr in source:
        return []
    SplPage = source.split(lstr)
    SplPage.pop(0)
    SplSplPage = [splitted.split(rstr)[0] for splitted in SplPage]
    return SplSplPage


def spec_lrsplit(source, lstr, rstr, value):
    # Возвращает массив эелементов
    if not lstr in source:
        return []
    SplPage = source.split(lstr)
    SplPage.pop(0)
    SplSplPage = [splitted.split(rstr)[0] for splitted in SplPage if float(splitted.split(rstr)[0].strip()) <= value]
    return SplSplPage


def lprint(mes):
    print(mes)
    with open('log.txt', 'a') as f:
        f.write(datetime.datetime.now().strftime("%d-%m-%Y %H:%M") + ':  ' + mes + '\n')
