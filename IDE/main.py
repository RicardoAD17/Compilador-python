import sys
from PyQt6.QtWidgets import QApplication
from ide_window import IDE

app = QApplication(sys.argv)
window = IDE()
window.show()
sys.exit(app.exec())