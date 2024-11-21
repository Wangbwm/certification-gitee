from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SysStation(Base):
    __tablename__ = 'sys_station'
    id = Column(Integer, primary_key=True, autoincrement=True)
    stationArea = Column(String(255))
    stationType = Column(String(255))
    stationId = Column(Integer)
    stationName = Column(String(255), nullable=False)
    equipmentId = Column(Integer)
    name = Column(String(255))
    controlId = Column(Integer)
    status = Column(Boolean, nullable=False)
    notes = Column(String(255))

    def __repr__(self):
        return "<SysStation(stationId='%s', stationName='%s', equipmentId='%s', name='%s', controlId='%s', status='%s', notes='%s')>" \
              % (self.stationId, self.stationName, self.equipmentId, self.name, self.controlId, self.status, self.notes)
