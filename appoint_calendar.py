from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QCalendarWidget, QCheckBox, QMessageBox, QComboBox, QSlider, 
                             QTimeEdit, QListWidget, QDialog, QDialogButtonBox, QTextEdit,
                             QScrollArea, QFrame, QListWidgetItem, QInputDialog, QGridLayout)
from PyQt5.QtCore import Qt, QTime, QDate
from PyQt5.QtGui import QIcon, QTextCharFormat, QColor
from sqlalchemy import extract
from database import Session, Client, Appointment, Breed
import datetime
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
import string, random

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
        self.calendar.selectionChanged.connect(self.update_calendar)

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
        
        start_date = QDate(year, month, 1)
        end_date = QDate(year, month, start_date.daysInMonth())

        session = Session()
        appointments = session.query(Appointment).filter(
            extract('month', Appointment.date) == month,
            extract('year', Appointment.date) == year
        ).all()
        
        # Resetear formato de fechas
        for day in range(1, start_date.daysInMonth() + 1):
            date = QDate(year, month, day)
            self.calendar.setDateTextFormat(date, QTextCharFormat())
        
        # Establecer formato para fechas con citas
        for appointment in appointments:
            date = QDate(appointment.date.year, appointment.date.month, appointment.date.day)
            fmt = self.calendar.dateTextFormat(date)
            fmt.setBackground(QColor(255, 200, 200))
            self.calendar.setDateTextFormat(date, fmt)
        
        session.close()

    def create_appointment(self):
        session = Session()
        clients = session.query(Client).all()
        session.close()
        
        if not clients:
            QMessageBox.warning(self, "Error", "No existen clientes. Cree un cliente primero para guardar un turno.")
            return
        
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
        # if appointment_id:
        #     self.load_appointment(appointment_id)
        #     delete_button = QPushButton("Eliminar Turno")
        #     delete_button.setObjectName("delete_button")
        #     delete_button.clicked.connect(self.delete_appointment)
        #     layout.addWidget(delete_button)

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