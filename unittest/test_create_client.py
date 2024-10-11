import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from create_client import CreateClientWidget
from database import Session, Client, Breed
from unittest.mock import patch, MagicMock

class TestCreateClientWidget(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def setUp(self):
        self.widget = CreateClientWidget()

    def test_initial_state(self):
        self.assertEqual(self.widget.lastname_input.text(), "")
        self.assertEqual(self.widget.name_input.text(), "")
        self.assertEqual(self.widget.address_input.text(), "")
        self.assertEqual(self.widget.phone_input.text(), "")
        self.assertEqual(self.widget.dog_name_input.text(), "")
        self.assertEqual(self.widget.breed_combo.currentText(), "Seleccione una raza")
        self.assertFalse(self.widget.custom_breed_input.isVisible())

    def test_on_breed_changed(self):
        self.test_breed_selection()
        
        self.widget.breed_combo.setCurrentText("Chihuahua")
        QTest.qWait(100)
        self.assertFalse(self.widget.custom_breed_input.isVisible())

    @patch('create_client.Session')
    @patch('create_client.QMessageBox')
    def test_create_client_success(self, mock_qmessage_box, mock_session):
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance

        self.widget.lastname_input.setText("Pérez")
        self.widget.name_input.setText("Juan")
        self.widget.address_input.setText("Calle 123")
        self.widget.phone_input.setText("1234567890")
        self.widget.dog_name_input.setText("Firulais")
        self.widget.breed_combo.setCurrentText("Chihuahua")
        self.widget.comments_input.setPlainText("Comentario de prueba")

        self.widget.create_client()

        mock_session_instance.add.assert_called_once()
        mock_session_instance.commit.assert_called_once()
        mock_qmessage_box.information.assert_called_once()

    @patch('create_client.Session')
    @patch('create_client.QMessageBox')
    def test_create_client_new_breed(self, mock_qmessage_box, mock_session):
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.query().filter().first.return_value = None

        self.widget.lastname_input.setText("Gómez")
        self.widget.name_input.setText("María")
        self.widget.address_input.setText("Avenida 456")
        self.widget.phone_input.setText("0987654321")
        self.widget.dog_name_input.setText("Luna")
        self.widget.breed_combo.setCurrentText("Otro")
        self.widget.custom_breed_input.setText("Nuevo Breed")
        self.widget.comments_input.setPlainText("Otro comentario")

        self.widget.create_client()

        self.assertEqual(mock_session_instance.add.call_count, 2)  # Una para la nueva raza y otra para el cliente
        self.assertEqual(mock_session_instance.commit.call_count, 2)  # Esperamos dos llamadas a commit()
        mock_qmessage_box.information.assert_called_once()

    def test_clear_fields(self):
        self.widget.lastname_input.setText("Test")
        self.widget.name_input.setText("Test")
        self.widget.address_input.setText("Test")
        self.widget.phone_input.setText("Test")
        self.widget.dog_name_input.setText("Test")
        self.widget.breed_combo.setCurrentIndex(1)
        self.widget.custom_breed_input.setText("Test")
        self.widget.comments_input.setPlainText("Test")

        self.widget.clear_fields()

        self.assertEqual(self.widget.lastname_input.text(), "")
        self.assertEqual(self.widget.name_input.text(), "")
        self.assertEqual(self.widget.address_input.text(), "")
        self.assertEqual(self.widget.phone_input.text(), "")
        self.assertEqual(self.widget.dog_name_input.text(), "")
        self.assertEqual(self.widget.breed_combo.currentIndex(), 0)
        self.assertEqual(self.widget.custom_breed_input.text(), "")
        self.assertEqual(self.widget.comments_input.toPlainText(), "")

    def test_breed_selection(self):
        
        self.assertFalse(self.widget.custom_breed_input.isVisible())

        
        self.widget.breed_combo.setCurrentText("Otro")

        
        self.widget.lastname_input.setText("Apellido")
        self.widget.name_input.setText("Nombre")
        self.widget.address_input.setText("Dirección")
        self.widget.phone_input.setText("123456789")
        self.widget.dog_name_input.setText("Firulais")

        
        self.widget.custom_breed_input.setText("Nueva Raza")

        
        with patch('create_client.Session') as mock_session, \
             patch('create_client.QMessageBox') as mock_qmessage_box:
            mock_session_instance = MagicMock()
            mock_session.return_value = mock_session_instance
            mock_session_instance.query().filter().first.return_value = None

            self.widget.create_client()

            
            self.assertEqual(mock_session_instance.add.call_count, 2) 
            self.assertEqual(mock_session_instance.commit.call_count, 2)  

        
        mock_qmessage_box.information.assert_called_once()

        
        self.assertEqual(self.widget.breed_combo.currentText(), "Seleccione una raza")
        self.assertFalse(self.widget.custom_breed_input.isVisible())

if __name__ == '__main__':
    unittest.main()