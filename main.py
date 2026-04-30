import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("URANNIO")
    app.setFont(QFont("Segoe UI", 10))

    from database import Database
    db = Database()
    db.initialize()

    from login_window import LoginWindow
    login_win = LoginWindow(db)

    def on_login(user: dict):
        login_win.close()
        from main_window import MainWindow
        main_win = MainWindow(db, user)
        main_win.show()
        app._main_win = main_win  # keep reference

    login_win.login_successful.connect(on_login)
    login_win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
