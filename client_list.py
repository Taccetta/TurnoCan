from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QCalendarWidget, QCheckBox, QMessageBox, QComboBox, QSlider, 
                             QTimeEdit, QListWidget, QDialog, QDialogButtonBox, QTextEdit,
                             QScrollArea, QFrame, QListWidgetItem, QInputDialog, QGridLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QTime, QDate, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QTextCharFormat, QColor
from sqlalchemy import or_, desc
from database import Session, Client, Appointment, Breed
import datetime
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
import string, random
import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    logger = logging.getLogger('client_list')
    logger.setLevel(logging.INFO)
    
    # Configurar el RotatingFileHandler
    file_handler = RotatingFileHandler(
        'client_operations.log',
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=1
    )
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logger()


class ClientListWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar clientes...")
        self.search_button = QPushButton("Buscar")
        self.search_button.clicked.connect(self.search_clients)
        self.search_input.textChanged.connect(self.on_search_text_changed)

        # Layout for search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button) 
        layout.addLayout(search_layout)

        # Checkbox para alternar entre Stretch e Interactive
        self.stretch_checkbox = QCheckBox("Ajustar columnas automáticamente")
        self.stretch_checkbox.setChecked(True)
        self.stretch_checkbox.stateChanged.connect(self.toggle_stretch_mode)
        layout.addWidget(self.stretch_checkbox)

        # Client table
        self.client_table = QTableWidget()
        self.client_table.setColumnCount(7)
        self.client_table.setHorizontalHeaderLabels(["Apellido", "Nombre", "Dirección", "Teléfono", "Perro", "Raza", "Comentarios"])
        self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.client_table.setAlternatingRowColors(True)
        self.client_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f2f2f2;
                gridline-color: #d3d3d3;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 4px;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #a0a0a0;
                color: white;
            }
            QHeaderView::section:selected {
                background-color: #388E3C;
            }
        """)
        self.client_table.horizontalHeader().sectionClicked.connect(self.sort_table)
        self.client_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.client_table.doubleClicked.connect(self.edit_client)
        layout.addWidget(self.client_table)

        # Pagination controls
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Anterior")
        self.prev_button.clicked.connect(self.previous_page)
        self.next_button = QPushButton("Siguiente")
        self.next_button.clicked.connect(self.next_page)
        self.page_label = QLabel("Página 1 de 1")
        self.items_per_page_combo = QComboBox()
        self.items_per_page_combo.addItems(["15", "20", "50", "100", "1000"])
        self.items_per_page_combo.currentTextChanged.connect(self.change_items_per_page)
        
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(QLabel("Items por página:"))
        pagination_layout.addWidget(self.items_per_page_combo)
        layout.addLayout(pagination_layout)

        # Client count label
        self.client_count_label = QLabel()
        self.client_count_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.client_count_label)

        # Pagination variables
        self.current_page = 1
        self.items_per_page = 15
        self.total_pages = 1
        self.total_clients = 0
        self.current_search = ""
        self.current_sort_column = 0
        self.current_sort_order = Qt.AscendingOrder

        # Timer para retrasar la búsqueda
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.search_clients)

        # Uncomment for testing
        # self.test_button = QPushButton("Test")
        # self.test_button.clicked.connect(self.create_random_clients)
        # layout.addWidget(self.test_button)

        # Load clients when initialized
        self.load_clients()

        # Apply styles
        self.apply_styles()

        logger.info("ClientListWidget inicializado")

    def on_search_text_changed(self):
        self.search_timer.stop()
        self.search_timer.start(300)

    def search_clients(self):
        self.current_search = self.search_input.text()
        self.current_page = 1
        self.load_clients(self.current_search)

    def apply_styles(self):
        """Apply QSS styles to widgets."""
        style = """
        QLineEdit, QComboBox {
            padding: 8px;
            border: 1px solid #ced4da;
            border-radius: 5px;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            padding: 8px 12px;
            border: none;
            border-radius: 5px;
            margin: 2px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #388E3C;
        }
        QListWidget {
            border: 1px solid #ced4da;
            border-radius: 5px;
            padding: 5px;
            background-color: white;
        }
        """
        self.setStyleSheet(style)

    def load_clients(self, search_term=None):
        self.client_table.setRowCount(0)
        session = Session()
        query = session.query(Client)
        
        if search_term:
            query = query.filter(
                or_(
                    Client.lastname.ilike(f"%{search_term}%"),
                    Client.name.ilike(f"%{search_term}%"),
                    Client.address.ilike(f"%{search_term}%"),
                    Client.phone.ilike(f"%{search_term}%"),
                    Client.dog_name.ilike(f"%{search_term}%"),
                    Client.breed.ilike(f"%{search_term}%"),
                    Client.comments.ilike(f"%{search_term}%")
                )
            )
        
        self.total_clients = query.count()
        self.total_pages = (self.total_clients + self.items_per_page - 1) // self.items_per_page
        
        # Aplicar ordenamiento
        if self.current_sort_order == Qt.AscendingOrder:
            query = query.order_by(getattr(Client, self.get_column_name(self.current_sort_column)))
        else:
            query = query.order_by(desc(getattr(Client, self.get_column_name(self.current_sort_column))))
        
        clients = query.offset((self.current_page - 1) * self.items_per_page)\
                       .limit(self.items_per_page)\
                       .all()
        
        self.client_table.setRowCount(len(clients))
        for row, client in enumerate(clients):
            self.client_table.setItem(row, 0, QTableWidgetItem(client.lastname))
            self.client_table.setItem(row, 1, QTableWidgetItem(client.name))
            self.client_table.setItem(row, 2, QTableWidgetItem(client.address))
            self.client_table.setItem(row, 3, QTableWidgetItem(client.phone))
            self.client_table.setItem(row, 4, QTableWidgetItem(client.dog_name))
            self.client_table.setItem(row, 5, QTableWidgetItem(client.breed))
            self.client_table.setItem(row, 6, QTableWidgetItem(client.comments))
            for col in range(7):
                self.client_table.item(row, col).setData(Qt.UserRole, client.id)
        
        session.close()
        self.update_pagination_controls()
        self.update_client_count()
        self.update_sort_indicator()  # Añadir esta línea

        logger.info(f"Cargando clientes. Búsqueda: '{search_term}', Página: {self.current_page}, Items por página: {self.items_per_page}")

    def get_column_name(self, column_index):
        column_names = ['lastname', 'name', 'address', 'phone', 'dog_name', 'breed', 'comments']
        return column_names[column_index]

    def sort_table(self, column):
        if column == self.current_sort_column:
            # Cambiar el orden si se hace clic en la misma columna
            self.current_sort_order = Qt.DescendingOrder if self.current_sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self.current_sort_column = column
            self.current_sort_order = Qt.AscendingOrder
        
        self.load_clients(self.current_search)
        self.update_sort_indicator()

    def update_sort_indicator(self):
        header = self.client_table.horizontalHeader()
        for i in range(self.client_table.columnCount()):
            item = self.client_table.horizontalHeaderItem(i)
            text = item.text().split()[0]  # Obtener el texto base sin flechas
            if i == self.current_sort_column:
                if self.current_sort_order == Qt.AscendingOrder:
                    item.setText(f"{text} ▲")
                else:
                    item.setText(f"{text} ▼")
            else:
                item.setText(text)

    def update_pagination_controls(self):
        self.page_label.setText(f"Página {self.current_page} de {self.total_pages}")
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < self.total_pages)

    def update_client_count(self):
        start = (self.current_page - 1) * self.items_per_page + 1
        end = min(self.current_page * self.items_per_page, self.total_clients)
        self.client_count_label.setText(f"Mostrando {start}-{end} de {self.total_clients} clientes")

    def previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_clients(self.current_search)

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_clients(self.current_search)

    def change_items_per_page(self, value):
        self.items_per_page = int(value)
        self.current_page = 1
        self.load_clients(self.current_search)

    def edit_client(self, item):
        client_id = item.data(Qt.UserRole)
        logger.info(f"Editando cliente con ID: {client_id}")
        dialog = ClientEditDialog(client_id)
        dialog.clientDeleted.connect(self.remove_client_from_table)  # Conectar la señal a un nuevo método
        if dialog.exec_() == QDialog.Accepted:
            self.update_client_row(dialog.client)

    def remove_client_from_table(self, client_id):
        for row in range(self.client_table.rowCount()):
            if self.client_table.item(row, 0).data(Qt.UserRole) == client_id:
                self.client_table.removeRow(row)
                break
        self.total_clients -= 1
        self.update_pagination_controls()
        self.update_client_count()
        logger.info(f"Cliente con ID {client_id} eliminado de la tabla")

    def update_client_row(self, client):
        for row in range(self.client_table.rowCount()):
            if self.client_table.item(row, 0).data(Qt.UserRole) == client.id:
                self.client_table.setItem(row, 0, QTableWidgetItem(client.lastname))
                self.client_table.setItem(row, 1, QTableWidgetItem(client.name))
                self.client_table.setItem(row, 2, QTableWidgetItem(client.address))
                self.client_table.setItem(row, 3, QTableWidgetItem(client.phone))
                self.client_table.setItem(row, 4, QTableWidgetItem(client.dog_name))
                self.client_table.setItem(row, 5, QTableWidgetItem(client.breed))
                self.client_table.setItem(row, 6, QTableWidgetItem(client.comments))
                for col in range(7):
                    self.client_table.item(row, col).setData(Qt.UserRole, client.id)
                break
        logger.info(f"Fila actualizada para el cliente con ID: {client.id}")

    def create_random_clients(self):
        logger.info("Creando 100 clientes aleatorios")
        session = Session()
        for _ in range(100):
            lastname = self.get_random_string(8)
            name = self.get_random_string(8)
            address = self.get_random_string(15)
            phone = self.get_random_phone()
            dog_name = self.get_random_string(8)
            breed = self.get_random_breed()
            comments = self.get_random_string(20)

            new_client = Client(
                lastname=lastname,
                name=name,
                address=address,
                phone=phone,
                dog_name=dog_name,
                breed=breed,
                comments=comments
            )
            session.add(new_client)
        session.commit()
        session.close()
        self.load_clients()
        logger.info("100 clientes aleatorios creados exitosamente")

    def get_random_string(self, length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(length))

    def get_random_phone(self):
        return f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

    def get_random_breed(self):
        breeds = ["Labrador", "Golden Retriever", "Pastor Alemán", "Bulldog", "Poodle", "Beagle", "Chihuahua", "Boxer", "Dachshund", "Husky Siberiano", "Yorkshire Terrier", "Rottweiler", "Doberman", "Gran Danés", "Schnauzer", "Shih Tzu", "Pomerania", "Cocker Spaniel", "Bulldog Francés", "Caniche", "Mastín", "Bóxer", "Galgo", "Collie", "Basset Hound", "Pug", "Chow Chow", "Bichón Frisé", "Akita Inu", "Setter Irlandés", "Dálmata", "Terranova", "Shar Pei", "Weimaraner", "Bullmastiff", "Pointer", "Samoyedo", "Alaskan Malamute", "Bloodhound", "Cane Corso", "Bernés de la Montaña", "Cavalier King Charles Spaniel", "Corgi", "Whippet", "Bull Terrier", "Papillón", "Pinscher Miniatura", "Vizsla", "Airedale Terrier"]
        return random.choice(breeds)

    def toggle_stretch_mode(self, state):
        if state == Qt.Checked:
            self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        else:
            self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)


class ClientEditDialog(QDialog):
    clientDeleted = pyqtSignal(int)  # Nueva señal para indicar que un cliente fue eliminado

    def __init__(self, client_id):
        super().__init__()
        self.client_id = client_id
        self.setWindowTitle("Editar Cliente")
        self.setMinimumWidth(600)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Cargar datos del cliente
        self.session = Session()
        self.client = self.session.query(Client).get(client_id)

        # Crear un grid layout para los campos de entrada
        grid_layout = QGridLayout()
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)

        # Campos de entrada con datos del cliente
        self.lastname_input = QLineEdit(self.client.lastname)
        self.name_input = QLineEdit(self.client.name)
        self.address_input = QLineEdit(self.client.address)
        self.phone_input = QLineEdit(self.client.phone)
        self.dog_name_input = QLineEdit(self.client.dog_name)

        # Combo box para la raza
        self.breed_combo = QComboBox()
        self.load_breeds()
        self.breed_combo.setCurrentText(self.client.breed)

        # Campo para raza personalizada
        self.custom_breed_input = QLineEdit()
        self.custom_breed_input.setPlaceholderText("Ingrese una raza personalizada")
        self.custom_breed_input.setVisible(False)

        # Sección de comentarios
        self.comments_input = QTextEdit(self.client.comments)

        # Añadir etiquetas y campos al grid layout
        grid_layout.addWidget(QLabel("Apellido:"), 0, 0)
        grid_layout.addWidget(self.lastname_input, 1, 0)
        grid_layout.addWidget(QLabel("Nombre:"), 0, 1)
        grid_layout.addWidget(self.name_input, 1, 1)

        grid_layout.addWidget(QLabel("Dirección:"), 2, 0, 1, 2)
        grid_layout.addWidget(self.address_input, 3, 0, 1, 2)
        grid_layout.addWidget(QLabel("Teléfono:"), 4, 0, 1, 2)
        grid_layout.addWidget(self.phone_input, 5, 0, 1, 2)

        grid_layout.addWidget(QLabel("Nombre del perro:"), 6, 0)
        grid_layout.addWidget(self.dog_name_input, 7, 0)
        grid_layout.addWidget(QLabel("Raza:"), 6, 1)
        grid_layout.addWidget(self.breed_combo, 7, 1)

        grid_layout.addWidget(self.custom_breed_input, 8, 0, 1, 2)

        grid_layout.addWidget(QLabel("Comentarios:"), 9, 0, 1, 2)
        grid_layout.addWidget(self.comments_input, 10, 0, 1, 2)

        main_layout.addLayout(grid_layout)

        # Botones OK/Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        # Aplicar nombres de objeto a los botones en el button box
        button_box.button(QDialogButtonBox.Ok).setObjectName("ok-button")
        button_box.button(QDialogButtonBox.Cancel).setObjectName("cancel-button")

        # Botón Eliminar
        delete_button = QPushButton("Eliminar Cliente")
        delete_button.clicked.connect(self.delete_client)
        delete_button.setObjectName("delete-button")
        main_layout.addWidget(delete_button)

        # Conectar la señal de cambio en el combo box
        self.breed_combo.currentTextChanged.connect(self.on_breed_changed)

        # Aplicar estilos
        self.apply_styles(button_box)

        logger.info(f"Abriendo diálogo de edición para el cliente con ID: {client_id}")

    def apply_styles(self, button_box):
        """Apply QSS styles to the widgets."""
        style = """
        QLineEdit, QTextEdit, QComboBox {
            padding: 8px;
            border: 1px solid #ced4da;
            border-radius: 5px;
            background-color: #ffffff;
        }
        QLabel {
            font-weight: bold;
            margin-bottom: 5px;
        }
        QPushButton {
            padding: 8px;
            border: 2px solid #ccc;
            border-radius: 5px;
            min-width: 100px;
        }
        QPushButton#ok-button {
            background-color: #28a745; /* Green for OK */
            color: white;
            border: 2px solid #28a745;
        }
        QPushButton#ok-button:hover {
            background-color: #218838;
        }
        QPushButton#ok-button:pressed {
            background-color: #1e7e34;
        }
        QPushButton#cancel-button {
            background-color: #ffc107; /* Yellow for Cancel */
            color: white;
            border: 2px solid #ffc107;
        }
        QPushButton#cancel-button:hover {
            background-color: #e0a800;
        }
        QPushButton#cancel-button:pressed {
            background-color: #d39e00;
        }
        QPushButton#delete-button {
            background-color: #dc3545; /* Red for Delete */
            color: white;
            border: 2px solid #dc3545;
            margin-top: 10px;
        }
        QPushButton#delete-button:hover {
            background-color: #c82333;
        }
        QPushButton#delete-button:pressed {
            background-color: #bd2130;
        }
        QDialog {
            background-color: #f5f5f5;
        }
        """
        self.setStyleSheet(style)

    def load_breeds(self):
        breeds = self.session.query(Breed).order_by(Breed.name).all()
        self.breed_combo.addItem("Seleccione una raza")
        self.breed_combo.addItem("Otro")
        for breed in breeds:
            self.breed_combo.addItem(breed.name)

    def on_breed_changed(self, text):
        self.custom_breed_input.setVisible(text == "Otro")

    def accept(self):
        try:
            # Verificar que los campos obligatorios no estén vacíos
            if not self.lastname_input.text().strip():
                raise ValueError("El apellido no puede estar vacío.")
            if not self.name_input.text().strip():
                raise ValueError("El nombre no puede estar vacío.")
            if not self.address_input.text().strip():
                raise ValueError("La dirección no puede estar vacía.")
            if not self.phone_input.text().strip():
                raise ValueError("El teléfono no puede estar vacío.")
            if not self.dog_name_input.text().strip():
                raise ValueError("El nombre del perro no puede estar vacío.")
            
            breed = self.breed_combo.currentText()
            if breed == "Seleccione una raza":
                raise ValueError("Por favor, seleccione una raza.")
            elif breed == "Otro":
                breed = self.custom_breed_input.text().strip()
                if not breed:
                    raise ValueError("Por favor, ingrese una raza válida.")
                breed = breed.capitalize()
                existing_breed = self.session.query(Breed).filter(Breed.name.ilike(breed)).first()
                if existing_breed:
                    QMessageBox.warning(self, "Advertencia", f"La raza '{breed}' ya existe en el listado")
                else:
                    new_breed = Breed(name=breed)
                    self.session.add(new_breed)
                    self.session.commit()
                    self.breed_combo.addItem(breed)

            # Actualizar los datos del cliente
            self.client.lastname = self.lastname_input.text().strip().capitalize()
            self.client.name = self.name_input.text().strip().capitalize()
            self.client.address = (t := self.address_input.text().strip())[0].upper() + t[1:]
            self.client.phone = self.phone_input.text().strip()
            self.client.dog_name = self.dog_name_input.text().strip().capitalize()

            self.client.breed = breed
            self.client.comments = self.comments_input.toPlainText()
            self.session.commit()
            logger.info(f"Cliente con ID {self.client_id} actualizado exitosamente")
            super().accept()
        except ValueError as e:
            logger.error(f"Error al actualizar cliente con ID {self.client_id}: {str(e)}")
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            logger.error(f"Error inesperado al actualizar cliente con ID {self.client_id}: {str(e)}")
            QMessageBox.critical(self, "Error", f"Ocurrió un error al guardar los cambios: {str(e)}")

    def delete_client(self):
        confirm = QMessageBox.question(self, "Confirmar Eliminación", 
                                       "¿Está seguro de que desea eliminar este cliente? Se eliminarán todos sus turnos futuros.",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                logger.info(f"Eliminando cliente con ID: {self.client_id}")
                future_appointments = self.session.query(Appointment).filter(
                    Appointment.client_id == self.client_id,
                    Appointment.date >= datetime.date.today()
                ).all()
                for appointment in future_appointments:
                    self.session.delete(appointment)
                
                self.session.delete(self.client)
                self.session.commit()
                logger.info(f"Cliente con ID {self.client_id} y sus turnos futuros eliminados exitosamente")
                self.clientDeleted.emit(self.client_id)  # Emitir señal con el ID del cliente eliminado
                super().accept()
            except Exception as e:
                logger.error(f"Error al eliminar cliente con ID {self.client_id}: {str(e)}")
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el cliente: {str(e)}")
            finally:
                self.session.close()

    def closeEvent(self, event):
        self.session.close()
        super().closeEvent(event)