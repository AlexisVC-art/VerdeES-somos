from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database.connection import Base


class PlantStatus(str, enum.Enum):
    NATIVA = "nativa"
    INVASIVA = "invasiva"
    INTRODUCIDA = "introducida"
    DESCONOCIDO = "desconocido"


class Plant(Base):
    __tablename__ = "plants"

    id = Column(Integer, primary_key=True, index=True)
    scientific_name = Column(String(255), unique=True, nullable=False, index=True)
    common_name_es = Column(String(255), nullable=True)
    common_name_local = Column(String(255), nullable=True)
    kingdom = Column(String(100), default="Plantae")
    family = Column(String(150), nullable=True)
    genus = Column(String(150), nullable=True)
    status = Column(Enum(PlantStatus), default=PlantStatus.DESCONOCIDO, index=True)
    is_priority = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    ecological_impact = Column(Text, nullable=True)
    control_methods = Column(Text, nullable=True)
    native_range = Column(String(255), nullable=True)
    gbif_taxon_key = Column(Integer, nullable=True, index=True)
    inaturalist_taxon_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    occurrences = relationship("Occurrence", back_populates="plant")
    images = relationship("Image", back_populates="plant")


class Occurrence(Base):
    __tablename__ = "occurrences"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False, index=True)
    source = Column(String(50), nullable=False)
    source_id = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    country = Column(String(100), default="El Salvador")
    locality = Column(String(255), nullable=True)
    observed_at = Column(DateTime, nullable=True)
    is_verified = Column(Boolean, default=False)
    raw_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    plant = relationship("Plant", back_populates="occurrences")


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False, index=True)
    file_path = Column(String(500), nullable=True)
    url = Column(String(500), nullable=True)
    source = Column(String(50), nullable=True)
    source_id = Column(String(100), nullable=True)
    is_for_training = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    plant = relationship("Plant", back_populates="images")