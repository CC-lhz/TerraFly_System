import sys
from PyQt6.QtWidgets import QApplication
from main_window import MapEditorWindow

def main():
    """地图编辑器主程序入口"""
    app = QApplication(sys.argv)
    window = MapEditorWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()