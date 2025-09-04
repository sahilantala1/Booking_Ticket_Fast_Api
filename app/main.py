from fastapi import FastAPI, Depends, HTTPException, Request, Form, Body
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app import models, schemas, crud, auth, database

# Create all database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Add session middleware (for login persistence)
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# ------------------- AUTH -------------------

@app.get("/register_page", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register_user")
def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    db_user = crud.get_user_by_username(db, username)
    if db_user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already taken"}
        )

    user_data = schemas.UserCreate(username=username, email=email, password=password)
    crud.create_user(db, user_data)
    return RedirectResponse(url="/login_page", status_code=302)


@app.get("/login_page", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login_user")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    db_user = crud.get_user_by_username(db, username)
    if not db_user or not auth.verify_password(password, db_user.password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )

    # ✅ Store user session
    request.session["user_id"] = db_user.id
    request.session["username"] = db_user.username

    return RedirectResponse(url="/events_page", status_code=302)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()   # ✅ clears user_id + username from session
    return RedirectResponse(url="/login_page", status_code=302)

# ------------------- EVENTS -------------------

@app.post("/events", response_model=schemas.EventResponse)
def create_event(event: schemas.EventCreate, db: Session = Depends(database.get_db)):
    return crud.create_event(db, event)


@app.get("/events_page", response_class=HTMLResponse)
def events_page(request: Request, db: Session = Depends(database.get_db)):
    events = db.query(models.Event).all()
    username = request.session.get("username", "Guest")
    return templates.TemplateResponse(
        "events.html",
        {"request": request, "events": events, "username": username}
    )


@app.get("/event/{event_id}", response_class=HTMLResponse)
def show_event(request: Request, event_id: int, db: Session = Depends(database.get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        return HTMLResponse(content="Event not found", status_code=404)

    user_id = request.session.get("user_id", 0)
    username = request.session.get("username", "Guest")

    return templates.TemplateResponse(
        "event.html",
        {"request": request, "event": event, "user_id": user_id, "username": username}
    )


@app.get("/events/{event_id}/seats")
def get_seat_map(event_id: int, db: Session = Depends(database.get_db)):
    seats = db.query(models.Seat).filter(models.Seat.event_id == event_id).all()
    return [{"seat_number": s.seat_number, "is_booked": s.is_booked} for s in seats]


# --------- MULTI-SEAT BOOKING ---------
@app.post("/events/{event_id}/book")
def book_multiple_seats(
    event_id: int,
    request: Request,
    booking_request: schemas.BookSeatsRequest = Body(...),
    db: Session = Depends(database.get_db)
):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Please login to book seats")

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    booked = []
    failed = []

    for seat_number in booking_request.seats:
        seat = db.query(models.Seat).filter(
            models.Seat.event_id == event_id,
            models.Seat.seat_number == seat_number
        ).first()

        if not seat or seat.is_booked:
            failed.append(seat_number)
            continue

        seat.is_booked = True
        booking = models.Booking(user_id=user_id, event_id=event_id, seat_id=seat.id)
        db.add(booking)
        booked.append(seat_number)

    db.commit()

    return {
        "message": f"Booked seats: {booked}, Failed: {failed}"
    }


# --------- USER BOOKINGS ---------
@app.get("/my_bookings", response_class=HTMLResponse)
def my_bookings(request: Request, db: Session = Depends(database.get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login_page", status_code=302)

    bookings = (
        db.query(models.Booking)
        .join(models.Event, models.Booking.event_id == models.Event.id)
        .join(models.Seat, models.Booking.seat_id == models.Seat.id)
        .filter(models.Booking.user_id == user_id)
        .all()
    )

    username = request.session.get("username", "Guest")
    return templates.TemplateResponse(
        "my_bookings.html",
        {"request": request, "bookings": bookings, "username": username}
    )
