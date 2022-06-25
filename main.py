import random
import time
import sys
import threading
import requests
import os
import datetime

import utils
from gui import *
from parser import Parser
from steam_auth import SteamAuth
from core import *
from functools import partial
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


class App(QtWidgets.QMainWindow, Ui_MainWindow, BotCore):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.bots = []
        self.bad_prox = []
        self.setup_default()
        self.numbot = 0
        self.steam_session, user = self.check_steam_session()
        self.is_login = False
        if self.steam_session:
            self.success_login(user)
            self.steam_login_group.hide()
            self.is_login = True
            self.driver = self.download_browser()
        self.open_needed()
        #self.chrome, self.chrome_options = self.download_browser()
        self.player = QMediaPlayer()

    def setup_default(self):
        with open('proxies.json') as f:
            proxies = json.load(f)
            self.len_proxy = len(proxies)
        with open('config.json') as f:
            self.config = json.load(f)
        self.setGeometry(400, 200, 950, 600)  # Ставим размер обязательно в коде
        self.setWindowTitle('CsBot')  # Ставим title

        self.login_loading_label.hide()  # Прячем т.к. на старте не нужен
        self.already_logined_group.hide()  # Прячем т.к. на старте не нужен

        self.login_button.clicked.connect(self.login)
        self.logout_button.clicked.connect(self.logout)
        self.run_bot_button.clicked.connect(self.start_parser)
        self.thread = UpdateTable(self.bots)
        self.thread.add_row.connect(self.add_table_row)
        self.thread.del_row.connect(self.delete_row)
        self.thread.play_audio.connect(self.play_audio)
        self.thread.start()
        for column in range(self.tableWidget.columnCount()):
            self.tableWidget.horizontalHeader().setSectionResizeMode(column, QtWidgets.QHeaderView.Stretch)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.setColumnHidden(5, True)
        self.tableWidget.setColumnHidden(6, True)

    # Всплывающее окно для ввода steam guard кода
    def steam_guard_popup(self):
        steam_code, is_done = QtWidgets.QInputDialog.getText(
            self, 'Steam Guard', '\nВведите код:')

        return steam_code, is_done

    # Всплывающее окно с предупреждением о пустых значениях
    def empty_values_popup(self):
        popup = QtWidgets.QMessageBox(self)
        popup.setWindowTitle('Пустые значения')
        popup.setText('\n\nОдно или несколько полей не были заполнены!\t')

        popup.exec_()

    def error_values_popup(self, message):
        popup = QtWidgets.QMessageBox(self)
        popup.setWindowTitle('Error')
        popup.setText(f'\n\n{message}\t')

        popup.exec_()

    # Проверка на пустоту
    def is_empty(self, value, value_opt=True, show_warning=True):
        if isinstance(value, list):
            for v in value:
                if not v:
                    if show_warning:
                        self.empty_values_popup()
                    return True
        else:
            if not value and value_opt:
                if show_warning:
                    self.empty_values_popup()
                return True
        return False

    def login(self):
        account_name = self.account_name_input.text()
        password = self.account_pass_input.text()

        if self.is_empty([account_name, password]):
            return False

        if not self.steam_session:
            steam_auth, result = self.login_steamacc(account_name, password)
            if not result:
                self.error_values_popup('Неверный логин или пароль')
                return
        self.login_loading_label.hide()
        steam_code, is_done = self.steam_guard_popup()
        if not is_done:  # Хз пока---------
            return False
        if self.is_empty(steam_code):
            return False

        self.steam_login_group.hide()
        self.login_loading_label.show()

        if not self.steam_session:
            result, self.steam_session = steam_auth.steam_guard(steam_code)
            while not result:
                self.error_values_popup('Неверный код Steam Guard')
                steam_code, is_done = self.steam_guard_popup()
                result, self.steam_session = steam_auth.steam_guard(steam_code)
            user = steam_auth.get_user_and_jpg()
            self.success_login(user)
            self.is_login = True
            self.driver = self.download_browser()

    def success_login(self, user):
        self.login_loading_label.hide()
        self.already_logined_group.show()
        self.logined_account_name_label.setText(user)
        dir = os.path.abspath(os.curdir).replace('\\', '/')
        self.frame.setStyleSheet("QFrame {\n"
                                 f"    border-image: url(\"{dir}/images/icon.jpg\") 0 0 0 0 stretch stretch;\n"
                                 "}")

    def login_steamacc(self, account, password):
        steam_auth = SteamAuth(self.numbot, account, password)
        result = steam_auth.login_steam()
        return steam_auth, result

    def logout(self):
        self.steam_login_group.show()
        self.already_logined_group.hide()
        self.steam_session = None
        self.is_login = False
        with open('cookies.json', 'w') as f:
            json.dump({}, f)
        self.driver.quit()

    def check_steam_session(self):
        steam_session = requests.Session()
        with open('cookies.json', 'r') as f:
            file = json.load(f)
            if not file:
                return None, None
            cookies = file['cookies']
            headers = file['headers']
        for key, value in cookies.items():
            steam_session.cookies.set(key, value)
        r = steam_session.get('https://steamcommunity.com/login/home/?goto=', headers=headers)
        if 'login' in r.url:
            return None, None
        return steam_session, file['user']

    def start_parser(self):
        url = self.url_input.text()
        price_down = self.price_input.value()
        price_up = self.price_input_2.value()
        float_value_down = self.float_value_input.value()
        float_value_up = self.float_value_input_2.value()
        thread_name = self.thread_name_input.text()
        pattern_down = self.paint_seed_input.value()
        pattern_up = self.paint_seed_input_2.value()

        if self.is_empty([url, price_up, thread_name]):
            return False
        if self.is_empty(float_value_up, float_value_down, show_warning=False) and self.is_empty(pattern_down,
                                                                                                 pattern_up,
                                                                                                 show_warning=False):
            self.empty_values_popup()
            return False

        with open('needed.json') as f:
            file = json.load(f)
        if not file:
            numb_prox = self.len_proxy
            sum_val = self.len_proxy // 2
        else:
            numb_prox = self.len_proxy // len(file)
            sum_val = numb_prox
        numb_prox = random.randint(0, self.len_proxy - sum_val - 100)
        self.add_item(url, price_down, price_up, float_value_down, float_value_up, pattern_down, pattern_up,
                      thread_name, numb_prox, sum_val)

    def open_needed(self):
        with open('needed.json') as f:
            file = json.load(f)

        if not file:
            return
        numb_prox = self.len_proxy // len(file)
        sum_val = numb_prox
        print(numb_prox)
        print(len(file))

        for thread in file:
            self.add_item(thread['url'], thread['price_down'], thread['price_up'], thread['float_value_down'],
                          thread['float_value_up'], thread['pattern_down'], thread['pattern_up'], thread['thread_name'], numb_prox, sum_val,
                          True)
            numb_prox += sum_val

    def start_bot(self, url, price_down, price_up, float_value_down, float_value_up, pattern_down, pattern_up,
                  thread_name, numb_prox, sum_val, from_file=False):
        numbot = random.randint(0, self.len_proxy - 1)
        bot = Parser(numbot, url, price_down, price_up, float_value_down, float_value_up, pattern_down, pattern_up,
                     self.len_proxy, thread_name, self.config, numb_prox, sum_val)
        threading.Thread(target=bot.body, daemon=True).start()
        self.bots.append(bot)
        if from_file:
            return
        with open('needed.json') as f:
            file = json.load(f)
        file.append({'url': url, 'price_down': price_down, 'price_up': price_up, 'float_value_down': float_value_down,
                     'float_value_up': float_value_up, 'pattern_down': pattern_down, 'pattern_up': pattern_up,
                     'thread_name': thread_name})
        with open('needed.json', 'w') as f:
            json.dump(file, f, indent=4, ensure_ascii=False)

    def add_item(self, url, price_down, price_up, float_value_down, float_value_up, pattern_down, pattern_up,
                 thread_name, numb_prox, sum_val, from_file=False):
        # Создаем сам виджет (группу)
        thread_group = QtWidgets.QGroupBox()
        thread_group.setStyleSheet("QGroupBox {"
                                   "     border: none;"
                                   "     border-bottom: 1px solid gray;"
                                   "     margin: 0px;"
                                   "}")
        vertical_layout = QtWidgets.QVBoxLayout()
        vertical_layout.setContentsMargins(10, 3, 10, 3)
        vertical_layout.setSpacing(20)
        thread_group.setLayout(vertical_layout)

        # Добавляем элементы к виджету
        horizontal_layout = QtWidgets.QHBoxLayout()
        horizontal_layout.setSpacing(0)

        l_style = ("QLabel {"
                   "    font-size: 16px;"
                   "}")

        thread_name_label = QtWidgets.QLabel(
            f'{thread_name} | Price: {price_down} - {price_up} | Float: {float_value_down} - {float_value_up} | PaintSeed: {pattern_down} - {pattern_up}')
        thread_name_label.setStyleSheet(l_style)

        delete_button = QtWidgets.QPushButton('X')
        delete_button.setFixedSize(20, 20)
        delete_button.setStyleSheet("QPushButton {"
                                    "   color: red;"
                                    "   background-color: #403c55;"
                                    "}")

        horizontal_layout.addWidget(thread_name_label)
        horizontal_layout.addWidget(delete_button)

        vertical_layout.addLayout(horizontal_layout)

        # Создаем lw_item, задаем ему размер, виджет и добавляем в listWidget
        list_widget_item = QtWidgets.QListWidgetItem()
        list_widget_item.setSizeHint(thread_group.sizeHint())
        self.listWidget.addItem(list_widget_item)
        self.listWidget.setItemWidget(list_widget_item, thread_group)
        delete_button.clicked.connect(partial(self.delete_thread, thread_name, list_widget_item))
        self.start_bot(url, price_down, price_up, float_value_down, float_value_up, pattern_down, pattern_up,
                       thread_name, numb_prox, sum_val, from_file)

    def add_table_row(self, list_info, url, thread):
        row_position = self.tableWidget.rowCount()
        self.tableWidget.insertRow(0)
        self.tableWidget.setRowHeight(row_position, 25)

        item = QtWidgets.QTableWidgetItem(list_info[0])
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tableWidget.setItem(0, 0, item)
        item = QtWidgets.QTableWidgetItem(str(list_info[1]))
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tableWidget.setItem(0, 1, item)
        item = QtWidgets.QTableWidgetItem(str(list_info[2])[:7])
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tableWidget.setItem(0, 2, item)
        item = QtWidgets.QTableWidgetItem(str(list_info[3]))
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tableWidget.setItem(0, 3, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tableWidget.setItem(0, 4, item)
        item = QtWidgets.QTableWidgetItem(thread)
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tableWidget.setItem(0, 5, item)
        item = QtWidgets.QTableWidgetItem(list_info[4])
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tableWidget.setItem(0, 6, item)
        buy_button = QtWidgets.QPushButton('Купить')
        buy_button.setStyleSheet("QPushButton {"
                                 "  color: green;"
                                 "  background-color: #403c55;"
                                 "  font-size: 16px;"
                                 "}")
        self.tableWidget.setCellWidget(0, 4, buy_button)
        buy_button.clicked.connect(partial(self.buy_item_link, list_info[4], list_info[5], url))

    def delete_thread(self, thread_name, item):
        index = self.listWidget.row(item)
        self.listWidget.takeItem(index)
        for bot in self.bots:
            if bot.thread_name == thread_name:
                remove_bot = bot
                bot.terminate = True
        self.bots.remove(remove_bot)
        with open('needed.json') as f:
            needed = json.load(f)
        for thread in needed:
            if thread['thread_name'] == thread_name:
                to_remove = thread
        needed.remove(to_remove)
        with open('needed.json', 'w') as f:
            json.dump(needed, f, indent=4, ensure_ascii=False)
        remove_list = []
        for i in range(self.tableWidget.rowCount()):
            if thread_name == self.tableWidget.item(i, 5).text():
                remove_list.append(i)
        remove_list.reverse()
        for i in remove_list:
            self.tableWidget.removeRow(i)

    def buy_item_link(self, js_code, page, url):
        if not self.is_login:
            self.error_values_popup('Необходимо авторизоваться в Steam аккаунт!')
            return False
        threading.Thread(target=self.open_browser, args=(js_code, url, page,), daemon=True).start()

    def open_browser(self, js_code, url, page):
        self.driver.get(url)
        time.sleep(2)
        self.driver.execute_script(f'g_oSearchResults.GoToPage({page})')
        time.sleep(2)
        try:
            self.driver.execute_script(js_code)
        except:
            self.driver.quit()

    def download_browser(self):
        user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                      ' AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/96.0.4664.45 Safari/537.36')
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_experimental_option("detach", True)
        chrome_driver = ChromeDriverManager().install()
        driver = webdriver.Chrome(chrome_driver, options=chrome_options)
        driver.get('https://steamcommunity.com/login/home/?goto=')
        for c in self.steam_session.cookies:
            driver.add_cookie({'name': c.name, 'value': c.value, 'path': c.path})
        driver.get('https://steamcommunity.com/market/')
        time.sleep(2)
        return driver

    def play_audio(self):
        dir = os.path.abspath(os.curdir).replace('\\', '/')
        file_path = f'{dir}/notification.mp3'
        url = QUrl.fromLocalFile(file_path)
        content = QMediaContent(url)
        self.player.setMedia(content)
        self.player.play()

    def delete_row(self, js):
        to_remove = []
        for i in range(self.tableWidget.rowCount()):
            if js == self.tableWidget.item(i, 6).text():
                to_remove.append(i)
        to_remove.reverse()
        for i in to_remove:
            self.tableWidget.removeRow(i)


class UpdateTable(QtCore.QThread):
    add_row = QtCore.pyqtSignal(list, str, str)
    del_row = QtCore.pyqtSignal(str)
    play_audio = QtCore.pyqtSignal()

    def __init__(self, bots):
        super(UpdateTable, self).__init__()
        self.bots = bots

    def run(self):
        while True:
            for bot in self.bots:
                if bot.q_add.qsize():
                    result = bot.q_add.get()
                    for info in result:
                        self.add_row.emit(info, bot.URL, bot.thread_name)
                    self.play_audio.emit()
                if bot.q_del.qsize():
                    result = bot.q_del.get()
                    for info in result:
                        self.del_row.emit(info[4])
            self.msleep(5000)


class CreateTable(QtCore.QThread):
    add_item = QtCore.pyqtSignal(str, float, float, float, float, float, float, str, bool, int)

    def __init__(self):
        super(CreateTable, self).__init__()

    def run(self):
        print('ag')
        with open('needed.json') as f:
            file = json.load(f)
        i = 0
        for thread in file:
            i += 1
            self.add_item.emit(thread['url'], thread['price_down'], thread['price_up'], thread['float_value_down'],
                               thread['float_value_up'], thread['pattern_down'], thread['pattern_up'],
                               thread['thread_name'],
                               True, i)


if __name__ == '__main__':
    app_sys = QtWidgets.QApplication(sys.argv)
    app = App()
    app.show()
    app_sys.exec_()
