import os
from sqlalchemy import Float, create_engine, Column, Integer, String, Date, Time, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func
from sqlalchemy import inspect
import datetime

Base = declarative_base()

# Función para obtener la hora local actual
def local_now():
    return datetime.datetime.now()

class Breed(Base):
    __tablename__ = 'breeds'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    lastname = Column(String)
    name = Column(String)
    address = Column(String)
    phone = Column(String)
    dog_name = Column(String)
    breed = Column(String)
    comments = Column(Text)
    created_at = Column(DateTime, default=local_now)

    appointments = relationship("Appointment", back_populates="client")

class Appointment(Base):
    __tablename__ = 'appointments'

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    time = Column(Time)
    repeat_weekly = Column(Boolean)
    repeat_monthly = Column(Boolean)
    confirmed = Column(Boolean, default=False)
    status = Column(String)
    appoint_comment = Column(String)
    price = Column(Float)
    client_id = Column(Integer, ForeignKey('clients.id'))
    created_at = Column(DateTime, default=local_now)

    client = relationship("Client", back_populates="appointments")

# Obtener la ruta absoluta del directorio del archivo main.py
main_dir = os.path.dirname(os.path.abspath(__file__))

# Construir la ruta de la base de datos en base a la ubicación del archivo main.py
db_path = os.path.join(main_dir, 'dog_grooming.db')

engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

    # Add initial breeds
    session = Session()
    initial_breeds = [
        "Salchicha", "Chihuahua"
    ]
    for breed_name in initial_breeds:
        if not session.query(Breed).filter_by(name=breed_name).first():
            session.add(Breed(name=breed_name))
    session.commit()
    session.close()

def close_db_connections():
    # Cierra la sesión global si existe
    if hasattr(Session, 'session'):
        Session.session.close()
    
    # Cierra el motor de la base de datos
    engine.dispose()

def verify_database_integrity():
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        # Verificar que podemos acceder a todos los datos de las tablas
        inspector = inspect(engine)
        for table_name in inspector.get_table_names():
            table = Base.metadata.tables[table_name]
            session.query(table).all()
        return True
    except Exception as e:
        print(f"Error durante la verificación de integridad: {e}")
        return False
    finally:
        session.close()