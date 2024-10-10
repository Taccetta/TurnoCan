import datetime
import random
import string

from PyQt5 import QtWidgets, QtCore, QtGui, QtPrintSupport
from sqlalchemy import extract
from database import Session, Client, Appointment, Breed

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QCalendarWidget,
    QCheckBox, QComboBox, QSlider, QTimeEdit, QListWidget, QDialog, QDialogButtonBox,
    QTextEdit, QScrollArea, QFrame, QListWidgetItem, QInputDialog, QGridLayout, QMessageBox,
    QSplitter, QSplitterHandle
)
from PyQt5.QtCore import Qt, QTime, QDate, QPoint, QSize
from PyQt5.QtGui import QIcon, QTextCharFormat, QColor, QFont, QDoubleValidator, QPainter, QPen
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog


class CustomSplitterHandle(QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.setFixedWidth(10)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor(150, 150, 150))
        
        # Dibujar tres líneas verticales
        pen = QPen(QColor(150, 150, 150), 1, Qt.SolidLine)
        painter.setPen(pen)
        center_x = self.width() // 2
        for i in range(-1, 2):
            painter.drawLine(center_x + i*2, self.height() // 2 - 10, center_x + i*2, self.height() // 2 + 10)

    def sizeHint(self):
        return QSize(10, super().sizeHint().height())


class AppointmentCalendarWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Crear QSplitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(10)
        self.splitter.setChildrenCollapsible(False)
        layout.addWidget(self.splitter)

        # Calendario
        self.calendar_widget = QWidget()
        calendar_layout = QVBoxLayout(self.calendar_widget)
        self.calendar = QCalendarWidget()
        calendar_layout.addWidget(self.calendar)
        self.splitter.addWidget(self.calendar_widget)

        # Lista de turnos
        appointment_widget = QWidget()
        appointment_layout = QVBoxLayout(appointment_widget)
        self.appointment_count_layout = QHBoxLayout()
        self.appointment_count_label = QLabel("Cantidad Turnos:")
        self.appointment_count_number = QLabel("0")
        self.appointment_count_layout.addWidget(self.appointment_count_label)
        self.appointment_count_layout.addWidget(self.appointment_count_number)
        self.appointment_count_layout.addStretch()
        appointment_layout.addLayout(self.appointment_count_layout)
        self.appointment_list = QListWidget()
        appointment_layout.addWidget(self.appointment_list)
        self.splitter.addWidget(appointment_widget)

        # Configurar el splitter
        self.splitter.setStyleSheet("""
            QSplitterHandle {
                background-color: #f0f0f0;
            }
            QSplitterHandle:hover {
                background-color: #e0e0e0;
            }
        """)

        # Guardar las posiciones iniciales del divisor
        self.initial_sizes = [300, 500]  # Ajusta estos valores según tus preferencias
        self.splitter.setSizes(self.initial_sizes)
        self.last_visible_sizes = self.initial_sizes.copy()

        # Buttons layout
        buttons_layout = QHBoxLayout()

        create_appointment_btn = QPushButton("Crear Turno")
        create_appointment_btn.clicked.connect(self.create_appointment)
        create_appointment_btn.setStyleSheet("""
            QPushButton {
                background-color: #45a049;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3e8e41;
            }
            QPushButton:pressed {
                background-color: #367c39;
            }
        """)
        buttons_layout.addWidget(create_appointment_btn)

        self.toggle_calendar_btn = QPushButton("Ocultar Calendario")
        self.toggle_calendar_btn.clicked.connect(self.toggle_calendar)
        self.toggle_calendar_btn.setStyleSheet("""
            QPushButton {
                background-color: #45a049;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3e8e41;
            }
            QPushButton:pressed {
                background-color: #367c39;
            }
        """)
        buttons_layout.addWidget(self.toggle_calendar_btn)

        repeat_weekly_btn = QPushButton("Repetir Turnos Semanalmente")
        repeat_weekly_btn.clicked.connect(self.repeat_weekly_appointments)
        repeat_weekly_btn.setStyleSheet("""
            QPushButton {
                background-color: #45a049;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3e8e41;
            }
            QPushButton:pressed {
                background-color: #367c39;
            }
        """)
        buttons_layout.addWidget(repeat_weekly_btn)

        print_btn = QPushButton("Imprimir")
        print_btn.clicked.connect(self.print_appointments)
        print_btn.setStyleSheet("""
            QPushButton {
                background-color: #45a049;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3e8e41;
            }
            QPushButton:pressed {
                background-color: #367c39;
            }
        """)
        buttons_layout.addWidget(print_btn)

        layout.addLayout(buttons_layout)

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
            border-radius: 10px;
            background-color: #ffffff;
            font-size: 14px;
        }
        QCalendarWidget QAbstractItemView::selected {
            background-color: #45a049;
            color: white;
        }
        QListWidget {
            border: 1px solid #ced4da;
            border-radius: 10px;
            padding: 10px;
            background-color: #ffffff;
            font-size: 14px;
        }
        QListWidget::item:nth-child(even) {
            background-color: #f9f9f9;
        }
        QListWidget::item:nth-child(odd) {
            background-color: #e9ecef;
        }
        QCheckBox {
            spacing: 5px;
            font-size: 14px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #ced4da;
            border-radius: 3px;
            background-color: white;
        }
        QCheckBox::indicator:checked {
            background-color: #45a049;
            border-color: #45a049;
            image: url(checkmark.png);
        }
        QPushButton {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            background-color: #45a049;
            color: white;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #3e8e41;
        }
        QPushButton:pressed {
            background-color: #367c39;
        }
        QPushButton#create_appointment_btn {
            background-color: #45a049; /* Green */
        }
        QPushButton#toggle_list_btn {
            background-color: #45a049; /* Green */
        }
        QPushButton#repeat_weekly_btn {
            background-color: #45a049; /* Green */
        }
        QPushButton#print_btn {
            background-color: #45a049; /* Green */
        }

        /* Botón Borrar */
        QPushButton#delete_button {
            background-color: #dc3545; /* Rojo */
            border-color: #dc3545;
            color: white;
            border-radius: 5px;
        }
        QPushButton#delete_button:hover {
            background-color: #c82333;
        }
        QPushButton#delete_button:pressed {
            background-color: #bd2130;
        }

        /* Contador de turnos */
        QLabel#appointment_count_label {
            font-weight: bold;
            font-size: 16px;
        }
        QLabel#appointment_count_number {
            font-weight: bold;
            font-size: 16px;
            color: #45a049;
        }

        /* Botones de editar */
        QPushButton#edit_button {
            background-color: #ffc107; /* Amarillo */
            border: none;
            color: white;
            border-radius: 5px;
            font-size: 12px;
        }
        QPushButton#edit_button:hover {
            background-color: #e0a800;
        }
        QPushButton#edit_button:pressed {
            background-color: #d39e00;
        }
        """
        self.setStyleSheet(style)

        # Poner el contador de turnos en negrita
        bold_font = QFont()
        bold_font.setBold(True)
        self.appointment_count_label.setFont(bold_font)
        self.appointment_count_number.setFont(bold_font)
        self.appointment_count_label.setStyleSheet("font-size: 16px;")
        self.appointment_count_number.setStyleSheet("font-size: 16px; color: #45a049;")


    def toggle_calendar(self):
        if self.calendar_widget.isVisible():
            self.last_visible_sizes = self.splitter.sizes()
            self.calendar_widget.hide()
            self.splitter.setSizes([0, sum(self.last_visible_sizes)])
            self.toggle_calendar_btn.setText("Mostrar Calendario")
        else:
            self.calendar_widget.show()
            self.splitter.setSizes(self.last_visible_sizes)
            self.toggle_calendar_btn.setText("Ocultar Calendario")

    def load_appointments(self):
        self.appointment_list.clear()
        selected_date = self.calendar.selectedDate().toPyDate()
        session = Session()
        appointments = session.query(Appointment).filter(Appointment.date == selected_date).order_by(Appointment.time).all()
        
        # Actualizar el contador de turnos
        self.appointment_count_number.setText(str(len(appointments)))
        
        for index, appointment in enumerate(appointments, start=1):
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            
            # Contenido principal del turno
            content_layout = QVBoxLayout()
            
            # Número de orden, hora, fecha, cliente y mascota en una línea
            time_date_client_info = QLabel(f"<b>{index}- {appointment.time.strftime('%H:%M')} - {appointment.date.strftime('%d/%m/%Y')}</b> - "
                                           f"<b>{appointment.client.lastname} {appointment.client.name}</b> - "
                                           f"Perro: <i>{appointment.client.dog_name}</i> ({appointment.client.breed})")
            time_date_client_info.setStyleSheet("font-size: 14px; color: #333;")
            content_layout.addWidget(time_date_client_info)
            
            # Dirección y teléfono en una línea
            contact_info = QLabel(f"Dirección: {appointment.client.address} - Tel: {appointment.client.phone}")
            contact_info.setStyleSheet("font-size: 13px; color: #555;")
            content_layout.addWidget(contact_info)
            
            # Comentarios del cliente (si existen)
            if appointment.client.comments:
                client_comments = QLabel(f"Comentarios del cliente: {appointment.client.comments.replace('\n', ' ')}")
                client_comments.setStyleSheet("font-size: 13px; font-style: italic; color: #666;")
                client_comments.setWordWrap(True)
                content_layout.addWidget(client_comments)
            
            # Servicio, precio y notas en una línea
            details = QLabel(f"Servicio: {appointment.status or 'No especificado'} - "
                             f"Precio: ${appointment.price or 'No especificado'} - "
                             f"Notas: {appointment.appoint_comment or 'Sin notas'}")
            details.setStyleSheet("font-size: 13px;")
            details.setWordWrap(True)
            content_layout.addWidget(details)
            
            # Botones y checkbox
            buttons_layout = QHBoxLayout()
            confirmed_checkbox = QCheckBox("Confirmado")
            confirmed_checkbox.setChecked(appointment.confirmed)
            confirmed_checkbox.stateChanged.connect(lambda state, a=appointment.id: self.toggle_confirmation(a, state))
            buttons_layout.addWidget(confirmed_checkbox)
            
            edit_button = QPushButton("Editar")
            edit_button.setFixedSize(80, 30)  # Aumentamos el ancho del botón
            edit_button.setObjectName("edit_button")
            edit_button.setStyleSheet("""
                QPushButton#edit_button {
                    background-color: #45a049;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 12px;
                }
                QPushButton#edit_button:hover {
                    background-color: #3e8e41;
                }
                QPushButton#edit_button:pressed {
                    background-color: #367c39;
                }
            """)
            edit_button.clicked.connect(lambda _, a=appointment.id: self.edit_appointment(a))
            buttons_layout.addWidget(edit_button)
            
            delete_button = QPushButton("Borrar")
            delete_button.setFixedSize(80, 30)  # Aumentamos el ancho del botón
            delete_button.setObjectName("delete_button") 
            delete_button.setStyleSheet("""
                QPushButton#delete_button {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 12px;
                }
                QPushButton#delete_button:hover {
                    background-color: #c82333;
                }
                QPushButton#delete_button:pressed {
                    background-color: #bd2130;
                }
            """)
            delete_button.clicked.connect(lambda _, a=appointment.id: self.delete_appointment(a))
            buttons_layout.addWidget(delete_button)
            
            buttons_layout.addStretch()  # Añadir espacio flexible al final
            content_layout.addLayout(buttons_layout)
            
            item_layout.addLayout(content_layout)
            
            list_item = QListWidgetItem(self.appointment_list)
            list_item.setSizeHint(item_widget.sizeHint())
            self.appointment_list.addItem(list_item)
            self.appointment_list.setItemWidget(list_item, item_widget)
        
        session.close()

    def adjust_time(self, appointment_id, minutes):
        session = Session()
        appointment = session.query(Appointment).get(appointment_id)
        new_time = (datetime.datetime.combine(datetime.date.today(), appointment.time) + 
                    datetime.timedelta(minutes=minutes)).time()
        appointment.time = new_time
        session.commit()
        session.close()
        self.load_appointments()
        self.update_calendar()

    def toggle_confirmation(self, appointment_id, state):
        session = Session()
        appointment = session.query(Appointment).get(appointment_id)
        appointment.confirmed = state == Qt.Checked
        session.commit()
        session.close()
        self.load_appointments()

    def update_calendar(self):
        current_date = self.calendar.selectedDate()
        year, month = current_date.year(), current_date.month()
        
        start_date = QDate(year, month, 1)
        days_in_month = start_date.daysInMonth()

        # Resetear formato de fechas
        for day in range(1, days_in_month + 1):
            date = QDate(year, month, day)
            self.calendar.setDateTextFormat(date, QTextCharFormat())

        # Obtener citas y establecer formato
        session = Session()
        try:
            appointments = session.query(Appointment).filter(
                extract('month', Appointment.date) == month,
                extract('year', Appointment.date) == year
            ).all()

            for appointment in appointments:
                date = QDate(appointment.date.year, appointment.date.month, appointment.date.day)
                fmt = self.calendar.dateTextFormat(date)
                fmt.setBackground(QColor(69, 160, 73))  # Verde suave
                fmt.setForeground(QColor(255, 255, 255))  # Texto blanco
                self.calendar.setDateTextFormat(date, fmt)

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error al actualizar el calendario: {str(e)}")
        finally:
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
 
    def createHandle(self):
        return CustomSplitterHandle(self.orientation(), self)


class PrintAppointmentsDialog(QDialog):
    def __init__(self, date):
        super().__init__()
        self.date = date
        self.setWindowTitle("Imprimir Turnos")
        self.setFixedSize(600, 400)
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
        appointments = session.query(Appointment).filter(Appointment.date == self.date).order_by(Appointment.time).all()
        text = ""
        for appointment in appointments:
            text += f"{appointment.time.strftime('%H:%M')} - {appointment.date.strftime('%d/%m/%Y')}  -  {appointment.client.lastname} {appointment.client.name}  -  "
            text += f"Perro: {appointment.client.dog_name}  -  Raza: {appointment.client.breed}  -  "
            text += f"Dirección: {appointment.client.address}  -  Teléfono: {appointment.client.phone}\n"
            if appointment.client.comments:
                text += f"Comentarios del cliente: {appointment.client.comments.replace('\n', ' ')}  -  "
            text += f"Servicio: {appointment.status or 'No especificado'}  -  "
            text += f"Precio: ${appointment.price or 'No especificado'}  -  "
            text += f"Notas: {appointment.appoint_comment or 'Sin notas'}\n"
            if appointment.confirmed:
                text += "CONFIRMADO\n"
            text += "\n"
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

        # Confirmed checkbox
        self.confirmed_checkbox = QCheckBox("Confirmado")
        layout.addWidget(self.confirmed_checkbox)

                # Service combo box (antes llamado Status)
        self.service_combo = QComboBox()
        self.service_combo.addItems(["Baño", "Corte", "Baño y corte"])
        layout.addWidget(QLabel("Servicio:"))
        layout.addWidget(self.service_combo)

        # Price input con validador
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Precio")
        validator = QDoubleValidator(0.00, 9999999.99, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.price_input.setValidator(validator)
        layout.addWidget(QLabel("Precio:"))
        layout.addWidget(self.price_input)



        # Client comments display
        self.client_comments = QTextEdit()
        self.client_comments.setReadOnly(True)
        self.client_comments.setPlaceholderText("Comentarios del cliente")
        self.client_comments.setStyleSheet("""
            QTextEdit {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 5px;
                color: #333333;
            }
        """)
        layout.addWidget(QLabel("Comentarios del cliente:"))
        layout.addWidget(self.client_comments)

        # Notes input
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas del turno")
        layout.addWidget(QLabel("Notas del turno:"))
        layout.addWidget(self.notes_input)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        if appointment_id:
            self.load_appointment(appointment_id)

        # Conectar el cambio de cliente seleccionado a la actualización de comentarios
        self.client_combo.currentIndexChanged.connect(self.update_client_comments)

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
            border: 1px solid #007bff;
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

    def update_client_comments(self):
        client_id = self.client_combo.currentData()
        if client_id:
            session = Session()
            client = session.query(Client).get(client_id)
            if client:
                self.client_comments.setText(client.comments)
            else:
                self.client_comments.clear()
            session.close()
        else:
            self.client_comments.clear()

    def filter_clients(self):
        search_term = self.client_search.text().lower()
        self.client_combo.clear()
        if len(search_term) >= 3:
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
        
        # Cargar el cliente del turno
        client = appointment.client
        self.client_search.setText(f"{client.lastname} {client.name}")
        self.client_combo.clear()
        self.client_combo.addItem(f"{client.lastname} {client.name}", client.id)
        
        if appointment.repeat_weekly:
            self.repeat_combo.setCurrentIndex(1)
        elif appointment.repeat_monthly:
            self.repeat_combo.setCurrentIndex(2)
        self.confirmed_checkbox.setChecked(appointment.confirmed)
        self.price_input.setText(str(appointment.price) if appointment.price else "")
        self.service_combo.setCurrentText(appointment.status if appointment.status else "Baño")
        self.notes_input.setText(appointment.appoint_comment if appointment.appoint_comment else "")
        self.update_client_comments()
        session.close()

    def accept(self):
        session = Session()
        client_id = self.client_combo.currentData()
        
        if not client_id:
            QMessageBox.warning(self, "Error", "Por favor, seleccione un cliente.")
            return

        time = self.time_edit.time().toPyTime()
        repeat = self.repeat_combo.currentText()
        confirmed = self.confirmed_checkbox.isChecked()
        
        # Manejo mejorado de la conversión del precio
        price_text = self.price_input.text().strip().replace(',', '.')
        price = None
        if price_text:
            try:
                price = float(price_text)
                if price < 0:
                    raise ValueError("El precio no puede ser negativo")
            except ValueError:
                QMessageBox.warning(self, "Error de entrada", 
                                    "Por favor, ingrese un número válido para el precio.")
                return
        
        service = self.service_combo.currentText()
        notes = self.notes_input.toPlainText()

        if self.appointment_id:
            appointment = session.query(Appointment).get(self.appointment_id)
            appointment.date = self.date
            appointment.time = time
            appointment.client_id = client_id
            appointment.repeat_weekly = (repeat == "Repetir semanalmente")
            appointment.repeat_monthly = (repeat == "Repetir mensualmente")
            appointment.confirmed = confirmed
            appointment.price = price
            appointment.status = service
            appointment.appoint_comment = notes
        else:
            new_appointment = Appointment(
                date=self.date,
                time=time,
                client_id=client_id,
                repeat_weekly=(repeat == "Repetir semanalmente"),
                repeat_monthly=(repeat == "Repetir mensualmente"),
                confirmed=confirmed,
                price=price,
                status=service,
                appoint_comment=notes
            )
            session.add(new_appointment)

        try:
            session.commit()
            session.close()
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el turno: {str(e)}")
            session.rollback()
            session.close()

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