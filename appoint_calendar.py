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
    QSplitter, QSplitterHandle, QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView, QToolButton,
    QSystemTrayIcon
)
from PyQt5.QtCore import Qt, QTime, QDate, QPoint, QSize, QTimer
from PyQt5.QtGui import QIcon, QTextCharFormat, QColor, QFont, QDoubleValidator, QPainter, QPen
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from logging.handlers import RotatingFileHandler
from background_tasks import BackgroundTaskManager

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

        # Iniciar el administrador de tareas en segundo plano
        self.task_manager = BackgroundTaskManager(self)

        # Crear QSplitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(10)
        self.splitter.setChildrenCollapsible(False)
        layout.addWidget(self.splitter)

        # Calendario
        self.calendar_widget = QWidget()
        calendar_layout = QVBoxLayout(self.calendar_widget)
        
        # Añadir un título al calendario con fecha actual
        self.calendar_header = QLabel()
        self.calendar_header.setAlignment(Qt.AlignCenter)
        self.calendar_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #45a049; margin-bottom: 5px;")
        calendar_layout.addWidget(self.calendar_header)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)  # Mostrar cuadrícula para mejor visibilidad
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)  # Quitar números de semana
        calendar_layout.addWidget(self.calendar)
        
        # Añadir leyenda para el calendario
        # legend_layout = QHBoxLayout()
        # legend_label = QLabel("Leyenda:")
        # legend_label.setStyleSheet("font-weight: bold;")
        # legend_layout.addWidget(legend_label)
        
        # appointment_color = QLabel()
        # appointment_color.setFixedSize(16, 16)
        # appointment_color.setStyleSheet("background-color: #45a049; border: 1px solid #333;")
        # legend_layout.addWidget(appointment_color)
        
        # appointment_text = QLabel("Día con turnos")
        # legend_layout.addWidget(appointment_text)
        
        # today_color = QLabel()
        # today_color.setFixedSize(16, 16)
        # today_color.setStyleSheet("background-color: #f0f0f0; border: 1px solid #333;")
        # legend_layout.addWidget(today_color)
        
        # today_text = QLabel("Día actual")
        # legend_layout.addWidget(today_text)
        
        # legend_layout.addStretch()
        # calendar_layout.addLayout(legend_layout)
        
        self.splitter.addWidget(self.calendar_widget)

        # Lista de turnos
        appointment_widget = QWidget()
        appointment_layout = QVBoxLayout(appointment_widget)
        
        # Título de la lista de turnos
        self.appointment_header = QLabel()
        self.appointment_header.setAlignment(Qt.AlignCenter)
        self.appointment_header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        appointment_layout.addWidget(self.appointment_header)
        
        self.appointment_count_layout = QHBoxLayout()
        self.appointment_count_label = QLabel("Cantidad Turnos:")
        self.appointment_count_number = QLabel("0")
        
        # Añadir botón de actualización manual
        # self.refresh_btn = QPushButton("Actualizar")
        # self.refresh_btn.setToolTip("Actualizar turnos")
        # self.refresh_btn.setFixedSize(28, 28)
        # self.refresh_btn.clicked.connect(self.refresh_appointments)
        # self.refresh_btn.setStyleSheet("""
        #     QPushButton {
        #         background-color: #45a049;
        #         color: white;
        #         border-radius: 14px;
        #         font-weight: bold;
        #     }
        #     QPushButton:hover {
        #         background-color: #3e8e41;
        #     }
        # """)
        
        self.view_toggle_checkbox = QCheckBox("Vista de Tabla")
        self.view_toggle_checkbox.stateChanged.connect(self.toggle_view)
        self.appointment_count_layout.addWidget(self.appointment_count_label)
        self.appointment_count_layout.addWidget(self.appointment_count_number)
        # self.appointment_count_layout.addWidget(self.refresh_btn)
        self.appointment_count_layout.addWidget(self.view_toggle_checkbox)
        self.appointment_count_layout.addStretch()
        appointment_layout.addLayout(self.appointment_count_layout)
        
        # Añadir barra de búsqueda para filtrar turnos
        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filtrar por cliente, mascota o servicio...")
        self.search_input.textChanged.connect(self.filter_appointments)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        appointment_layout.addLayout(search_layout)
        
        self.appointment_list = QListWidget()
        self.appointment_table = QTableWidget()
        self.appointment_table.setColumnCount(9)
        self.appointment_table.setHorizontalHeaderLabels(["Hora", "Cliente", "Dirección", "Teléfono", "Mascota", "Servicio", "Precio", "Confirmado", "Acciones"])
        self.appointment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.appointment_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)  # Fijar el ancho de la columna de acciones
        self.appointment_table.setColumnWidth(8, 70)  # Ajustar el ancho de la columna de acciones
        self.appointment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.appointment_table.setAlternatingRowColors(True)
        self.appointment_table.setStyleSheet("""
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
        """)
        self.appointment_table.hide()  # Inicialmente oculta
        appointment_layout.addWidget(self.appointment_list)
        appointment_layout.addWidget(self.appointment_table)
        self.splitter.addWidget(appointment_widget)

        # Guardar las anchuras originales de las columnas
        self.original_column_widths = [self.appointment_table.columnWidth(i) for i in range(self.appointment_table.columnCount())]

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

        # Agregar botón para repetir turnos
        repeat_weekly_btn = QPushButton("Repetir Turnos")
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
        self.calendar.selectionChanged.connect(self.update_headers)
        
        # Nuevo: Mejorar la actualización al cambiar el mes
        # Detectar el cambio de página (mes) del calendario de forma más robusta
        self.calendar.currentPageChanged.connect(self.on_month_changed)

        # Configurar el temporizador para actualización automática
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_appointments)
        self.refresh_timer.start(60000)  # Actualizar cada 60 segundos
        
        # Variable para mantener los datos de búsqueda
        self.search_text = ""
        self.all_appointments = []
        
        # Crear notificador de sistema
        self.tray_icon = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon("icon.png"))  # Asegúrate de tener un icon.png
            self.tray_icon.setToolTip("TurnosCan - Próximos turnos")

        # Apply styles
        self.apply_styles()

        # Inicializar la vista del calendario
        self.init_calendar_view()

        logger.info("AppointmentCalendarWidget inicializado con temporizador de actualización")
    
    def update_headers(self):
        selected_date = self.calendar.selectedDate()
        
        # Actualizar encabezado del calendario
        today = QDate.currentDate()
        month_name = selected_date.toString("MMMM yyyy")
        month_name = month_name[0].upper() + month_name[1:]
        self.calendar_header.setText(f"Calendario - {month_name}")
        
        # Actualizar encabezado de la lista de turnos
        day_name = selected_date.toString("dddd d 'de' MMMM, yyyy")
        day_name = day_name[0].upper() + day_name[1:]
        
        if selected_date == today:
            day_name += " (Hoy)"
        
        self.appointment_header.setText(f"Turnos para: {day_name}")

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

    def toggle_view(self, state):
        if state == Qt.Checked:
            self.appointment_list.hide()
            self.appointment_table.show()
            # Restaurar las anchuras originales de las columnas
            for i, width in enumerate(self.original_column_widths):
                if i != 8:  # No cambiar el ancho de la columna de acciones
                    self.appointment_table.setColumnWidth(i, width)
            self.appointment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            self.appointment_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        else:
            self.appointment_list.show()
            self.appointment_table.hide()
            # Guardar las anchuras actuales de las columnas
            self.original_column_widths = [self.appointment_table.columnWidth(i) for i in range(self.appointment_table.columnCount())]
            self.appointment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.appointment_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        self.load_appointments()

    def filter_appointments(self):
        """Filtra los turnos según el texto de búsqueda"""
        self.search_text = self.search_input.text().lower()
        self.load_appointments(reload_data=False)  # No recargar de la base de datos
    
    def refresh_appointments(self):
        """Actualiza los turnos manualmente"""
        logger.info("Actualizando turnos manualmente")
        self.load_appointments(reload_data=True)
        self.update_calendar()
        
        # Notificar sobre próximos turnos
        self.check_upcoming_appointments()

    def load_appointments(self, reload_data=True):
        """Carga los turnos para la fecha seleccionada"""
        self.appointment_list.clear()
        self.appointment_table.setRowCount(0)
        selected_date = self.calendar.selectedDate().toPyDate()
        logger.info(f"Cargando turnos para la fecha: {selected_date}")
        
        if reload_data:
            session = Session()
            try:
                # Usar joinedload para cargar los clientes junto con las citas en una sola consulta
                # Esto evita el error DetachedInstanceError
                from sqlalchemy.orm import joinedload
                query = session.query(Appointment).options(
                    joinedload(Appointment.client)
                ).filter(
                    Appointment.date == selected_date
                ).order_by(Appointment.time)
                
                # Convertir a lista mientras la sesión aún está abierta
                self.all_appointments = list(query.all())
            finally:
                # Asegurarse de que la sesión se cierre incluso si hay un error
                session.close()
        
        # Filtrar por búsqueda si hay texto
        filtered_appointments = []
        if self.search_text:
            for appointment in self.all_appointments:
                # Crear copia local de los datos que necesitamos para evitar accesos tardíos
                if appointment.client:
                    client_name = f"{appointment.client.lastname} {appointment.client.name}".lower()
                    dog_name = appointment.client.dog_name.lower() if appointment.client.dog_name else ""
                    address = appointment.client.address.lower() if appointment.client.address else ""
                    phone = appointment.client.phone.lower() if appointment.client.phone else ""
                    appoint_comment = appointment.appoint_comment.lower() if appointment.appoint_comment else ""
                    
                    if (self.search_text in client_name or 
                        self.search_text in dog_name or 
                        self.search_text in address or 
                        self.search_text in phone or
                        self.search_text in appoint_comment):
                        filtered_appointments.append(appointment)
                else:
                    # Si por alguna razón no hay cliente asociado
                    appoint_comment = appointment.appoint_comment.lower() if appointment.appoint_comment else ""
                    if self.search_text in appoint_comment:
                        filtered_appointments.append(appointment)
        else:
            filtered_appointments = self.all_appointments
            
        # Actualizar el contador de turnos mostrados vs totales
        if len(filtered_appointments) == len(self.all_appointments):
            self.appointment_count_number.setText(str(len(filtered_appointments)))
        else:
            self.appointment_count_number.setText(f"{len(filtered_appointments)}/{len(self.all_appointments)}")
        
        # Procesar y mostrar los turnos
        self._display_appointments(filtered_appointments)
        
        logger.info(f"Se cargaron {len(filtered_appointments)} turnos para la fecha {selected_date}")
    
    def _display_appointments(self, appointments):
        """Muestra los turnos en la vista correspondiente (lista o tabla)"""
        for index, appointment in enumerate(appointments, start=1):
            if not self.view_toggle_checkbox.isChecked():
                # Vista de lista
                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)
                
                # Contenido principal del turno
                content_layout = QVBoxLayout()
                
                # Número de orden, hora, fecha, cliente y mascota en una línea
                time_str = appointment.time.strftime('%H:%M')
                
                # Manejar posible ausencia de cliente
                if appointment.client:
                    client_name = f"{appointment.client.lastname} {appointment.client.name}"
                    dog_info = f"{appointment.client.dog_name} ({appointment.client.breed})" if appointment.client.dog_name else ""
                else:
                    client_name = "Cliente desconocido"
                    dog_info = "Sin información"
                
                # Destacar horario con color según confirmación
                if appointment.confirmed:
                    time_color = "#006400"  # Verde oscuro para confirmados
                    status = "✓"
                else:
                    time_color = "#8B0000"  # Rojo oscuro para no confirmados
                    status = "✗"
                
                time_date_client_info = QLabel(f"<b style='color:{time_color};'>{time_str} {status}</b> - "
                                              f"<b>{client_name}</b> - "
                                              f"Perro: <i>{dog_info}</i>")
                time_date_client_info.setStyleSheet("font-size: 14px; color: #333;")
                content_layout.addWidget(time_date_client_info)
                
                # Dirección y teléfono en una línea
                if appointment.client:
                    contact_info = QLabel(f"Dirección: {appointment.client.address} - Tel: {appointment.client.phone}")
                    contact_info.setStyleSheet("font-size: 13px; color: #555;")
                    content_layout.addWidget(contact_info)
                
                # Precio y comentario
                if appointment.price or appointment.appoint_comment:
                    price_str = f"Precio: ${appointment.price}" if appointment.price else ""
                    comment_str = f"Nota: {appointment.appoint_comment}" if appointment.appoint_comment else ""
                    separator = " - " if price_str and comment_str else ""
                    price_comment = QLabel(f"{price_str}{separator}{comment_str}")
                    price_comment.setStyleSheet("font-size: 13px; color: #555; font-style: italic;")
                    content_layout.addWidget(price_comment)
                
                item_layout.addLayout(content_layout)
                
                # Contenedor de botones con layout vertical
                buttons_container = QWidget()
                buttons_layout = QVBoxLayout(buttons_container)
                buttons_layout.setContentsMargins(0, 0, 0, 0)
                buttons_layout.setSpacing(2)
                
                # Botones de acción
                edit_btn = QPushButton("Editar")
                edit_btn.setToolTip("Editar Turno")
                edit_btn.setFixedSize(100, 40)
                appointment_id = appointment.id
                edit_btn.clicked.connect(lambda checked=False, id=appointment_id: self.edit_appointment(id))
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border-radius: 2px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background-color: #45a049; }
                """)
                
                delete_btn = QPushButton("Eliminar")
                delete_btn.setToolTip("Eliminar Turno")
                delete_btn.setFixedSize(100, 40) 
                delete_btn.clicked.connect(lambda checked=False, id=appointment_id: self.delete_appointment(id))
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border-radius: 2px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background-color: #d32f2f; }
                """)
                
                # Checkbox para confirmar turno
                confirm_check = QCheckBox("Confirmado")
                confirm_check.setChecked(appointment.confirmed)
                confirm_check.stateChanged.connect(lambda state, id=appointment_id: self.toggle_confirmation(id, state))
                
                # Agregar widgets al layout de botones
                top_buttons = QHBoxLayout()
                top_buttons.addWidget(edit_btn)
                top_buttons.addWidget(delete_btn)
                buttons_layout.addLayout(top_buttons)
                buttons_layout.addWidget(confirm_check)
                
                item_layout.addWidget(buttons_container)
                
                # Crear y configurar el item de la lista
                list_item = QListWidgetItem()
                list_item.setSizeHint(item_widget.sizeHint())
                self.appointment_list.addItem(list_item)
                self.appointment_list.setItemWidget(list_item, item_widget)
                
                # Alternar colores de fondo
                if index % 2 == 0:
                    item_widget.setStyleSheet("background-color: #f8f8f8;")
            else:
                # Vista de tabla
                row_position = self.appointment_table.rowCount()
                self.appointment_table.insertRow(row_position)
                
                self.appointment_table.setItem(row_position, 0, QTableWidgetItem(appointment.time.strftime('%H:%M')))
                
                # Comprobar si hay cliente antes de acceder a sus propiedades
                if appointment.client:
                    self.appointment_table.setItem(row_position, 1, QTableWidgetItem(f"{appointment.client.lastname} {appointment.client.name}"))
                    self.appointment_table.setItem(row_position, 2, QTableWidgetItem(appointment.client.address))
                    self.appointment_table.setItem(row_position, 3, QTableWidgetItem(appointment.client.phone))
                    self.appointment_table.setItem(row_position, 4, QTableWidgetItem(f"{appointment.client.dog_name} ({appointment.client.breed})"))
                else:
                    self.appointment_table.setItem(row_position, 1, QTableWidgetItem("Cliente desconocido"))
                    self.appointment_table.setItem(row_position, 2, QTableWidgetItem(""))
                    self.appointment_table.setItem(row_position, 3, QTableWidgetItem(""))
                    self.appointment_table.setItem(row_position, 4, QTableWidgetItem(""))
                
                self.appointment_table.setItem(row_position, 5, QTableWidgetItem(appointment.status or "No especificado"))
                self.appointment_table.setItem(row_position, 6, QTableWidgetItem(f"${appointment.price}" if appointment.price else "No especificado"))
                
                # Checkbox para confirmar (centrado)
                confirmed_checkbox = QCheckBox()
                confirmed_checkbox.setChecked(appointment.confirmed)
                confirmed_checkbox.stateChanged.connect(lambda state, a=appointment.id: self.toggle_confirmation(a, state))
                
                # Crear un widget contenedor para el checkbox
                checkbox_container = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_container)
                checkbox_layout.addWidget(confirmed_checkbox)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                
                self.appointment_table.setCellWidget(row_position, 7, checkbox_container)
                
                # Botones de acción
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                actions_layout.setSpacing(2)
                
                edit_button = QToolButton()
                edit_button.setText("E")
                edit_button.setStyleSheet("""
                    QToolButton {
                        background-color: #007bff;
                        color: white;
                        border: none;
                        padding: 3px;
                        border-radius: 3px;
                    }
                    QToolButton:hover {
                        background-color: #0056b3;
                    }
                """)
                edit_button.clicked.connect(lambda _, a=appointment.id: self.edit_appointment(a))
                actions_layout.addWidget(edit_button)
                
                delete_button = QToolButton()
                delete_button.setText("x")
                delete_button.setStyleSheet("""
                    QToolButton {
                        background-color: #dc3545;
                        color: white;
                        border: none;
                        padding: 3px;
                        border-radius: 3px;
                    }
                    QToolButton:hover {
                        background-color: #c82333;
                    }
                """)
                delete_button.clicked.connect(lambda _, a=appointment.id: self.delete_appointment(a))
                actions_layout.addWidget(delete_button)
                
                actions_layout.addStretch()  # Añadir espacio flexible al final
                self.appointment_table.setCellWidget(row_position, 8, actions_widget)

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
        try:
            appointment = session.query(Appointment).get(appointment_id)
            if appointment:
                appointment.confirmed = state == Qt.Checked
                session.commit()
                logger.info(f"Estado de confirmación actualizado para turno ID {appointment_id}")
            else:
                logger.warning(f"No se encontró el turno con ID {appointment_id} para cambiar confirmación")
        except Exception as e:
            logger.error(f"Error al cambiar estado de confirmación: {str(e)}")
            session.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo cambiar el estado: {str(e)}")
        finally:
            session.close()
        
        # Recargar los datos para actualizar la interfaz
        self.load_appointments(reload_data=True)

    def update_calendar(self):
        current_date = self.calendar.selectedDate()
        year, month = current_date.year(), current_date.month()
        
        # Llamar al método específico para marcar días con turnos
        self.highlight_appointment_days(year, month)
        
        logger.info(f"Calendario actualizado para el mes: {month}/{year}")

    def create_appointment(self):
        logger.info("Iniciando creación de nuevo turno")
        session = Session()
        try:
            clients = session.query(Client).all()
        finally:
            session.close()
        
        if not clients:
            QMessageBox.warning(self, "Error", "No existen clientes. Cree un cliente primero para guardar un turno.")
            return
        
        dialog = AppointmentDialog(self.calendar.selectedDate().toPyDate())
        if dialog.exec_():
            logger.info("Nuevo turno creado exitosamente")
            self.load_appointments(reload_data=True)  # Recargar para obtener datos actualizados
            self.update_calendar()
        else:
            logger.info("Creación de turno cancelada")

    def edit_appointment(self, appointment_id):
        logger.info(f"Editando turno con ID: {appointment_id}")
        dialog = AppointmentDialog(self.calendar.selectedDate().toPyDate(), appointment_id)
        if dialog.exec_():
            # Recargar datos para evitar usar objetos detached
            self.load_appointments(reload_data=True)
            self.update_calendar()

    def delete_appointment(self, appointment_id):
        logger.info(f"Intentando eliminar turno con ID: {appointment_id}")
        confirm = QMessageBox.question(self, "Confirmar Eliminación", 
                                       "¿Está seguro de que desea eliminar este turno?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            session = Session()
            try:
                appointment = session.query(Appointment).get(appointment_id)
                if appointment:
                    session.delete(appointment)
                    session.commit()
                    logger.info(f"Turno con ID {appointment_id} eliminado exitosamente")
                else:
                    logger.warning(f"No se encontró el turno con ID {appointment_id} para eliminar")
            except Exception as e:
                logger.error(f"Error al eliminar turno: {str(e)}")
                session.rollback()
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el turno: {str(e)}")
            finally:
                session.close()
            
            # Recargar datos para actualizar la interfaz
            self.load_appointments(reload_data=True)
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

    def check_upcoming_appointments(self):
        """Verifica si hay turnos próximos y notifica al usuario"""
        if not self.tray_icon:
            return
            
        current_time = datetime.datetime.now().time()
        current_date = datetime.date.today()
        
        session = Session()
        try:
            # Usar joinedload para cargar también los clientes
            from sqlalchemy.orm import joinedload
            
            # Buscar turnos en las próximas 2 horas
            two_hours_later = (datetime.datetime.combine(datetime.date.today(), current_time) + 
                             datetime.timedelta(hours=2)).time()
            
            upcoming_appointments = session.query(Appointment).options(
                joinedload(Appointment.client)
            ).filter(
                Appointment.date == current_date,
                Appointment.time > current_time,
                Appointment.time <= two_hours_later
            ).order_by(Appointment.time).all()
            
            if upcoming_appointments:
                message = "Próximos turnos:\n"
                for appointment in upcoming_appointments:
                    if appointment.client:
                        client_name = f"{appointment.client.lastname} {appointment.client.name}"
                    else:
                        client_name = "Cliente desconocido"
                    time_str = appointment.time.strftime('%H:%M')
                    message += f"• {time_str} - {client_name}\n"
                
                self.tray_icon.showMessage(
                    "Recordatorio de Turnos",
                    message,
                    QSystemTrayIcon.Information,
                    10000  # Mostrar por 10 segundos
                )
        except Exception as e:
            logger.error(f"Error al verificar turnos próximos: {str(e)}")
        finally:
            session.close()

    def notify_upcoming_appointments(self, appointments):
        """Recibe notificaciones de turnos próximos desde las tareas en segundo plano"""
        if not self.tray_icon:
            return
            
        if appointments:
            message = "Próximos turnos:\n"
            for appointment in appointments:
                message += f"• {appointment['time']} - {appointment['client_name']}\n"
            
            self.tray_icon.showMessage(
                "Recordatorio de Turnos",
                message,
                QSystemTrayIcon.Information,
                10000  # Mostrar por 10 segundos
            )
    
    def refresh_calendar_data(self):
        """Actualiza los datos del calendario cuando hay cambios en la base de datos"""
        logger.info("Actualizando calendario por cambios en la base de datos")
        # Guardar la fecha seleccionada actual
        current_selected_date = self.calendar.selectedDate()
        
        # Actualizar calendario y citas
        self.update_calendar()
        
        # Solo recargar las citas si el día seleccionado es el actual
        # Esto evita interrupciones inesperadas al usuario si está viendo otro día
        if current_selected_date == QDate.currentDate():
            self.load_appointments(reload_data=True)

    def closeEvent(self, event):
        """Evento que se dispara al cerrar el widget"""
        if hasattr(self, 'task_manager'):
            self.task_manager.stop()
        event.accept()

    def on_month_changed(self, year, month):
        """
        Función específica para manejar el cambio de mes en el calendario.
        Actualiza la visualización para mostrar los días con turnos inmediatamente.
        """
        logger.info(f"Cambio de mes detectado: {month}/{year}")
        
        # Actualizar el formato de fechas para este mes
        self.highlight_appointment_days(year, month)
        
        # Actualizar el encabezado del calendario
        self.update_headers()
    
    def highlight_appointment_days(self, year, month):
        """
        Marca específicamente los días que tienen turnos en el mes seleccionado.
        """
        # Resetear formato de fechas para el mes actual
        start_date = QDate(year, month, 1)
        days_in_month = start_date.daysInMonth()
        
        for day in range(1, days_in_month + 1):
            date = QDate(year, month, day)
            self.calendar.setDateTextFormat(date, QTextCharFormat())
        
        # Consultar y marcar días con turnos
        session = Session()
        try:
            # Usar una consulta SQL más eficiente para obtener solo los días distintos que tienen turnos
            from sqlalchemy import func, distinct
            
            # Obtener solo los días únicos que tienen turnos
            days_with_appointments = session.query(
                func.extract('day', Appointment.date).label('day')
            ).filter(
                extract('month', Appointment.date) == month,
                extract('year', Appointment.date) == year
            ).distinct().all()
            
            # Aplicar formato a esos días
            for day_result in days_with_appointments:
                day = int(day_result[0])  # Extraer el número del día
                date = QDate(year, month, day)
                fmt = self.calendar.dateTextFormat(date)
                fmt.setBackground(QColor(69, 160, 73))  # Verde suave
                fmt.setForeground(QColor(255, 255, 255))  # Texto blanco
                self.calendar.setDateTextFormat(date, fmt)
                
            logger.info(f"Se marcaron {len(days_with_appointments)} días con turnos en {month}/{year}")
        except Exception as e:
            logger.error(f"Error al marcar días con turnos: {str(e)}")
        finally:
            session.close()
    
    def init_calendar_view(self):
        """
        Inicializa la vista del calendario marcando los días con turnos
        para el mes actual y estableciendo la selección en la fecha actual.
        """
        today = QDate.currentDate()
        # Establecer la fecha actual como seleccionada
        self.calendar.setSelectedDate(today)
        # Marcar los días con turnos
        self.highlight_appointment_days(today.year(), today.month())
        # Cargar los turnos para la fecha actual
        self.load_appointments()
        # Actualizar encabezados
        self.update_headers()


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
            /* 
            QDateEdit::down-arrow, QTimeEdit::down-arrow {
                image: url(data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 20 20'%3E%3Cpath fill='%233498db' d='M5 8l5 5 5-5z'/%3E%3C/svg%3E);
                width: 20px;
                height: 20px;
            }
            QDateEdit::down-arrow:hover, QTimeEdit::down-arrow:hover {
                image: url(data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 20 20'%3E%3Cpath fill='%232980b9' d='M5 8l5 5 5-5z'/%3E%3C/svg%3E);
            }
            */
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
            try:
                client = session.query(Client).get(client_id)
                if client:
                    self.client_comments.setText(client.comments or "")
                else:
                    self.client_comments.clear()
                    logger.warning(f"No se encontró el cliente con ID {client_id}")
            except Exception as e:
                logger.error(f"Error al cargar comentarios del cliente: {str(e)}")
                self.client_comments.clear()
            finally:
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
        try:
            # Usar joinedload para cargar el cliente junto con la cita
            from sqlalchemy.orm import joinedload
            appointment = session.query(Appointment).options(
                joinedload(Appointment.client)
            ).get(appointment_id)
            
            if not appointment:
                logger.error(f"No se encontró el turno con ID: {appointment_id}")
                QMessageBox.critical(self, "Error", "No se pudo cargar el turno solicitado.")
                return
                
            self.date_edit.setDate(appointment.date)
            self.time_edit.setTime(appointment.time)
            
            # Cargar el cliente del turno
            if appointment.client:
                client = appointment.client
                self.client_search.setText(f"{client.lastname} {client.name}")
                self.client_combo.clear()
                self.client_combo.addItem(f"{client.lastname} {client.name}", client.id)
            else:
                logger.warning(f"El turno con ID {appointment_id} no tiene cliente asociado")
                self.client_combo.clear()
            
            self.confirmed_checkbox.setChecked(appointment.confirmed)
            self.price_input.setText(str(appointment.price) if appointment.price else "")
            self.service_combo.setCurrentText(appointment.status if appointment.status else "Baño")
            self.notes_input.setText(appointment.appoint_comment if appointment.appoint_comment else "")
            self.update_client_comments()
        except Exception as e:
            logger.error(f"Error al cargar datos del turno: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al cargar el turno: {str(e)}")
        finally:
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