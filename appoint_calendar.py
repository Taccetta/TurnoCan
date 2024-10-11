import logging
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
    QSplitter, QSplitterHandle, QDateEdit
)
from PyQt5.QtCore import Qt, QTime, QDate, QPoint, QSize
from PyQt5.QtGui import QIcon, QTextCharFormat, QColor, QFont, QDoubleValidator, QPainter, QPen
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from logging.handlers import RotatingFileHandler

def setup_logger():
    logger = logging.getLogger('appoint_calendar')
    logger.setLevel(logging.INFO)
    
    # Configurar el RotatingFileHandler
    file_handler = RotatingFileHandler(
        'appointment_operations.log',
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=1
    )
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logger()


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

        logger.info("AppointmentCalendarWidget inicializado")

    def apply_styles(self):
        """Apply QSS styles to the widgets."""
        style = """
        QLabel {
            font-weight: bold;
            font-size: 14px;
        }
        QLineEdit, QComboBox, QTimeEdit, QDateEdit {
            padding: 5px;
            border: 1px solid #3498db;
            border-radius: 3px;
            font-size: 14px;
        }
        QDateEdit, QTimeEdit {
            padding-right: 20px; /* Espacio para el botón de flecha */
        }
        QDateEdit::drop-down, QTimeEdit::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #3498db;
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
        }
        QTextEdit {
            border: 1px solid #3498db;
            border-radius: 3px;
            font-size: 14px;
        }
        QTextEdit[readOnly="true"] {
            background-color: #f0f0f0;
        }
        QCheckBox {
            font-size: 14px;
        }
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
        logger.info(f"Cargando turnos para la fecha: {selected_date}")
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
        logger.info(f"Se cargaron {len(appointments)} turnos para la fecha {selected_date}")

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
        logger.info(f"Cambiando estado de confirmación del turno ID {appointment_id} a {'confirmado' if state == Qt.Checked else 'no confirmado'}")
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

        logger.info(f"Actualizando calendario para el mes: {current_date.month()}/{current_date.year()}")

    def create_appointment(self):
        logger.info("Iniciando creación de nuevo turno")
        session = Session()
        clients = session.query(Client).all()
        session.close()
        
        if not clients:
            QMessageBox.warning(self, "Error", "No existen clientes. Cree un cliente primero para guardar un turno.")
            return
        
        dialog = AppointmentDialog(self.calendar.selectedDate().toPyDate())
        if dialog.exec_():
            logger.info("Nuevo turno creado exitosamente")
            self.load_appointments()
            self.update_calendar()
        else:
            logger.info("Creación de turno cancelada")

    def edit_appointment(self, appointment_id):
        logger.info(f"Editando turno con ID: {appointment_id}")
        dialog = AppointmentDialog(self.calendar.selectedDate().toPyDate(), appointment_id)
        if dialog.exec_():
            self.load_appointments()
            self.update_calendar()

    def delete_appointment(self, appointment_id):
        logger.info(f"Intentando eliminar turno con ID: {appointment_id}")
        confirm = QMessageBox.question(self, "Confirmar Eliminación", 
                                       "¿Está seguro de que desea eliminar este turno?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            session = Session()
            appointment = session.query(Appointment).get(appointment_id)
            session.delete(appointment)
            session.commit()
            session.close()
            logger.info(f"Turno con ID {appointment_id} eliminado exitosamente")
            self.load_appointments()
            self.update_calendar()

    def toggle_appointment_list(self):
        self.appointment_list.setVisible(not self.appointment_list.isVisible())
        if self.appointment_list.isVisible():
            self.toggle_list_btn.setText("⮚ Ocultar Lista")
        else:
            self.toggle_list_btn.setText("⮘ Mostrar Lista")
    
    def print_appointments(self):
        logger.info("Iniciando impresión de turnos")
        dialog = PrintAppointmentsDialog(self.calendar.selectedDate().toPyDate())
        dialog.exec_()

    def repeat_weekly_appointments(self):
        current_date = self.calendar.selectedDate()
        next_week = current_date.addDays(7)
        logger.info(f"Repitiendo turnos semanales del {current_date.toString('dd/MM/yyyy')} al {next_week.toString('dd/MM/yyyy')}")
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
        logger.info(f"Se repitieron {len(appointments_to_repeat)} turnos para la semana siguiente")
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

        logger.info(f"Abriendo diálogo de impresión para la fecha: {date}")

    def load_appointments(self):
        session = Session()
        appointments = session.query(Appointment).filter(Appointment.date == self.date).order_by(Appointment.time).all()
        text = f"Turnos para el {self.date.strftime('%d/%m/%Y')}\n\n"
        for appointment in appointments:
            text += f"{appointment.time.strftime('%H:%M')} - {appointment.client.lastname} {appointment.client.name} - "
            text += f"{appointment.client.dog_name} ({appointment.client.breed}) - "
            text += f"Dirección: {appointment.client.address} - Tel: {appointment.client.phone}\n"
            
            text += f"Servicio: {appointment.status or 'No esp.'} - Precio: ${appointment.price or 'No esp.'}"
            if appointment.confirmed:
                text += " - CONFIRMADO"
            text += "\n"
            
            comments = []
            if appointment.client.comments:
                comments.append(f"Comentarios: {appointment.client.comments.strip()}")
            if appointment.appoint_comment:
                comments.append(f"Notas: {appointment.appoint_comment.strip()}")
            if comments:
                text += " - ".join(comments) + "\n"
            
            text += "_" * 90 + "\n"
        self.preview.setText(text)
        session.close()

    def print(self):
        logger.info(f"Imprimiendo turnos para la fecha: {self.date}")
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
        self.setMinimumWidth(600)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Grid layout para los campos
        grid_layout = QGridLayout()
        layout.addLayout(grid_layout)

        # Cliente
        grid_layout.addWidget(QLabel("Cliente:"), 0, 0, 1, 2)
        client_layout = QHBoxLayout()
        self.client_search = QLineEdit()
        self.client_search.setPlaceholderText("Buscar cliente...")
        self.client_search.textChanged.connect(self.filter_clients)
        self.client_combo = QComboBox()
        client_layout.addWidget(self.client_search, 1)
        client_layout.addWidget(self.client_combo, 1)
        grid_layout.addLayout(client_layout, 1, 0, 1, 2)

        # Fecha y Hora
        grid_layout.addWidget(QLabel("Fecha:"), 2, 0)
        grid_layout.addWidget(QLabel("Hora:"), 2, 1)
        date_time_layout = QHBoxLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate(self.date))
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(9, 0))
        date_time_layout.addWidget(self.date_edit)
        date_time_layout.addWidget(self.time_edit)
        grid_layout.addLayout(date_time_layout, 3, 0, 1, 2)

        # Confirmado
        self.confirmed_checkbox = QCheckBox("Confirmado")
        grid_layout.addWidget(self.confirmed_checkbox, 4, 0, 1, 2)

        # Servicio y Precio
        grid_layout.addWidget(QLabel("Servicio:"), 5, 0)
        grid_layout.addWidget(QLabel("Precio:"), 5, 1)
        service_price_layout = QHBoxLayout()
        self.service_combo = QComboBox()
        self.service_combo.addItems(["Baño", "Corte", "Baño y corte"])
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Precio")
        validator = QDoubleValidator(0.00, 9999999.99, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.price_input.setValidator(validator)
        service_price_layout.addWidget(self.service_combo, 1)
        service_price_layout.addWidget(self.price_input, 1)
        grid_layout.addLayout(service_price_layout, 6, 0, 1, 2)

        # Comentarios del cliente
        grid_layout.addWidget(QLabel("Comentarios del cliente:"), 7, 0, 1, 2)
        self.client_comments = QTextEdit()
        self.client_comments.setReadOnly(True)
        self.client_comments.setPlaceholderText("Comentarios del cliente")
        self.client_comments.setMaximumHeight(100)
        self.client_comments.setStyleSheet("background-color: #f0f0f0;")  # Añadir esta línea
        grid_layout.addWidget(self.client_comments, 8, 0, 1, 2)

        # Notas del turno
        grid_layout.addWidget(QLabel("Notas del turno:"), 9, 0, 1, 2)
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas del turno")
        self.notes_input.setMaximumHeight(100)
        grid_layout.addWidget(self.notes_input, 10, 0, 1, 2)

        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Cambiar el texto y los colores de los botones
        ok_button = button_box.button(QDialogButtonBox.Ok)
        ok_button.setText("Guardar")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #45a049;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3e8e41;
            }
        """)

        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setText("Cancelar")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)

        if appointment_id:
            self.load_appointment(appointment_id)

        # Conectar el cambio de cliente seleccionado a la actualización de comentarios
        self.client_combo.currentIndexChanged.connect(self.update_client_comments)

        # Aplicar estilos generales
        self.apply_styles()

        logger.info(f"Abriendo diálogo de {'edición' if appointment_id else 'creación'} de turno para la fecha: {date}")

    def apply_styles(self):
        self.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
            }
            QLineEdit, QComboBox, QTimeEdit, QDateEdit {
                padding: 5px;
                border: 1px solid #3498db;
                border-radius: 3px;
                font-size: 14px;
            }
            QDateEdit, QTimeEdit {
                padding-right: 20px; /* Espacio para el botón de flecha */
            }
            QDateEdit::drop-down, QTimeEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #3498db;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QDateEdit::down-arrow, QTimeEdit::down-arrow {
                image: url(data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 20 20'%3E%3Cpath fill='%233498db' d='M5 8l5 5 5-5z'/%3E%3C/svg%3E);
                width: 20px;
                height: 20px;
            }
            QDateEdit::down-arrow:hover, QTimeEdit::down-arrow:hover {
                image: url(data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 20 20'%3E%3Cpath fill='%232980b9' d='M5 8l5 5 5-5z'/%3E%3C/svg%3E);
            }
            QTextEdit {
                border: 1px solid #3498db;
                border-radius: 3px;
                font-size: 14px;
            }
            QTextEdit[readOnly="true"] {
                background-color: #f0f0f0;
            }
            QCheckBox {
                font-size: 14px;
            }
        """)

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
        logger.info(f"Cargando datos del turno con ID: {appointment_id}")
        session = Session()
        appointment = session.query(Appointment).get(appointment_id)
        self.date_edit.setDate(appointment.date)
        self.time_edit.setTime(appointment.time)
        
        # Cargar el cliente del turno
        client = appointment.client
        self.client_search.setText(f"{client.lastname} {client.name}")
        self.client_combo.clear()
        self.client_combo.addItem(f"{client.lastname} {client.name}", client.id)
        
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

        date = self.date_edit.date().toPyDate()
        time = self.time_edit.time().toPyTime()
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
            appointment.date = date
            appointment.time = time
            appointment.client_id = client_id
            appointment.confirmed = confirmed
            appointment.price = price
            appointment.status = service
            appointment.appoint_comment = notes
        else:
            new_appointment = Appointment(
                date=date,
                time=time,
                client_id=client_id,
                confirmed=confirmed,
                price=price,
                status=service,
                appoint_comment=notes
            )
            session.add(new_appointment)

        try:
            session.commit()
            logger.info(f"Turno {'actualizado' if self.appointment_id else 'creado'} exitosamente")
            session.close()
            super().accept()
        except Exception as e:
            logger.error(f"Error al {'actualizar' if self.appointment_id else 'crear'} turno: {str(e)}")
            QMessageBox.critical(self, "Error", f"No se pudo guardar el turno: {str(e)}")
            session.rollback()
            session.close()