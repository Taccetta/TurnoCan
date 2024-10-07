import sys
import time
from PyQt5.QtWidgets import QApplication, QMessageBox
from main_window import MainWindow
from database import init_db, close_db_connections
from backup import create_auto_backup, restore_from_auto_backup, try_restore_database
import os


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    try:
        init_db()
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        close_db_connections()  # Cerrar todas las conexiones existentes
        
        success, timestamp = try_restore_database()
        if success:
            QMessageBox.information(None, "Restauración de base de datos", 
                                    f"Se ha restaurado la base de datos debido a un fallo.\n"
                                    f"Fecha y hora del backup: {timestamp}")
        else:
            QMessageBox.critical(None, "Error", "No se pudo restaurar la base de datos después de varios intentos.")
            sys.exit(1)
    
    create_auto_backup()
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())