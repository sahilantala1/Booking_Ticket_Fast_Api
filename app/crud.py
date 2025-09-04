from sqlalchemy.orm import Session
from . import models, schemas, auth

def create_user(db: Session, user: schemas.UserCreate):
    hashed_pw = auth.hash_password(user.password)
    db_user = models.User(username=user.username, email=user.email, password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_event(db: Session, event: schemas.EventCreate):
    db_event = models.Event(
        title=event.title,
        description=event.description,
        date=event.date,
        location=event.location,
        total_seats=event.total_seats
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    # Auto-generate seats
    for num in range(1, event.total_seats + 1):
        seat = models.Seat(seat_number=num, event_id=db_event.id, is_booked=False)
        db.add(seat)
    db.commit()

    return db_event
