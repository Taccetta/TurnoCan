import os
import shutil
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QSizePolicy, QGridLayout
from database import db_path


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
        backup_btn = QPushButton("Realizar Backup")
        backup_btn.clicked.connect(self.do_backup)
        backup_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        backup_btn.setFixedHeight(self.height() // 8)
        backup_btn.setObjectName("backup_button")  #
        layout.addWidget(backup_btn, 0, 1)

        # Botón Restaurar Backup
        restore_btn = QPushButton("Restaurar Backup")
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
            background-color: #007bff; /* Azul */
            border-color: #007bff;
        }
        QPushButton#restore_button:hover {
            background-color: #0056b3; /* Hover Azul */
        }
        QPushButton#restore_button:pressed {
            background-color: #004085; /* Pressed Azul */
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


