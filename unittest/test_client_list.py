import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from PyQt5.QtWidgets import QApplication, QTableWidgetItem
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from client_list import ClientListWidget
from database import Session, Client
from unittest.mock import patch, MagicMock

class TestClientListWidget(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def setUp(self):
        self.widget = ClientListWidget()

    def test_initial_state(self):
        # Verifica que los componentes principales existan
        self.assertIsNotNone(self.widget.search_input)
        self.assertIsNotNone(self.widget.search_button)
        # Busca el widget de tabla (podría ser self.widget.tableWidget o similar)
        table_widget = next((attr for attr in dir(self.widget) if 'table' in attr.lower()), None)
        self.assertIsNotNone(getattr(self.widget, table_widget, None))

    @patch('client_list.Session')
    def test_load_clients(self, mock_session):
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        
        mock_clients = [
            MagicMock(id=1, lastname="Pérez", name="Juan", dog_name="Firulais", breed="Labrador"),
            MagicMock(id=2, lastname="Gómez", name="María", dog_name="Luna", breed="Poodle")
        ]
        mock_session_instance.query().all.return_value = mock_clients

        self.widget.current_page = 1
        self.widget.total_pages = 1
        self.widget.items_per_page = 10
        self.widget.total_clients = 2 
        
        self.widget.total_clients = int(self.widget.total_clients)
        
        # with patch.object(self.widget, 'update_pagination_controls'):
        #     self.widget.load_clients()

        table_widget = getattr(self.widget, 'table_widget', None)  
        if table_widget:
            print("hola")
            self.assertEqual(table_widget.rowCount(), 2)
            self.assertEqual(table_widget.item(0, 1).text(), "Pérez")
            self.assertEqual(table_widget.item(1, 1).text(), "Gómez")

    def test_search_clients(self):
        self.widget.search_input.setText("Pérez")
        QTest.mouseClick(self.widget.search_button, Qt.LeftButton)


    @patch('client_list.Session')
    def test_edit_client(self, mock_session):
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        
        mock_client = MagicMock(id=1, lastname="Pérez", name="Juan")
        mock_session_instance.query().get.return_value = mock_client



if __name__ == '__main__':
    unittest.main()