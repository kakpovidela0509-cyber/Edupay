from PySide6.QtWidgets import QApplication

from src.database.connection import init_db
from src.ui.main_window import MainWindow


def main():
    init_db()
    app = QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
