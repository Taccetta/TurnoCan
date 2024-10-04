import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow
from database import init_db

if __name__ == '__main__':
    app = QApplication(sys.argv)
    init_db()
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())