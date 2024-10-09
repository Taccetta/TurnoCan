import sys
import time
from PyQt5.QtWidgets import QApplication, QMessageBox
from main_window import MainWindow
from database import init_db, close_db_connections, verify_database_integrity
from backup import create_auto_backup, restore_from_auto_backup, try_restore_database
import os

def handle_database_error(e):
    print(f"Error al inicializar o verificar la base de datos: {e}")
    close_db_connections()  # Cerrar todas las conexiones existentes
    
    success, timestamp = try_restore_database()
    if success:
        QMessageBox.information(None, "Restauración de base de datos", 
                                f"Se ha restaurado la base de datos debido a un fallo.\n"
                                f"Fecha y hora del backup: {timestamp}")
        return True
    else:
        QMessageBox.critical(None, "Error", "No se pudo restaurar la base de datos después de varios intentos.")
        return False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    try:
        init_db()
        if not verify_database_integrity():
            raise Exception("La base de datos no pasó la verificación de integridad")
        create_auto_backup()
    except Exception as e:
        if not handle_database_error(e):
            sys.exit(1)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())