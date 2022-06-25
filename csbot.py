import PyQt5.Qt
from PyQt5 import QtWidgets, QtCore
import gui
import sys


def clickable(widget):
    print('asdasd')
    class Filter(QtCore.QObject):
        clicked = QtCore.pyqtSignal()

        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == PyQt5.Qt.QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        # The developer can opt for .emit(obj) to get the object within the slot.
                        return True
            return False

    filter_ = Filter(widget)
    widget.installEventFilter(filter_)
    return filter_.clicked


class App(QtWidgets.QMainWindow, gui.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setGeometry(400, 200, 950, 700)  # Ставим размер обязательно в коде
        self.setWindowTitle('CsBot')  # Ставим title

        self.login_loading_label.hide()  # Прячем т.к. на старте не нужен
        self.already_logined_group.hide()  # Прячем т.к. на старте не нужен

        self.login_button.clicked.connect(self.login)
        self.logout_button.clicked.connect(self.logout)
        self.run_bot_button.clicked.connect(self.add_item)
        self.listWidget.itemClicked.connect(self.item_clicked)

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

    # Проверка на пустоту
    def is_empty(self, value):
        if isinstance(value, list):
            for v in value:
                if not v:
                    self.empty_values_popup()
                    return True
        else:
            if not value:
                self.empty_values_popup()
                return True
        return False

    def login(self):
        account_name = self.account_name_input.text()
        password = self.account_pass_input.text()

        if self.is_empty([account_name, password]):
            return False

        #
        # --> login request
        #

        steam_code, is_done = self.steam_guard_popup()
        if not is_done:  # Хз пока---------
            pass
        if self.is_empty(steam_code):
            return False

        self.steam_login_group.hide()
        self.login_loading_label.show()

        #
        # --> steam guard sent request
        #

        # if successful_login:
        self.login_loading_label.hide()
        self.already_logined_group.show()

    def logout(self):
        self.steam_login_group.show()
        self.already_logined_group.hide()

    def add_item(self):
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
        thread_name_label = QtWidgets.QLabel(self.thread_name_input.text())
        thread_name_label.setStyleSheet(l_style)
        from random import randint
        thread_amount_label = QtWidgets.QLabel(f'{randint(10, 500)} шт.')
        thread_amount_label.setStyleSheet(l_style)

        delete_button = QtWidgets.QPushButton('X')
        delete_button.setFixedSize(20, 20)
        delete_button.setStyleSheet("QPushButton {"
                                    "   color: red;"
                                    "   background-color: #403c55;"
                                    "}")

        horizontal_layout.addWidget(thread_name_label)
        horizontal_layout.addWidget(thread_amount_label)
        horizontal_layout.addWidget(delete_button)

        thread_table = QtWidgets.QTableWidget()
        thread_table.setEditTriggers(PyQt5.Qt.QAbstractItemView.NoEditTriggers)
        thread_table.setSortingEnabled(True)
        thread_table.hide()
        thread_table.setMaximumSize(QtCore.QSize(16777215, 151))
        thread_table.horizontalHeader().setStretchLastSection(True)
        thread_table.setStyleSheet("QTableWidget {"
                                   "    border: none;"
                                   "    color: rgb(136, 143, 147);"
                                   "    background-color: #2C2A37;"
                                   "}"
                                   "QHeaderView::section {"
                                   "    background-color: #2C2A37;"
                                   "}")

        thread_table.setColumnCount(4)
        thread_table.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem('Цена'))
        thread_table.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem('Float'))
        thread_table.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem('PaintSeed'))
        thread_table.setHorizontalHeaderItem(3, QtWidgets.QTableWidgetItem('URL'))
        thread_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        thread_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        thread_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        thread_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)

        self.add_table_row(thread_table, '0.27 / 28.35р', '0.101853', '280')
        self.add_table_row(thread_table, '0.28 / 29.35р', '0.201854', '281')
        self.add_table_row(thread_table, '0.29 / 30.35р', '0.301855', '282')
        self.add_table_row(thread_table, '0.30 / 31.35р', '0.401854', '283')
        self.add_table_row(thread_table, '0.31 / 32.35р', '0.501855', '284')
        self.add_table_row(thread_table, '0.32 / 33.35р', '0.601855', '285')

        vertical_layout.addLayout(horizontal_layout)
        vertical_layout.addWidget(thread_table)

        # Создаем lw_item, задаем ему размер, виджет и добавляем в listWidget
        list_widget_item = QtWidgets.QListWidgetItem()
        list_widget_item.setSizeHint(thread_group.sizeHint())
        self.listWidget.addItem(list_widget_item)
        self.listWidget.setItemWidget(list_widget_item, thread_group)

    @staticmethod
    def add_table_row(table, price, float_, paint_seed):
        row_position = table.rowCount()
        table.insertRow(row_position)
        table.setRowHeight(row_position, 25)

        item = QtWidgets.QTableWidgetItem(price)
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        table.setItem(row_position, 0, item)
        item = QtWidgets.QTableWidgetItem(float_)
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        table.setItem(row_position, 1, item)
        item = QtWidgets.QTableWidgetItem(paint_seed)
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        table.setItem(row_position, 2, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        table.setItem(row_position, 3, item)
        buy_button = QtWidgets.QPushButton('Купить')
        buy_button.setStyleSheet("QPushButton {"
                                 "  color: green;"
                                 "  background-color: #403c55;"
                                 "  font-size: 16px;"
                                 "}")
        table.setCellWidget(row_position, 3, buy_button)

    def find_table(self, index):
        item = self.listWidget.takeItem(index)
        thread_group = self.listWidget.itemWidget(item)
        table = thread_group.layout().itemAt(1).widget()

        return table

    def item_clicked(self, item):
        thread_group = self.listWidget.itemWidget(item)
        table = thread_group.layout().itemAt(1).widget()

        if table.isHidden():
            table.show()
            item.setSizeHint(QtCore.QSize(100, thread_group.sizeHint().height() + 50))
        else:
            table.hide()
            item.setSizeHint(thread_group.sizeHint())


if __name__ == '__main__':
    app_sys = QtWidgets.QApplication(sys.argv)
    app = App()
    app.show()
    app_sys.exec_()
