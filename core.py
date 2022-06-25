import json
import utils


class BotCore():
    user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                  ' AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/96.0.4664.45 Safari/537.36')

    def __init__(self, numbot):
        self.numbot = numbot
        self.user_agent = BotCore.user_agent

    def requests_proxies(self):
        ptype, host, port, user, pwd = self.get_proxy()
        proxies = {
            'http': '%s://%s:%s@%s:%d' % (ptype, user, pwd, host, port),
            'https': '%s://%s:%s@%s:%d' % (ptype, user, pwd, host, port)
        }
        return proxies

    def get_proxy(self):
        with open('proxies.json', 'r') as proxiesjson:
            proxies = json.load(proxiesjson)

        proxy = proxies[self.numbot % len(proxies)]

        return utils.parse_proxy(proxy)
