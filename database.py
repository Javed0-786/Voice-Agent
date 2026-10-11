import sqlite3
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any

DB_FILE = os.path.join(os.path.dirname(__file__), "aura_clinic.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Services Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        duration_minutes INTEGER NOT NULL,
        price REAL NOT NULL,
        description TEXT NOT NULL
    )
    """)

    # Bookings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        service_name TEXT NOT NULL,
        booking_date TEXT NOT NULL,
        booking_time TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # Seed initial services if empty
    cursor.execute("SELECT COUNT(*) FROM services")
    if cursor.fetchone()[0] == 0:
        services = [
            ("General Wellness Consultation", "Medical", 30, 75.0, "Comprehensive intake and personalized health evaluation with our clinician."),
            ("Deep Tissue Massage", "Therapy", 60, 120.0, "Therapeutic muscular tension relief and targeted myofascial release."),
            ("Facial Skin Therapy", "Aesthetics", 45, 95.0, "Hydrating facial treatment, gentle exfoliation, and rejuvenation therapy."),
            ("Acupuncture & Recovery", "Holistic", 45, 110.0, "Traditional acupuncture balancing energy meridians and chronic pain reduction."),
            ("Chiropractic Alignment", "Chiropractic", 30, 130.0, "Spinal decompression and joint articulation adjustment.")
        ]
        cursor.executemany("""
        INSERT INTO services (name, category, duration_minutes, price, description)
        VALUES (?, ?, ?, ?, ?)
        """, services)

    # Seed sample existing bookings for testing if empty
    cursor.execute("SELECT COUNT(*) FROM bookings")
    if cursor.fetchone()[0] == 0:
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
        sample_bookings = [
            ("BK-1001", "Alex Turner", "+1-555-234-5678", "Deep Tissue Massage", tomorrow, "14:00", "CONFIRMED", datetime.now().isoformat()),
            ("BK-1002", "Samantha Hayes", "+1-555-876-5432", "Facial Skin Therapy", next_week, "11:00", "CONFIRMED", datetime.now().isoformat())
        ]
        cursor.executemany("""
        INSERT INTO bookings (id, customer_name, customer_phone, service_name, booking_date, booking_time, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_bookings)

    conn.commit()
    conn.close()

def get_services() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, category, duration_minutes, price, description FROM services ORDER BY price ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def check_availability(service_name: str, booking_date: str) -> List[str]:
    """Check available time slots (09:00 to 17:00) for a given date and service."""
    all_slots = ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT booking_time FROM bookings 
    WHERE booking_date = ? AND status = 'CONFIRMED'
    """, (booking_date,))
    booked_times = {row["booking_time"] for row in cursor.fetchall()}
    conn.close()
    return [slot for slot in all_slots if slot not in booked_times]

def create_booking(customer_name: str, customer_phone: str, service_name: str, booking_date: str, booking_time: str) -> Dict[str, Any]:
    """Creates a new confirmed appointment."""
    import random
    booking_id = f"BK-{random.randint(2000, 9999)}"
    now = datetime.now().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check conflict
    cursor.execute("""
    SELECT id FROM bookings 
    WHERE booking_date = ? AND booking_time = ? AND status = 'CONFIRMED'
    """, (booking_date, booking_time))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "error": f"Time slot {booking_time} on {booking_date} is already taken. Please choose another slot."}

    cursor.execute("""
    INSERT INTO bookings (id, customer_name, customer_phone, service_name, booking_date, booking_time, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, 'CONFIRMED', ?)
    """, (booking_id, customer_name, customer_phone, service_name, booking_date, booking_time, now))
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "booking_id": booking_id,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "service_name": service_name,
        "booking_date": booking_date,
        "booking_time": booking_time,
        "status": "CONFIRMED"
    }

def lookup_booking(search_query: str) -> Optional[Dict[str, Any]]:
    """Look up a booking by booking ID or customer phone number."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM bookings 
    WHERE id = ? OR customer_phone LIKE ? OR customer_name LIKE ?
    ORDER BY created_at DESC LIMIT 1
    """, (search_query.strip(), f"%{search_query.strip()}%", f"%{search_query.strip()}%"))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def reschedule_booking(booking_id: str, new_date: str, new_time: str) -> Dict[str, Any]:
    """Reschedules an existing booking to a new date and time."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Find existing
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    booking = cursor.fetchone()
    if not booking:
        conn.close()
        return {"success": False, "error": f"Booking ID {booking_id} not found."}

    # Check slot conflict
    cursor.execute("""
    SELECT id FROM bookings 
    WHERE booking_date = ? AND booking_time = ? AND status = 'CONFIRMED' AND id != ?
    """, (new_date, new_time, booking_id))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "error": f"Slot {new_time} on {new_date} is occupied. Please select an available slot."}

    cursor.execute("""
    UPDATE bookings 
    SET booking_date = ?, booking_time = ?, status = 'CONFIRMED'
    WHERE id = ?
    """, (new_date, new_time, booking_id))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "booking_id": booking_id,
        "service_name": booking["service_name"],
        "customer_name": booking["customer_name"],
        "new_date": new_date,
        "new_time": new_time,
        "status": "RESCHEDULED"
    }

def cancel_booking(booking_id: str) -> Dict[str, Any]:
    """Cancels a booking by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    booking = cursor.fetchone()
    if not booking:
        conn.close()
        return {"success": False, "error": f"Booking ID {booking_id} not found."}

    cursor.execute("UPDATE bookings SET status = 'CANCELLED' WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()
    return {
        "success": True,
        "booking_id": booking_id,
        "customer_name": booking["customer_name"],
        "status": "CANCELLED"
    }

def get_all_bookings() -> List[Dict[str, Any]]:
    """Get all bookings sorted by date and time."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings ORDER BY booking_date DESC, booking_time DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Initialize schema on load
init_db()
