from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QListWidget, QDialog, QDialogButtonBox, QTextEdit, QComboBox,
                             QListWidgetItem, QGridLayout, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from database import Session, Appointment, Client
from sqlalchemy import or_
import datetime

class AppointmentSearchWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar turnos...")
        self.search_button = QPushButton("Buscar")
        self.search_button.clicked.connect(self.search_appointments)
        self.search_input.textChanged.connect(self.on_search_text_changed)

        # Layout for search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)  # Agregar esta línea
        layout.addLayout(search_layout)

        # Appointment list
        self.appointment_list = QListWidget()
        self.appointment_list.itemDoubleClicked.connect(self.view_appointment)
        layout.addWidget(self.appointment_list)

        # Pagination controls
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Anterior")
        self.prev_button.clicked.connect(self.previous_page)
        self.next_button = QPushButton("Siguiente")
        self.next_button.clicked.connect(self.next_page)
        self.page_label = QLabel("Página 1 de 1")
        self.items_per_page_combo = QComboBox()
        self.items_per_page_combo.addItems(["50", "100", "200", "1000"])
        self.items_per_page_combo.currentTextChanged.connect(self.change_items_per_page)
        
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addWidget(QLabel("Items por página:"))
        pagination_layout.addWidget(self.items_per_page_combo)
        layout.addLayout(pagination_layout)

        # Appointment count label
        self.appointment_count_label = QLabel()
        self.appointment_count_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.appointment_count_label)

        # Pagination variables
        self.current_page = 1
        self.items_per_page = 50
        self.total_pages = 1
        self.total_appointments = 0
        self.current_search = ""

        # Timer para retrasar la búsqueda
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.search_appointments)

        # Load appointments when initialized
        self.load_appointments()

        # Apply styles
        self.apply_styles()

    def on_search_text_changed(self):
        self.search_timer.stop()
        self.search_timer.start(300)

    def search_appointments(self):
        self.current_search = self.search_input.text()
        self.current_page = 1
        self.load_appointments(self.current_search)

    def apply_styles(self):
        style = """
        QLineEdit, QComboBox {
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

    def load_appointments(self, search_term=None):
        self.appointment_list.clear()
        session = Session()
        query = session.query(Appointment).join(Client)
        
        if search_term:
            query = query.filter(
                or_(
                    Client.lastname.ilike(f"%{search_term}%"),
                    Client.name.ilike(f"%{search_term}%"),
                    Client.dog_name.ilike(f"%{search_term}%"),
                    Appointment.status.ilike(f"%{search_term}%"),
                    Appointment.appoint_comment.ilike(f"%{search_term}%")
                )
            )
        
        self.total_appointments = query.count()
        self.total_pages = (self.total_appointments + self.items_per_page - 1) // self.items_per_page
        
        appointments = query.order_by(Appointment.date.desc(), Appointment.time.desc())\
                            .offset((self.current_page - 1) * self.items_per_page)\
                            .limit(self.items_per_page)\
                            .all()
        
        for appointment in appointments:
            item = QListWidgetItem(
                f"{appointment.date.strftime('%d/%m/%Y')} {appointment.time.strftime('%H:%M')} - "
                f"{appointment.client.lastname} {appointment.client.name} - "
                f"{appointment.client.dog_name} - {appointment.status}"
            )
            item.setData(Qt.UserRole, appointment.id)
            self.appointment_list.addItem(item)
        
        session.close()
        self.update_pagination_controls()
        self.update_appointment_count()

    def update_pagination_controls(self):
        self.page_label.setText(f"Página {self.current_page} de {self.total_pages}")
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < self.total_pages)

    def update_appointment_count(self):
        start = (self.current_page - 1) * self.items_per_page + 1
        end = min(self.current_page * self.items_per_page, self.total_appointments)
        self.appointment_count_label.setText(f"Mostrando {start}-{end} de {self.total_appointments} turnos")

    def previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_appointments(self.current_search)

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_appointments(self.current_search)

    def change_items_per_page(self, value):
        self.items_per_page = int(value)
        self.current_page = 1
        self.load_appointments(self.current_search)

    def view_appointment(self, item):
        appointment_id = item.data(Qt.UserRole)
        dialog = AppointmentViewDialog(appointment_id)
        dialog.exec_()

class AppointmentViewDialog(QDialog):
    def __init__(self, appointment_id):
        super().__init__()
        self.appointment_id = appointment_id
        self.setWindowTitle("Ver Turno")
        layout = QGridLayout()
        self.setLayout(layout)

        session = Session()
        appointment = session.query(Appointment).get(appointment_id)

        # Información del turno
        layout.addWidget(QLabel("Fecha:"), 0, 0)
        layout.addWidget(QLabel(appointment.date.strftime('%d/%m/%Y')), 0, 1)
        layout.addWidget(QLabel("Hora:"), 1, 0)
        layout.addWidget(QLabel(appointment.time.strftime('%H:%M')), 1, 1)
        layout.addWidget(QLabel("Cliente:"), 2, 0)
        layout.addWidget(QLabel(f"{appointment.client.lastname} {appointment.client.name}"), 2, 1)
        layout.addWidget(QLabel("Perro:"), 3, 0)
        layout.addWidget(QLabel(f"{appointment.client.dog_name} ({appointment.client.breed})"), 3, 1)
        layout.addWidget(QLabel("Estado:"), 4, 0)
        layout.addWidget(QLabel(appointment.status), 4, 1)
        layout.addWidget(QLabel("Precio:"), 5, 0)
        layout.addWidget(QLabel(f"${appointment.price}" if appointment.price else "No especificado"), 5, 1)
        layout.addWidget(QLabel("Confirmado:"), 6, 0)
        layout.addWidget(QLabel("Sí" if appointment.confirmed else "No"), 6, 1)
        layout.addWidget(QLabel("Comentarios:"), 7, 0)
        comments = QTextEdit()
        comments.setPlainText(appointment.appoint_comment)
        comments.setReadOnly(True)
        layout.addWidget(comments, 7, 1, 1, 2)

        session.close()

        # Botón de cerrar
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, 8, 0, 1, 2)

        self.apply_styles()

    def apply_styles(self):
        style = """
        QLabel {
            font-size: 12px;
        }
        QLabel:nth-child(odd) {
            font-weight: bold;
        }
        QTextEdit {
            border: 1px solid #ced4da;
            border-radius: 5px;
            padding: 5px;
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
        """
        self.setStyleSheet(style)
