"""SQLAlchemy ORM models."""

from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from api.database import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    vars = Column(JSON, default=dict)

    hosts = relationship("Host", back_populates="group", cascade="all, delete-orphan")


class Host(Base):
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    vars = Column(JSON, default=dict)

    group = relationship("Group", back_populates="hosts")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
