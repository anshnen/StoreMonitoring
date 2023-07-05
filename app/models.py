from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Time

from .database import Base

class Store(Base):
    __tablename__ = "Store"
    id = Column(Integer, primary_key=True)
    timestamp_utc = Column(DateTime)
    status = Column(String(10))

class BusinessHours(Base):
    __tablename__ = "BuisnessHours"

    id = Column(Integer, primary_key=True)
    store_id = Column(Integer)
    day_of_week = Column(Integer)
    start_time_local = Column(Time)
    end_time_local = Column(Time)

class Timezone(Base):
    __tablename__ = "Timezone"

    id = Column(Integer, primary_key=True)
    store_id = Column(Integer)
    timezone_str = Column(String(50))

class Report(Base):
    __tablename__ = "Report"

    id = Column(Integer, primary_key=True)
    report_id = Column(String(255), nullable=False, unique=True)
    status = Column(String(50), nullable=False)
    data = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() + 'Z',
            'completed_at': self.completed_at.isoformat() + 'Z' if self.completed_at else None
        }