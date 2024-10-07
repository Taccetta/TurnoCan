import os
import shutil
import time
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QSizePolicy, QGridLayout
from database import db_path
from database import init_db


def realizar_backup(backup_path):
    if not os.path.exists(db_path):
        print(f"Error: El archivo {db_path} no existe")
        return False
    try:
        shutil.copy2(db_path, backup_path)
        return True
    except Exception as e:
        print(f"Error al realizar el backup: {str(e)}")
        return False

def restaurar_backup(backup_path):
    if not os.path.exists(backup_path):
        print(f"Error: El archivo {backup_path} no existe")
        return False
    try:
        shutil.copy2(backup_path, db_path)
        return True
    except Exception as e:
        print(f"Error al restaurar el backup: {str(e)}")
        return False

def create_auto_backup():
    time.sleep(1)  # Wait for 1 second
    auto_backup_path = os.path.join(os.path.dirname(db_path), "auto_backup.db")
    if realizar_backup(auto_backup_path):
        print("Auto-backup created successfully")
    else:
        print("Error creating auto-backup")

def restore_from_auto_backup():
    auto_backup_path = os.path.join(os.path.dirname(db_path), "auto_backup.db")
    
    if not os.path.exists(auto_backup_path):
        return False, None
    
    try:
        # Eliminar la base de datos actual si existe
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # Copiar el auto-backup y renombrarlo
        shutil.copy2(auto_backup_path, db_path)
        
        # Obtener la fecha y hora de creación del auto-backup
        timestamp = time.ctime(os.path.getctime(auto_backup_path))
        
        # Intentar inicializar la base de datos restaurada
        init_db()
        
        return True, timestamp
    except Exception as e:
        print(f"Error durante la restauración: {e}")
        return False, None

def try_restore_database(max_attempts=3, delay=1):
    for attempt in range(max_attempts):
        try:
            success, timestamp = restore_from_auto_backup()
            if success:
                return True, timestamp
        except Exception as e:
            print(f"Intento {attempt + 1} fallido: {e}")
            time.sleep(delay)
    return False, None

class BackupWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()
        layout.setColumnStretch(0, 1)  
        layout.setColumnStretch(1, 1)  
        layout.setColumnStretch(2, 1)  

        # Botón Realizar Backup
        backup_btn = QPushButton("Guardar Backup")
        backup_btn.clicked.connect(self.do_backup)
        backup_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        backup_btn.setFixedHeight(self.height() // 8)
        backup_btn.setObjectName("backup_button")  #
        layout.addWidget(backup_btn, 0, 1)

        # Botón Restaurar Backup
        restore_btn = QPushButton("Cargar Backup")
        restore_btn.clicked.connect(self.do_restore)
        restore_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        restore_btn.setFixedHeight(self.height() // 8)
        restore_btn.setObjectName("restore_button")  # 
        layout.addWidget(restore_btn, 1, 1)

        self.setLayout(layout)

        # Aplicar estilos
        self.apply_styles()

    def apply_styles(self):
        """Aplica estilos QSS a los widgets."""
        style = """
        QPushButton {
            padding: 10px;
            border: 2px solid #ccc;
            border-radius: 5px;
            color: white;
            font-size: 14px;
        }
        QPushButton#backup_button {
            background-color: #28a745; /* Verde */
            border-color: #28a745;
        }
        QPushButton#backup_button:hover {
            background-color: #218838; /* Hover Verde */
        }
        QPushButton#backup_button:pressed {
            background-color: #1e7e34; /* Pressed Verde */
        }

        QPushButton#restore_button {
            background-color: #FF0000; /* Rojo */
            border-color: #FF0000;
        }
        QPushButton#restore_button:hover {
            background-color: #8B0000; /* Hover rojo */
        }
        QPushButton#restore_button:pressed {
            background-color: #300101; /* Pressed rojo */
        }
        QDialogButtonBox QPushButton {
        background-color: #007bff; /* Color Azul para OK */
        color: white;
        padding: 10px;
        border-radius: 5px;
        }
        QDialogButtonBox QPushButton:hover {
            background-color: #0056b3; /* Hover Azul */
        }
        QDialogButtonBox QPushButton:pressed {
            background-color: #004085; /* Pressed Azul */
        }
        """
        self.setStyleSheet(style)

    def do_backup(self):
        backup_path, _ = QFileDialog.getSaveFileName(self, "Guardar Backup", "", "Database Files (*.db)")
        if backup_path:
            if realizar_backup(backup_path):
                QMessageBox.information(self, "Éxito", "Backup realizado correctamente")
            else:
                QMessageBox.warning(self, "Error", "No se pudo realizar el backup")

    def do_restore(self):
        backup_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Backup", "", "Database Files (*.db)")
        if backup_path:
            if restaurar_backup(backup_path):
                QMessageBox.information(self, "Éxito", "Backup restaurado correctamente")
            else:
                QMessageBox.warning(self, "Error", "No se pudo restaurar el backup")


