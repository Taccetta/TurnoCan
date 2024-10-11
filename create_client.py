import logging
from logging.handlers import RotatingFileHandler
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QScrollArea, QFormLayout, QTextEdit, QMessageBox, QComboBox, 
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from database import Session, Client, Breed

def setup_logger():
    logger = logging.getLogger('create_client')
    logger.setLevel(logging.INFO)
    
    # Configurar el RotatingFileHandler
    file_handler = RotatingFileHandler(
        'create_client_operations.log',
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=1
    )
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logger()

class CreateClientWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        scroll_area = QScrollArea()
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Input fields
        self.lastname_input = QLineEdit()
        self.name_input = QLineEdit()
        self.address_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.dog_name_input = QLineEdit()

        # Combo box for breed selection
        self.breed_combo = QComboBox()
        self.breed_combo.addItem("Seleccione una raza")
        self.breed_combo.addItem("Otro")

        self.custom_breed_input = QLineEdit()
        self.custom_breed_input.setPlaceholderText("Ingrese la raza personalizada")
        self.custom_breed_input.setVisible(False)

        # Comments section
        self.comments_input = QTextEdit()
        self.comments_input.setPlaceholderText("Comentarios adicionales...")

        # Adding labels and fields to the form layout
        form_layout.addRow(QLabel("Apellido:*"), self.lastname_input)
        form_layout.addRow(QLabel("Nombre:*"), self.name_input)
        form_layout.addRow(QLabel("Dirección:*"), self.address_input)
        form_layout.addRow(QLabel("Teléfono:*"), self.phone_input)
        form_layout.addRow(QLabel("Nombre del perro:*"), self.dog_name_input)
        form_layout.addRow(QLabel("Raza:*"), self.breed_combo)
        form_layout.addRow(QLabel("Raza personalizada:"), self.custom_breed_input)
        form_layout.addRow(QLabel("Comentarios:"), self.comments_input)

        # Create client button with style
        create_client_btn = QPushButton("Crear Cliente")
        create_client_btn.setFixedHeight(40)
        create_client_btn.clicked.connect(self.create_client)
        form_layout.addRow(create_client_btn)

        scroll_layout.addLayout(form_layout)

        # Connecting signals
        self.breed_combo.currentTextChanged.connect(self.on_breed_changed)
        
        # Añadimos esta línea para cargar las razas cuando se muestra el widget
        self.breed_combo.showPopup = self.load_breeds_and_show_popup

        # Apply QSS styles
        self.apply_styles(create_client_btn)

        logger.info("CreateClientWidget inicializado")

    def apply_styles(self, button):
        """Apply QSS styles to widgets."""
        style = """
        QWidget {
            background-color: #f5f5f5;
        }
        QLabel {
            font-weight: bold;
            color: #333333;
            font-size: 14px;
        }
        QLineEdit, QTextEdit, QComboBox {
            padding: 10px;
            border: 1px solid #ced4da;
            border-radius: 8px;
            font-size: 14px;
            background-color: #ffffff;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border: 1px solid #80bdff;
            outline: none;
        }
        QPushButton {
            background-color: #45a049;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:pressed {
            background-color: #004085;
        }
        QScrollArea {
            border: none;
        }
        """

        self.setStyleSheet(style)

        # Añadir sombra al botón de crear cliente
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        button.setGraphicsEffect(shadow)

        logger.info("Estilos aplicados a CreateClientWidget")

    def load_breeds(self):
        session = Session()
        breeds = session.query(Breed).order_by(Breed.name).all()
        
        # Guardamos el texto actual
        current_text = self.breed_combo.currentText()
        
        # Limpiamos y recargamos el combo box
        self.breed_combo.clear()
        self.breed_combo.addItem("Seleccione una raza")
        self.breed_combo.addItem("Otro")
        
        for breed in breeds:
            self.breed_combo.addItem(breed.name)
        
        # Restauramos el texto seleccionado si aún existe, o seleccionamos el primero
        index = self.breed_combo.findText(current_text)
        if index >= 0:
            self.breed_combo.setCurrentIndex(index)
        else:
            self.breed_combo.setCurrentIndex(0)
        
        session.close()
        logger.info(f"Razas cargadas: {len(breeds)} razas encontradas")

    def load_breeds_and_show_popup(self):
        self.load_breeds()
        QComboBox.showPopup(self.breed_combo)

    def on_breed_changed(self, text):
        self.custom_breed_input.setVisible(text == "Otro")
        logger.info(f"Raza seleccionada: {text}")

    def create_client(self):
        # Verificar campos obligatorios
        required_fields = [
            (self.lastname_input.text().strip(), "Apellido"),
            (self.name_input.text().strip(), "Nombre"),
            (self.address_input.text().strip(), "Dirección"),
            (self.phone_input.text().strip(), "Teléfono"),
            (self.dog_name_input.text().strip(), "Nombre del perro")
        ]

        missing_fields = [field[1] for field in required_fields if not field[0]]

        if missing_fields:
            logger.warning(f"Intento de crear cliente con campos faltantes: {', '.join(missing_fields)}")
            QMessageBox.warning(
                self, 
                "Error", 
                f"Por favor, complete los siguientes campos obligatorios: {', '.join(missing_fields)}"
            )
            return

        session = Session()
        breed = self.breed_combo.currentText()
        if breed == "Otro":
            breed = self.custom_breed_input.text().strip()
            if not breed:
                logger.warning("Intento de crear cliente con raza personalizada vacía")
                QMessageBox.warning(self, "Error", "Por favor, ingrese una raza personalizada.")
                session.close()
                return
            breed = breed.capitalize()
            existing_breed = session.query(Breed).filter(Breed.name.ilike(breed)).first()
            if existing_breed:
                logger.info(f"Raza personalizada '{breed}' ya existe en el listado")
                QMessageBox.warning(
                    self, 
                    "Advertencia", 
                    f"La raza '{breed}' ya existe en el listado."
                )
            else:
                new_breed = Breed(name=breed)
                session.add(new_breed)
                session.commit()
                logger.info(f"Nueva raza '{breed}' añadida al listado")
                self.breed_combo.clear()
                self.breed_combo.addItem("Seleccione una raza")
                self.breed_combo.addItem("Otro")
                self.load_breeds()
                self.breed_combo.setCurrentText(breed)
        elif breed == "Seleccione una raza":
            logger.warning("Intento de crear cliente sin seleccionar una raza")
            QMessageBox.warning(self, "Error", "Por favor, seleccione una raza.")
            session.close()
            return

        new_client = Client(
            lastname=self.lastname_input.text().capitalize(),
            name=self.name_input.text().capitalize(),
            address= (t := self.address_input.text().strip())[0].upper() + t[1:],
            phone=self.phone_input.text(),
            dog_name=self.dog_name_input.text().capitalize(),
            breed=breed,
            comments=self.comments_input.toPlainText()
        )
        session.add(new_client)
        session.commit()
        logger.info(f"Nuevo cliente creado: {new_client.lastname} {new_client.name}")
        session.close()
        QMessageBox.information(self, "Éxito", "Cliente creado correctamente.")
        self.clear_fields()

    def clear_fields(self):
        self.lastname_input.clear()
        self.name_input.clear()
        self.address_input.clear()
        self.phone_input.clear()
        self.dog_name_input.clear()
        self.breed_combo.setCurrentIndex(0)
        self.custom_breed_input.clear()
        self.comments_input.clear()
        logger.info("Campos del formulario de creación de cliente limpiados")