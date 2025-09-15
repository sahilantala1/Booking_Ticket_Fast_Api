from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class User(Base):
    __tablename__ = "bookings_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    date = Column(DateTime, nullable=False)
    location = Column(String, nullable=False)
    total_seats = Column(Integer, nullable=False)

    # Relationships
    seats = relationship("Seat", back_populates="event", cascade="all, delete")
    bookings = relationship("Booking", back_populates="event", cascade="all, delete")


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    seat_number = Column(Integer, nullable=False)
    is_booked = Column(Boolean, default=False)

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))

    # Relationships
    event = relationship("Event", back_populates="seats")
    bookings = relationship("Booking", back_populates="seat", cascade="all, delete")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("bookings_users.id", ondelete="CASCADE"))
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))
    seat_id = Column(Integer, ForeignKey("seats.id", ondelete="CASCADE"))
    booking_date = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    event = relationship("Event", back_populates="bookings")
    seat = relationship("Seat", back_populates="bookings")
