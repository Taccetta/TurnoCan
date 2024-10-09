import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QDate, QTime
from appoint_calendar import AppointmentCalendarWidget, AppointmentDialog
from database import Session, Appointment, Client

class TestAppointmentCalendarWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Crear una instancia de QApplication para los tests
        cls.app = QApplication([])

    def setUp(self):
        self.widget = AppointmentCalendarWidget()

    def test_init(self):
        # Verificar que los widgets principales se han creado
        self.assertIsNotNone(self.widget.calendar)
        self.assertIsNotNone(self.widget.appointment_list)
        self.assertIsNotNone(self.widget.appointment_count_label)
        self.assertIsNotNone(self.widget.appointment_count_number)

    @patch('appoint_calendar.Session')
    def test_load_appointments(self, mock_session):
        # Configurar el mock de la sesión
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        # Crear algunos appointments de prueba
        test_date = QDate(2023, 6, 1).toPyDate()
        test_appointments = [
            MagicMock(id=1, date=test_date, time=QTime(9, 0).toPyTime(), 
                      client=MagicMock(lastname="Doe", name="John")),
            MagicMock(id=2, date=test_date, time=QTime(10, 0).toPyTime(), 
                      client=MagicMock(lastname="Smith", name="Jane"))
        ]
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = test_appointments
        mock_session_instance.query.return_value = mock_query

        # Establecer la fecha seleccionada en el calendario
        self.widget.calendar.setSelectedDate(QDate(2023, 6, 1))

        # Llamar al método que queremos probar
        self.widget.load_appointments()

        # Verificar que se llamó a la consulta de la base de datos
        mock_session_instance.query.assert_called_with(Appointment)

        # Verificar que se actualizó el contador de turnos
        self.assertEqual(self.widget.appointment_count_number.text(), "2")

        # Verificar que se agregaron los items a la lista de turnos
        self.assertEqual(self.widget.appointment_list.count(), 2)

    @patch('appoint_calendar.AppointmentDialog')
    def test_create_appointment(self, mock_dialog):
        # Configurar el mock del diálogo
        mock_dialog_instance = MagicMock()
        mock_dialog_instance.exec_.return_value = True
        mock_dialog.return_value = mock_dialog_instance

        # Llamar al método que queremos probar
        with patch.object(self.widget, 'load_appointments') as mock_load:
            with patch.object(self.widget, 'update_calendar') as mock_update:
                self.widget.create_appointment()

        # Verificar que se creó el diálogo
        mock_dialog.assert_called_once()

        # Verificar que se llamaron los métodos para actualizar la vista
        mock_load.assert_called_once()
        mock_update.assert_called_once()

    # Puedes agregar más tests aquí para otros métodos de AppointmentCalendarWidget

if __name__ == '__main__':
    unittest.main()
