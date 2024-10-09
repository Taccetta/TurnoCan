from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
from PyQt5.QtCore import Qt
from backup import BackupWidget
from create_client import CreateClientWidget
from client_list import ClientListWidget 
from appoint_calendar import AppointmentCalendarWidget
from appointment_search import AppointmentSearchWidget  # Importar el nuevo widget

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
        self.create_client_btn = QPushButton("Crear Cliente")
        self.clients_btn = QPushButton("Clientes")
        self.appointments_btn = QPushButton("Calendario de Turnos")
        self.appointment_search_btn = QPushButton("Buscar Turnos")  # Nuevo botón
        self.backup_btn = QPushButton("Backup")

        # Estilos de botones
        self.button_style = """
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
        
        self.active_button_style = """
        QPushButton {
            background-color: #004085;
            color: white;
            padding: 10px;
            border: none;
            border-radius: 5px;
        }
        """

        # Aplicar estilos iniciales
        for btn in [self.create_client_btn, self.clients_btn, self.appointments_btn, self.appointment_search_btn, self.backup_btn]:
            btn.setStyleSheet(self.button_style)

        header_layout.addWidget(self.create_client_btn)
        header_layout.addWidget(self.clients_btn)
        header_layout.addWidget(self.appointments_btn)
        header_layout.addWidget(self.appointment_search_btn)  # Agregar el nuevo botón
        header_layout.addWidget(self.backup_btn)

        main_layout.addLayout(header_layout)

        # Stacked Widget for different sections
        self.stacked_widget = QStackedWidget()
        self.create_client_widget = CreateClientWidget()
        self.client_list_widget = ClientListWidget()
        self.appointment_calendar_widget = AppointmentCalendarWidget()
        self.appointment_search_widget = AppointmentSearchWidget()  # Nuevo widget
        self.backup_widget = BackupWidget()

        self.stacked_widget.addWidget(self.create_client_widget)
        self.stacked_widget.addWidget(self.client_list_widget)
        self.stacked_widget.addWidget(self.appointment_calendar_widget)
        self.stacked_widget.addWidget(self.appointment_search_widget)  # Agregar el nuevo widget
        self.stacked_widget.addWidget(self.backup_widget)

        main_layout.addWidget(self.stacked_widget)

        # Conectar botones
        self.create_client_btn.clicked.connect(lambda: self.change_section(self.create_client_widget, self.create_client_btn))
        self.clients_btn.clicked.connect(lambda: self.change_section(self.client_list_widget, self.clients_btn))
        self.appointments_btn.clicked.connect(lambda: self.change_section(self.appointment_calendar_widget, self.appointments_btn))
        self.appointment_search_btn.clicked.connect(lambda: self.change_section(self.appointment_search_widget, self.appointment_search_btn))
        self.backup_btn.clicked.connect(lambda: self.change_section(self.backup_widget, self.backup_btn))

        # Botón activo inicial
        self.active_button = None

    def change_section(self, widget, button):
        self.stacked_widget.setCurrentWidget(widget)
        self.update_active_button(button)

    def update_active_button(self, new_active_button):
        if self.active_button:
            self.active_button.setStyleSheet(self.button_style)
        new_active_button.setStyleSheet(self.active_button_style)
        self.active_button = new_active_button