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
    app._login_win = login_win  # mantém referência viva

    def on_login(user: dict):
        try:
            from main_window import MainWindow
            main_win = MainWindow(db, user)
            main_win.show()
            app._main_win = main_win  # mantém referência viva
            login_win.close()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None, "Erro ao abrir o sistema",
                f"Não foi possível abrir a janela principal:\n\n{e}"
            )

    login_win.login_successful.connect(on_login)
    login_win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
