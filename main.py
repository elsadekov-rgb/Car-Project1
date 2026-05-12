import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from PyQt6.QtWidgets import QApplication
from database.models import init_db
from ui.main_window import MainWindow

os.makedirs("resources/images", exist_ok=True)

if __name__ == "__main__":
    init_db()
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    print("все работает")
    sys.exit(app.exec())