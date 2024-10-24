import sys
import time
import hashlib
from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog, QLineEdit
from main_window import MainWindow
from database import init_db, close_db_connections, verify_database_integrity
from backup import create_auto_backup, restore_from_auto_backup, try_restore_database
import os

def handle_database_error(e):
    print(f"Error al inicializar o verificar la base de datos: {e}")
    close_db_connections()  
    
    success, timestamp = try_restore_database()
    if success:
        QMessageBox.information(None, "Restauración de base de datos", 
                                f"Se ha restaurado la base de datos debido a un fallo.\n"
                                f"Fecha y hora del backup: {timestamp}")
        return True
    else:
        QMessageBox.critical(None, "Error", "No se pudo restaurar la base de datos después de varios intentos.")
        return False

def prompt_password():
    hashed_password = 'a05ba560427a528100410c8553ffb49df7493d8a6308922c200fd81c538cf8fe'
    
    while True:
        input_password, ok = QInputDialog.getText(
            None, 
            'Autenticación Requerida', 
            'Ingrese la contraseña:', 
            QLineEdit.Password
        )

        if not ok:
            return False

        if input_password:
            hashed_input = hashlib.sha256(input_password.encode()).hexdigest()
            if hashed_input == hashed_password:
                return True
            else:
                QMessageBox.warning(None, "Error de Autenticación", "Contraseña incorrecta. Intente nuevamente.")
        else:
            QMessageBox.warning(None, "Error", "Por favor, ingrese una contraseña.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    if not prompt_password():
        sys.exit(0) 
    
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
