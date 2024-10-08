import os
from sqlalchemy import Float, create_engine, Column, Integer, String, Date, Time, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

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
        "Labrador", "Golden Retriever", "Pastor Alemán", "Bulldog", "Poodle", "Beagle", "Chihuahua",
        "Boxer", "Salchicha (Dachshund)", "Husky Siberiano", "Yorkshire Terrier", "Rottweiler", "Doberman",
        "Gran Danés", "Schnauzer", "Shih Tzu", "Pomerania", "Cocker Spaniel", "Bulldog Francés",
        "Caniche", "Mastín", "Bóxer", "Galgo", "Collie", "Basset Hound", "Pug", "Chow Chow",
        "Bichón Frisé", "Akita Inu", "Setter Irlandés", "Dálmata", "Terranova", "Shar Pei",
        "Weimaraner", "Bullmastiff", "Pointer", "Samoyedo", "Alaskan Malamute", "Bloodhound",
        "Cane Corso", "Bernés de la Montaña", "Cavalier King Charles Spaniel", "Corgi", "Whippet",
        "Bull Terrier", "Papillón", "Pinscher Miniatura", "Vizsla", "Airedale Terrier"
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