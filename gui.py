from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QCalendarWidget, QCheckBox, QMessageBox, QComboBox, QSlider, 
                             QTimeEdit, QListWidget, QDialog, QDialogButtonBox, QTextEdit,
                             QScrollArea, QFrame, QListWidgetItem, QInputDialog, QGridLayout)
from PyQt5.QtCore import Qt, QTime, QDate
from PyQt5.QtGui import QIcon, QTextCharFormat, QColor
from database import Session, Client, Appointment, Breed
import datetime
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
import string, random


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

        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)

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
        self.load_breeds()

        self.custom_breed_input = QLineEdit()
        self.custom_breed_input.setVisible(False)

        # Comments section
        self.comments_input = QTextEdit()

        # Adding labels and fields to the form layout
        form_layout.addWidget(QLabel("Apellido:"))
        form_layout.addWidget(self.lastname_input)
        form_layout.addWidget(QLabel("Nombre:"))
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(QLabel("Dirección:"))
        form_layout.addWidget(self.address_input)
        form_layout.addWidget(QLabel("Teléfono:"))
        form_layout.addWidget(self.phone_input)
        form_layout.addWidget(QLabel("Nombre del perro:"))
        form_layout.addWidget(self.dog_name_input)
        form_layout.addWidget(QLabel("Raza:"))
        form_layout.addWidget(self.breed_combo)
        form_layout.addWidget(self.custom_breed_input)
        form_layout.addWidget(QLabel("Comentarios:"))
        form_layout.addWidget(self.comments_input)

        # Create client button with style
        create_client_btn = QPushButton("Crear Cliente")
        create_client_btn.clicked.connect(self.create_client)
        form_layout.addWidget(create_client_btn)

        scroll_layout.addLayout(form_layout)

        # Connecting signals
        self.breed_combo.currentTextChanged.connect(self.on_breed_changed)

        # Apply QSS styles
        self.apply_styles(create_client_btn)

    def apply_styles(self, button):
        """Apply QSS styles to widgets."""
        button_style = """
        QPushButton {
            background-color: #28a745;
            color: white;
            padding: 10px;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #218838;
        }
        QPushButton:pressed {
            background-color: #1e7e34;
        }
        QLineEdit {
            padding: 8px;
            border: 1px solid #ced4da;
            border-radius: 5px;
        }
        QTextEdit {
            padding: 8px;
            border: 1px solid #ced4da;
            border-radius: 5px;
        }
        QComboBox {
            padding: 8px;
            border: 1px solid #ced4da;
            border-radius: 5px;
            background-color: white;
        }
        QScrollArea {
            border: none;
        }
        QLabel {
            font-weight: bold;
        }
        """

        self.setStyleSheet(button_style)

    def load_breeds(self):
        session = Session()
        breeds = session.query(Breed).order_by(Breed.name).all()
        for breed in breeds:
            self.breed_combo.addItem(breed.name)
        session.close()

    def on_breed_changed(self, text):
        self.custom_breed_input.setVisible(text == "Otro")

    def create_client(self):
        session = Session()
        breed = self.breed_combo.currentText()
        if breed == "Otro":
            breed = self.custom_breed_input.text().strip()
            if not breed:
                QMessageBox.warning(self, "Error", "Por favor, ingrese una raza")
                return
            breed = breed.capitalize()
            existing_breed = session.query(Breed).filter(Breed.name.ilike(breed)).first()
            if existing_breed:
                QMessageBox.warning(self, "Advertencia", f"La raza '{breed}' ya existe en el listado")
            else:
                new_breed = Breed(name=breed)
                session.add(new_breed)
                session.commit()
                self.breed_combo.clear()
                self.breed_combo.addItem("Seleccione una raza")
                self.breed_combo.addItem("Otro")
                self.load_breeds()
                self.breed_combo.setCurrentText(breed)
        elif breed == "Seleccione una raza":
            QMessageBox.warning(self, "Error", "Por favor, seleccione una raza")
            return
        
        new_client = Client(
            lastname=self.lastname_input.text().capitalize(),
            name=self.name_input.text().capitalize(),
            address=self.address_input.text(),
            phone=self.phone_input.text(),
            dog_name=self.dog_name_input.text().capitalize(),
            breed=breed,
            comments=self.comments_input.toPlainText()
        )
        session.add(new_client)
        session.commit()
        session.close()
        QMessageBox.information(self, "Éxito", "Cliente creado correctamente")
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

class ClientListWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Search input and button
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar clientes...")
        self.search_button = QPushButton("Buscar")
        self.search_button.clicked.connect(self.search_clients)
        self.search_input.returnPressed.connect(self.search_clients)

        # Layout for search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # Client list
        self.client_list = QListWidget()
        self.client_list.itemDoubleClicked.connect(self.edit_client)
        layout.addWidget(self.client_list)

        # Uncomment for testing
        # self.test_button = QPushButton("Test")
        # self.test_button.clicked.connect(self.create_random_clients)
        # layout.addWidget(self.test_button)


        # Client count label
        self.client_count_label = QLabel()
        self.client_count_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.client_count_label)

        # Client list
        self.client_list.itemDoubleClicked.connect(self.edit_client)
        layout.addWidget(self.client_list)

        # Load clients when initialized
        self.load_clients()

        # Apply styles
        self.apply_styles()

    def apply_styles(self):
        """Apply QSS styles to widgets."""
        style = """
        QLineEdit {
            padding: 8px;
            border: 1px solid #ced4da;
            border-radius: 5px;
        }
        QPushButton {
            background-color: #007bff;
            color: white;
            padding: 8px 12px;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:pressed {
            background-color: #004085;
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
        self.client_list.clear()
        session = Session()
        query = session.query(Client)
        if search_term:
            query = query.filter(
                (Client.lastname.contains(search_term)) |
                (Client.name.contains(search_term)) |
                (Client.address.contains(search_term)) |
                (Client.phone.contains(search_term)) |
                (Client.dog_name.contains(search_term)) |
                (Client.breed.contains(search_term)) |
                (Client.comments.contains(search_term))
            )
        clients = query.order_by(Client.lastname.asc(), Client.name.asc()).all()
        for client in clients:
            item = QListWidgetItem(
                f"{client.lastname} {client.name} - {client.dog_name} ({client.breed}) - "
                f"Dirección: {client.address} - "
                f"Teléfono: {client.phone}")
            item.setData(Qt.UserRole, client.id)
            self.client_list.addItem(item)
        session.close()
        self.update_client_count(len(self.client_list))

    def update_client_count(self, count):
        self.client_count_label.setText(f"Mostrando {count} clientes")

    def search_clients(self):
        search_term = self.search_input.text()
        self.load_clients(search_term)

    def edit_client(self, item):
        client_id = item.data(Qt.UserRole)
        dialog = ClientEditDialog(client_id)
        if dialog.exec_():
            self.load_clients()

    def create_random_clients(self):
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

    def get_random_string(self, length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(length))

    def get_random_phone(self):
        return f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

    def get_random_breed(self):
        breeds = ["Labrador", "Golden Retriever", "Pastor Alemán", "Bulldog", "Poodle", "Beagle", "Chihuahua", "Boxer", "Dachshund", "Husky Siberiano", "Yorkshire Terrier", "Rottweiler", "Doberman", "Gran Danés", "Schnauzer", "Shih Tzu", "Pomerania", "Cocker Spaniel", "Bulldog Francés", "Caniche", "Mastín", "Bóxer", "Galgo", "Collie", "Basset Hound", "Pug", "Chow Chow", "Bichón Frisé", "Akita Inu", "Setter Irlandés", "Dálmata", "Terranova", "Shar Pei", "Weimaraner", "Bullmastiff", "Pointer", "Samoyedo", "Alaskan Malamute", "Bloodhound", "Cane Corso", "Bernés de la Montaña", "Cavalier King Charles Spaniel", "Corgi", "Whippet", "Bull Terrier", "Papillón", "Pinscher Miniatura", "Vizsla", "Airedale Terrier"]
        return random.choice(breeds)

class ClientEditDialog(QDialog):
    def __init__(self, client_id):
        super().__init__()
        self.client_id = client_id
        self.setWindowTitle("Editar Cliente")
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Load client data
        session = Session()
        self.client = session.query(Client).get(client_id)

        # Input fields with client data
        self.lastname_input = QLineEdit(self.client.lastname)
        self.name_input = QLineEdit(self.client.name)
        self.address_input = QLineEdit(self.client.address)
        self.phone_input = QLineEdit(self.client.phone)
        self.dog_name_input = QLineEdit(self.client.dog_name)

        # Breed combo box
        self.breed_combo = QComboBox()
        self.load_breeds()
        self.breed_combo.setCurrentText(self.client.breed)

        # Comments section
        self.comments_input = QTextEdit(self.client.comments)

        # Adding labels and fields to layout
        layout.addWidget(QLabel("Apellido:"))
        layout.addWidget(self.lastname_input)
        layout.addWidget(QLabel("Nombre:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Dirección:"))
        layout.addWidget(self.address_input)
        layout.addWidget(QLabel("Teléfono:"))
        layout.addWidget(self.phone_input)
        layout.addWidget(QLabel("Nombre del perro:"))
        layout.addWidget(self.dog_name_input)
        layout.addWidget(QLabel("Raza:"))
        layout.addWidget(self.breed_combo)
        layout.addWidget(QLabel("Comentarios:"))
        layout.addWidget(self.comments_input)

        # OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Apply object names to buttons in the button box
        button_box.button(QDialogButtonBox.Ok).setObjectName("ok-button")
        button_box.button(QDialogButtonBox.Cancel).setObjectName("cancel-button")

        # Delete button
        delete_button = QPushButton("Eliminar Cliente")
        delete_button.clicked.connect(self.delete_client)
        delete_button.setObjectName("delete-button")  # Asigna el nombre de objeto aquí
        layout.addWidget(delete_button)

        session.close()

        # Apply styles
        self.apply_styles(button_box)

    def apply_styles(self, button_box):
        """Apply QSS styles to the widgets."""
        style = """
        QLineEdit, QTextEdit {
            padding: 8px;
            border: 1px solid #ced4da;
            border-radius: 5px;
        }
        QComboBox {
            padding: 8px;
            border: 1px solid #ced4da;
            border-radius: 5px;
            background-color: white;
        }
        QLabel {
            font-weight: bold;
            margin-bottom: 5px;
        }
        QPushButton {
            padding: 8px;
            border: 2px solid #ccc;
            border-radius: 5px;
        }
        QPushButton#ok-button {
            background-color: #28a745; /* Green for OK */
            color: white;
            border: 2px solid #28a745;
        }
        QPushButton#cancel-button {
            background-color: #ffc107; /* Yellow for Cancel */
            color: white;
            border: 2px solid #ffc107;
        }
        QPushButton#delete-button {
            background-color: #dc3545; /* Red for Delete */
            color: white;
            border: 2px solid #dc3545;
        }
        """
        self.setStyleSheet(style)

    def load_breeds(self):
        session = Session()
        breeds = session.query(Breed).order_by(Breed.name).all()
        self.breed_combo.addItem("Seleccione una raza")
        self.breed_combo.addItem("Otro")
        for breed in breeds:
            self.breed_combo.addItem(breed.name)
        session.close()

    def accept(self):
        session = Session()
        client = session.query(Client).get(self.client_id)
        client.lastname = self.lastname_input.text().capitalize()
        client.name = self.name_input.text().capitalize()
        client.address = self.address_input.text()
        client.phone = self.phone_input.text()
        client.dog_name = self.dog_name_input.text().capitalize()
        
        breed = self.breed_combo.currentText()
        if breed == "Otro":
            breed = QInputDialog.getText(self, "Nueva Raza", "Ingrese el nombre de la nueva raza:")[0].strip()
            if not breed:
                QMessageBox.warning(self, "Error", "Por favor, ingrese una raza")
                return
            breed = breed.capitalize()
            existing_breed = session.query(Breed).filter(Breed.name.ilike(breed)).first()
            if existing_breed:
                QMessageBox.warning(self, "Advertencia", f"La raza '{breed}' ya existe en el listado")
            else:
                new_breed = Breed(name=breed)
                session.add(new_breed)
                session.commit()
                self.breed_combo.addItem(breed)
        elif breed == "Seleccione una raza":
            QMessageBox.warning(self, "Error", "Por favor, seleccione una raza")
            return
        
        client.breed = breed
        client.comments = self.comments_input.toPlainText()
        session.commit()
        session.close()
        super().accept()

    def delete_client(self):
        confirm = QMessageBox.question(self, "Confirmar Eliminación", 
                                       "¿Está seguro de que desea eliminar este cliente? Se eliminarán todos sus turnos futuros.",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            session = Session()
            client = session.query(Client).get(self.client_id)
            
            if client:
                future_appointments = session.query(Appointment).filter(
                    Appointment.client_id == self.client_id,
                    Appointment.date >= datetime.date.today()
                ).all()
                for appointment in future_appointments:
                    session.delete(appointment)
                
                session.delete(client)
                session.commit()
                session.close()
                super().accept()
            else:
                QMessageBox.warning(self, "Error", "No se pudo encontrar el cliente para eliminar.")
                session.close()

class AppointmentCalendarWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout()
        self.setLayout(layout)

        # Calendar widget
        self.calendar = QCalendarWidget()
        layout.addWidget(self.calendar, 0, 0)

        # Appointment list (hidden by default)
        self.appointment_list = QListWidget()
        self.appointment_list.setVisible(False)
        layout.addWidget(self.appointment_list, 0, 1)

        # Buttons layout
        buttons_layout = QHBoxLayout()

        create_appointment_btn = QPushButton("Crear Turno")
        create_appointment_btn.clicked.connect(self.create_appointment)
        buttons_layout.addWidget(create_appointment_btn)

        self.toggle_list_btn = QPushButton("⮘ Mostrar Lista")
        self.toggle_list_btn.clicked.connect(self.toggle_appointment_list)
        buttons_layout.addWidget(self.toggle_list_btn)

        repeat_weekly_btn = QPushButton("Repetir Turnos Semanalmente")
        repeat_weekly_btn.clicked.connect(self.repeat_weekly_appointments)
        buttons_layout.addWidget(repeat_weekly_btn)

        print_btn = QPushButton("Imprimir")
        print_btn.clicked.connect(self.print_appointments)
        buttons_layout.addWidget(print_btn)

        layout.addLayout(buttons_layout, 1, 0, 1, 2)

        # Connect calendar signals
        self.calendar.selectionChanged.connect(self.load_appointments)
        self.calendar.currentPageChanged.connect(self.update_calendar)

        # Load calendar data
        self.update_calendar()

        # Apply styles
        self.apply_styles()

    def apply_styles(self):
        """Apply QSS styles to the widgets."""
        style = """
        QCalendarWidget {
            border: 1px solid #ced4da;
            border-radius: 5px;
            background-color: #f8f9fa;
        }
        QListWidget {
            border: 1px solid #ced4da;
            border-radius: 5px;
            padding: 5px;
        }
        QPushButton {
            padding: 2px;
            border: 2px solid #ccc;
            border-radius: 5px;
            background-color: #007bff;
            color: white;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:pressed {
            background-color: #004085;
        }
        QPushButton#create_appointment_btn {
            background-color: #28a745; /* Green */
            border-color: #28a745;
        }
        QPushButton#create_appointment_btn:hover {
            background-color: #218838;
        }
        QPushButton#create_appointment_btn:pressed {
            background-color: #1e7e34;
        }
        QPushButton#toggle_list_btn {
            background-color: #ffc107; /* Yellow */
            border-color: #ffc107;
        }
        QPushButton#toggle_list_btn:hover {
            background-color: #e0a800;
        }
        QPushButton#toggle_list_btn:pressed {
            background-color: #d39e00;
        }
        QPushButton#repeat_weekly_btn {
            background-color: #17a2b8; /* Teal */
            border-color: #17a2b8;
        }
        QPushButton#repeat_weekly_btn:hover {
            background-color: #138496;
        }
        QPushButton#repeat_weekly_btn:pressed {
            background-color: #117a8b;
        }
        QPushButton#print_btn {
            background-color: #6c757d; /* Gray */
            border-color: #6c757d;
        }
        QPushButton#print_btn:hover {
            background-color: #5a6268;
        }
        QPushButton#print_btn:pressed {
            background-color: #545b62;
        }

        /* boton Borrar */
        QPushButton#delete_button {
            background-color: #dc3545; /* Rojo */
            border-color: #dc3545;
        }
        QPushButton#delete_button:hover {
            background-color: #c82333;
        }
        QPushButton#delete_button:pressed {
            background-color: #bd2130;
        }
        """
        self.setStyleSheet(style)


    def load_appointments(self):
        self.appointment_list.clear()
        selected_date = self.calendar.selectedDate().toPyDate()
        session = Session()
        appointments = session.query(Appointment).filter(Appointment.date == selected_date).all()
        for appointment in appointments:
            item = QListWidgetItem(f"{appointment.time.strftime('%H:%M')} - {appointment.client.lastname} {appointment.client.name}")
            item.setData(Qt.UserRole, appointment.id)
            
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            
            info_layout = QVBoxLayout()
            label = QLabel(f"{appointment.client.lastname} {appointment.client.name}  - "
                           f"Perro: {appointment.client.dog_name} - "
                           f"Raza: {appointment.client.breed}\n"
                           f"Dirección: {appointment.client.address}\n"
                           f"Teléfono: {appointment.client.phone} - "
                           f"Hora: {appointment.time.strftime('%H:%M')} - "
                           f"Fecha: {appointment.date.strftime('%d-%m-%Y')}\n"
                           f"Comentarios: {appointment.client.comments}")
            info_layout.addWidget(label)
            
            buttons_layout = QVBoxLayout()
            edit_button = QPushButton("Editar")
            edit_button.clicked.connect(lambda _, a=appointment.id: self.edit_appointment(a))
            buttons_layout.addWidget(edit_button)
            
            delete_button = QPushButton("Borrar")
            delete_button.setObjectName("delete_button") 
            delete_button.clicked.connect(lambda _, a=appointment.id: self.delete_appointment(a))
            buttons_layout.addWidget(delete_button)
            
            item_layout.addLayout(info_layout)
            item_layout.addLayout(buttons_layout)
            
            list_item = QListWidgetItem(self.appointment_list)
            list_item.setSizeHint(item_widget.sizeHint())
            self.appointment_list.addItem(list_item)
            self.appointment_list.setItemWidget(list_item, item_widget)
        
        session.close()

    def update_calendar(self):
        current_date = self.calendar.selectedDate()
        year = current_date.year()
        month = current_date.month()
        
        if year == 0 or month == 0:
            current_date = QDate.currentDate()
            year = current_date.year()
            month = current_date.month()
            self.calendar.setSelectedDate(current_date)

        start_date = QDate(year, month, 1)
        end_date = QDate(year, month, start_date.daysInMonth())

        session = Session()
        appointments = session.query(Appointment).filter(
            Appointment.date.between(start_date.toPyDate(), end_date.toPyDate())
        ).all()
        
        for day in range(1, 32):
            date = QDate(year, month, day)
            if date.isValid():
                self.calendar.setDateTextFormat(date, QTextCharFormat())
        
        for appointment in appointments:
            date = QDate(appointment.date.year, appointment.date.month, appointment.date.day)
            fmt = self.calendar.dateTextFormat(date)
            fmt.setBackground(QColor(255, 200, 200))
            self.calendar.setDateTextFormat(date, fmt)
        
        session.close()

    def create_appointment(self):
        dialog = AppointmentDialog(self.calendar.selectedDate().toPyDate())
        if dialog.exec_():
            self.load_appointments()
            self.update_calendar()

    def edit_appointment(self, appointment_id):
        dialog = AppointmentDialog(self.calendar.selectedDate().toPyDate(), appointment_id)
        if dialog.exec_():
            self.load_appointments()
            self.update_calendar()

    def delete_appointment(self, appointment_id):
        confirm = QMessageBox.question(self, "Confirmar Eliminación", 
                                       "¿Está seguro de que desea eliminar este turno?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            session = Session()
            appointment = session.query(Appointment).get(appointment_id)
            session.delete(appointment)
            session.commit()
            session.close()
            self.load_appointments()
            self.update_calendar()

    def toggle_appointment_list(self):
        self.appointment_list.setVisible(not self.appointment_list.isVisible())
        if self.appointment_list.isVisible():
            self.toggle_list_btn.setText("⮚ Ocultar Lista")
        else:
            self.toggle_list_btn.setText("⮘ Mostrar Lista")
    
    def print_appointments(self):
        dialog = PrintAppointmentsDialog(self.calendar.selectedDate().toPyDate())
        dialog.exec_()

    def repeat_weekly_appointments(self):
        current_date = self.calendar.selectedDate()
        next_week = current_date.addDays(7)
        session = Session()
        appointments_to_repeat = session.query(Appointment).filter(
            Appointment.date == current_date.toPyDate(),
            Appointment.repeat_weekly == True
        ).all()

        for appointment in appointments_to_repeat:
            existing_appointment = session.query(Appointment).filter(
                Appointment.date == next_week.toPyDate(),
                Appointment.time == appointment.time,
                Appointment.client_id == appointment.client_id
            ).first()

            if not existing_appointment:
                new_appointment = Appointment(
                    date=next_week.toPyDate(),
                    time=appointment.time,
                    client_id=appointment.client_id,
                    repeat_weekly=appointment.repeat_weekly,
                    repeat_monthly=appointment.repeat_monthly
                )
                session.add(new_appointment)

        session.commit()
        session.close()
        self.load_appointments()
        self.update_calendar()
 
class PrintAppointmentsDialog(QDialog):
    def __init__(self, date):
        super().__init__()
        self.date = date
        self.setWindowTitle("Imprimir Turnos")
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Imprimir")
        button_box.accepted.connect(self.print)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.load_appointments()

    def load_appointments(self):
        session = Session()
        appointments = session.query(Appointment).filter(Appointment.date == self.date).all()
        text = ""
        for appointment in appointments:
            text += f"{appointment.time.strftime('%H:%M')} - {appointment.client.lastname} {appointment.client.name} - "
            text += f"Perro: {appointment.client.dog_name} - Raza: {appointment.client.breed} - "
            text += f"Dirección: {appointment.client.address} - Teléfono: {appointment.client.phone}\n"
            text += f"Comentarios: {appointment.client.comments}\n"
        self.preview.setText(text)
        session.close()

    def print(self):
        printer = QPrinter()
        dialog = QPrintDialog()
        if dialog.exec_() == QDialog.Accepted:
            self.preview.print_(printer)

class AppointmentDialog(QDialog):
    def __init__(self, date, appointment_id=None):
        super().__init__()
        self.date = date
        self.appointment_id = appointment_id
        self.setWindowTitle("Crear Turno" if appointment_id is None else "Editar Turno")
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Search for client
        self.client_search = QLineEdit()
        layout.addWidget(QLabel("Cliente:"))
        self.client_search.setPlaceholderText("Buscar cliente...")
        self.client_search.textChanged.connect(self.filter_clients)
        layout.addWidget(self.client_search)

        # Client combo box
        self.client_combo = QComboBox()
        self.load_clients()
        layout.addWidget(self.client_combo)
        
        # Time edit
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(9, 0))
        layout.addWidget(QLabel("Hora:"))
        layout.addWidget(self.time_edit)

        # Repeat combo box
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["No repetir", "Repetir semanalmente"])
        layout.addWidget(QLabel("Repetición:"))
        layout.addWidget(self.repeat_combo)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Delete button (if editing an appointment)
        if appointment_id:
            self.load_appointment(appointment_id)
            delete_button = QPushButton("Eliminar Turno")
            delete_button.setObjectName("delete_button")  # Establecer un nombre de objeto para el botón
            delete_button.clicked.connect(self.delete_appointment)
            layout.addWidget(delete_button)

        # Apply styles
        self.apply_styles()

    def apply_styles(self):
        """Apply QSS styles to the widgets."""
        style = """
        QLabel {
            font-weight: bold;
            margin-bottom: 5px;
        }
        QLineEdit, QComboBox, QTimeEdit {
            padding: 10px;
            border: 1px solid #ced4da;
            border-radius: 5px;
            background-color: #f8f9fa;
            font-size: 14px;
        }
        QLineEdit:focus, QComboBox:focus, QTimeEdit:focus {
            border: 1px solid #007bff;
        }
        QPushButton {
            padding: 10px;
            border: 2px solid #ccc;
            border-radius: 5px;
            background-color: #007bff;
            color: white;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:pressed {
            background-color: #004085;
        }

        /* Estilo específico para el botón Eliminar */
        QPushButton#delete_button {
            background-color: #dc3545; /* Rojo */
            border-color: #dc3545;
        }
        QPushButton#delete_button:hover {
            background-color: #c82333;
        }
        QPushButton#delete_button:pressed {
            background-color: #bd2130;
        }
        """
        self.setStyleSheet(style)

    def load_clients(self):
        self.client_combo.clear()
        session = Session()
        clients = session.query(Client).all()
        for client in clients:
            self.client_combo.addItem(f"{client.lastname} {client.name}", client.id)
        session.close()

    def update_client_combo(self):
        self.client_combo.clear()
        for client in self.clients:
            self.client_combo.addItem(client.name, client.id)

    def filter_clients(self):
        search_term = self.client_search.text().lower()
        self.client_combo.clear()
        session = Session()
        clients = session.query(Client).filter(
            (Client.name.ilike(f"%{search_term}%")) |
            (Client.lastname.ilike(f"%{search_term}%"))
        ).all()
        for client in clients:
            self.client_combo.addItem(f"{client.lastname} {client.name}", client.id)
        session.close()

    def load_appointment(self, appointment_id):
        session = Session()
        appointment = session.query(Appointment).get(appointment_id)
        self.time_edit.setTime(appointment.time)
        index = self.client_combo.findData(appointment.client_id)
        if index >= 0:
            self.client_combo.setCurrentIndex(index)
        if appointment.repeat_weekly:
            self.repeat_combo.setCurrentIndex(1)
        elif appointment.repeat_monthly:
            self.repeat_combo.setCurrentIndex(2)
        session.close()

    def accept(self):
        session = Session()
        client_id = self.client_combo.currentData()
        time = self.time_edit.time().toPyTime()
        repeat = self.repeat_combo.currentText()

        if self.appointment_id:
            appointment = session.query(Appointment).get(self.appointment_id)
            appointment.date = self.date
            appointment.time = time
            appointment.client_id = client_id
            appointment.repeat_weekly = (repeat == "Repetir semanalmente")
            appointment.repeat_monthly = (repeat == "Repetir mensualmente")
        else:
            new_appointment = Appointment(
                date=self.date,
                time=time,
                client_id=client_id,
                repeat_weekly=(repeat == "Repetir semanalmente"),
                repeat_monthly=(repeat == "Repetir mensualmente")
            )
            session.add(new_appointment)

        session.commit()
        session.close()
        super().accept()


    def delete_appointment(self):
        confirm = QMessageBox.question(self, "Confirmar Eliminación", 
                                       "¿Está seguro de que desea eliminar este turno?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            session = Session()
            appointment = session.query(Appointment).get(self.appointment_id)
            session.delete(appointment)
            session.commit()
            session.close()
            self.accept()