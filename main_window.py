from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
from PyQt5.QtCore import Qt
from backup import BackupWidget
from create_client import CreateClientWidget
from client_list import ClientListWidget 
from appoint_calendar import AppointmentCalendarWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TurnosCan")
        self.setGeometry(200, 50, 1000, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Header
        header_layout = QHBoxLayout()
        create_client_btn = QPushButton("Crear Cliente")
        clients_btn = QPushButton("Clientes")
        appointments_btn = QPushButton("Calendario de Turnos")
        backup_btn = QPushButton("Backup")

        # Apply QSS (styles)
        button_style = """
        QPushButton {
            background-color: #007bff;
            color: white;
            padding: 10px;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:pressed {
            background-color: #004085;
        }
        """

        create_client_btn.setStyleSheet(button_style)
        clients_btn.setStyleSheet(button_style)
        appointments_btn.setStyleSheet(button_style)
        backup_btn.setStyleSheet(button_style)

        header_layout.addWidget(create_client_btn)
        header_layout.addWidget(clients_btn)
        header_layout.addWidget(appointments_btn)
        header_layout.addWidget(backup_btn)

        main_layout.addLayout(header_layout)

        # Stacked Widget for different sections
        self.stacked_widget = QStackedWidget()
        self.create_client_widget = CreateClientWidget()
        self.client_list_widget = ClientListWidget()
        self.appointment_calendar_widget = AppointmentCalendarWidget()
        self.backup_widget = BackupWidget()

        self.stacked_widget.addWidget(self.create_client_widget)
        self.stacked_widget.addWidget(self.client_list_widget)
        self.stacked_widget.addWidget(self.appointment_calendar_widget)
        self.stacked_widget.addWidget(self.backup_widget)

        main_layout.addWidget(self.stacked_widget)

        # Connect buttons to change stacked widget
        create_client_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.create_client_widget))
        clients_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.client_list_widget))
        appointments_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.appointment_calendar_widget))
        backup_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.backup_widget))