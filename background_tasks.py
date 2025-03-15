import logging
import datetime
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer
from database import Session, Appointment
from sqlalchemy import extract
import time

# Configurar logger
logger = logging.getLogger('background_tasks')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('background_tasks.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class BackgroundWorker(QObject):
    """
    Clase para ejecutar tareas en segundo plano como:
    - Verificar turnos próximos para notificaciones
    - Comprobar cambios en la base de datos
    - Realizar otras tareas periódicas
    """
    
    # Señales para comunicarse con la interfaz principal
    upcoming_appointments = pyqtSignal(list)  # Lista de turnos próximos
    database_changed = pyqtSignal()  # Avisa que hubo cambios en la base de datos
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.last_check_time = datetime.datetime.now()
        self.db_last_update = {}
        self.init_db_state()
        logger.info("BackgroundWorker inicializado")
    
    def init_db_state(self):
        """Inicializa el estado de la base de datos para detectar cambios"""
        session = Session()
        try:
            # Contar cuántos turnos hay por día para el mes actual y el siguiente
            today = datetime.date.today()
            current_month = today.month
            current_year = today.year
            
            next_month = current_month + 1
            next_year = current_year
            if next_month > 12:
                next_month = 1
                next_year += 1
            
            # Obtener recuentos para el mes actual
            self.db_last_update['current_month'] = self.get_appointment_counts(session, current_month, current_year)
            
            # Obtener recuentos para el mes siguiente
            self.db_last_update['next_month'] = self.get_appointment_counts(session, next_month, next_year)
            
            # Guardar tiempo del último chequeo
            self.last_check_time = datetime.datetime.now()
            
            logger.info(f"Estado inicial de la base de datos guardado. Mes actual: {current_month}/{current_year}, "
                     f"Próximo mes: {next_month}/{next_year}")
        except Exception as e:
            logger.error(f"Error al inicializar estado de base de datos: {e}")
        finally:
            session.close()
    
    def get_appointment_counts(self, session, month, year):
        """Obtiene el recuento de turnos por día para un mes específico"""
        counts = {}
        try:
            # Consultar todos los turnos del mes
            appointments = session.query(Appointment).filter(
                extract('month', Appointment.date) == month,
                extract('year', Appointment.date) == year
            ).all()
            
            # Contar por día
            for appointment in appointments:
                day = appointment.date.day
                if day in counts:
                    counts[day] += 1
                else:
                    counts[day] = 1
                    
        except Exception as e:
            logger.error(f"Error al obtener recuentos de turnos: {e}")
        
        return counts
    
    def run(self):
        """Método principal que se ejecuta en segundo plano"""
        self.is_running = True
        logger.info("BackgroundWorker iniciado")
        
        while self.is_running:
            try:
                # Verificar cambios en la base de datos
                if self.check_database_changes():
                    self.database_changed.emit()
                    logger.info("Se detectaron cambios en la base de datos, notificando a la interfaz")
                
                # Verificar turnos próximos
                upcoming = self.check_upcoming_appointments()
                if upcoming:
                    self.upcoming_appointments.emit(upcoming)
                    logger.info(f"Se encontraron {len(upcoming)} turnos próximos")
                
                # Dormir para no consumir muchos recursos
                time.sleep(30)  # Verificar cada 30 segundos
                
            except Exception as e:
                logger.error(f"Error en el ciclo de trabajo en segundo plano: {e}")
                time.sleep(60)  # Esperar un poco más si hay error
    
    def check_database_changes(self):
        """Verifica si han habido cambios en la base de datos desde la última verificación"""
        current_time = datetime.datetime.now()
        # Solo verificar si han pasado al menos 30 segundos desde la última verificación
        if (current_time - self.last_check_time).total_seconds() < 30:
            return False
            
        session = Session()
        try:
            has_changes = False
            today = datetime.date.today()
            current_month = today.month
            current_year = today.year
            
            next_month = current_month + 1
            next_year = current_year
            if next_month > 12:
                next_month = 1
                next_year += 1
            
            # Verificar cambios en el mes actual
            current_month_counts = self.get_appointment_counts(session, current_month, current_year)
            if current_month_counts != self.db_last_update['current_month']:
                has_changes = True
                self.db_last_update['current_month'] = current_month_counts
            
            # Verificar cambios en el mes siguiente
            next_month_counts = self.get_appointment_counts(session, next_month, next_year)
            if next_month_counts != self.db_last_update['next_month']:
                has_changes = True
                self.db_last_update['next_month'] = next_month_counts
            
            # Actualizar tiempo de último chequeo
            self.last_check_time = current_time
            
            return has_changes
            
        except Exception as e:
            logger.error(f"Error al verificar cambios en la base de datos: {e}")
            return False
        finally:
            session.close()
    
    def check_upcoming_appointments(self):
        """Verifica si hay turnos próximos que deben ser notificados"""
        session = Session()
        try:
            current_time = datetime.datetime.now().time()
            current_date = datetime.date.today()
            
            # Buscar turnos en las próximas 2 horas
            two_hours_later = (datetime.datetime.combine(datetime.date.today(), current_time) + 
                             datetime.timedelta(hours=2)).time()
            
            upcoming_appointments = session.query(Appointment).filter(
                Appointment.date == current_date,
                Appointment.time > current_time,
                Appointment.time <= two_hours_later
            ).order_by(Appointment.time).all()
            
            # Convertir a lista de diccionarios para pasar a través de la señal
            result = []
            for appointment in upcoming_appointments:
                result.append({
                    'id': appointment.id,
                    'time': appointment.time.strftime('%H:%M'),
                    'client_name': f"{appointment.client.lastname} {appointment.client.name}",
                    'dog_name': appointment.client.dog_name,
                    'phone': appointment.client.phone,
                    'confirmed': appointment.confirmed
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error al verificar turnos próximos: {e}")
            return []
        finally:
            session.close()
    
    def stop(self):
        """Detiene el hilo de trabajo"""
        self.is_running = False
        logger.info("BackgroundWorker detenido")


class BackgroundTaskManager:
    """
    Administra la ejecución de tareas en segundo plano
    """
    def __init__(self, parent=None):
        self.parent = parent
        self.worker = BackgroundWorker()
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        
        # Conectar señales
        self.thread.started.connect(self.worker.run)
        self.worker.upcoming_appointments.connect(self.handle_upcoming_appointments)
        self.worker.database_changed.connect(self.handle_database_changed)
        
        # Iniciar el hilo
        self.thread.start()
        logger.info("BackgroundTaskManager iniciado")
    
    def handle_upcoming_appointments(self, appointments):
        """Maneja la señal de turnos próximos"""
        if self.parent and hasattr(self.parent, 'notify_upcoming_appointments'):
            self.parent.notify_upcoming_appointments(appointments)
    
    def handle_database_changed(self):
        """Maneja la señal de cambios en la base de datos"""
        if self.parent and hasattr(self.parent, 'refresh_calendar_data'):
            self.parent.refresh_calendar_data()
    
    def stop(self):
        """Detiene todas las tareas en segundo plano"""
        if self.worker and self.thread:
            self.worker.stop()
            self.thread.quit()
            self.thread.wait()
            logger.info("BackgroundTaskManager detenido") 