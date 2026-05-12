from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()
DATABASE_URL = "sqlite:///auto_parts.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class Brand(Base):
    __tablename__ = 'brands'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    models = relationship("Model", back_populates="brand", cascade="all, delete-orphan")


class Model(Base):
    __tablename__ = 'models'
    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, ForeignKey('brands.id'), nullable=False)
    name = Column(String(150), nullable=False)
    year_from = Column(Integer)
    year_to = Column(Integer)

    brand = relationship("Brand", back_populates="models")


class Part(Base):
    __tablename__ = 'parts'
    id = Column(Integer, primary_key=True)
    article = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    manufacturer = Column(String(100))
    price = Column(Float)
    stock_quantity = Column(Integer, default=0)
    description = Column(Text)
    image_path = Column(String(300))

    compatibilities = relationship("PartCompatibility", back_populates="part", cascade="all, delete-orphan")


class PartCompatibility(Base):
    __tablename__ = 'part_compatibility'
    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey('parts.id', ondelete='CASCADE'), nullable=False)
    model_id = Column(Integer, ForeignKey('models.id'), nullable=False)

    part = relationship("Part", back_populates="compatibilities")
    model = relationship("Model")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    db = SessionLocal()
    try:
        return db
    finally:
        pass