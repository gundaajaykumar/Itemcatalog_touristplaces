import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Tourism(Base):
    __tablename__ = 'tourist'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class Destination(Base):
    __tablename__ = 'pack'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    details = Column(String(250))
    charge = Column(String(8))
    course = Column(String(250))
    tourist_id = Column(Integer, ForeignKey('tourist.id'))
    tourist = relationship(Tourism)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'details': self.details,
            'id': self.id,
            'charge': self.charge,
            'course': self.course,
        }


engine = create_engine('sqlite:///skytravels.db')


Base.metadata.create_all(engine)
