import hashlib
import mysql.connector
from mysql.connector import Error, IntegrityError

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",   # change this
    "database": "cinema_db",
}


# ---------- Helper functions ----------
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def run_select(query, params=(), one=False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        return cursor.fetchone() if one else cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def run_write(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def format_rows(rows):
    # Converts date and time values to text so the GUI can display them
    for row in rows:
        if "show_date" in row:
            row["show_date"] = str(row["show_date"])
        if "show_time" in row:
            row["show_time"] = str(row["show_time"])[:5]   # HH:MM
    return rows


# ---------- Users ----------
def register_user(full_name, email, password):
    if not full_name or not email or not password:
        return False, "Please fill in all fields."
    try:
        run_write(
            "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
            (full_name, email, hash_password(password)),
        )
        return True, "Account created successfully."
    except IntegrityError:
        return False, "This email is already registered."
    except Error as e:
        return False, f"Database error: {e}"


def login_user(email, password):
    # Returns a dictionary (user_id, full_name, role) or None
    return run_select(
        "SELECT user_id, full_name, role FROM users "
        "WHERE email = %s AND password_hash = %s",
        (email, hash_password(password)),
        one=True,
    )


# ---------- Movies and showtimes ----------
def get_movies():
    return run_select("SELECT * FROM movies ORDER BY title")


def get_showtimes(movie_id):
    rows = run_select(
        "SELECT s.showtime_id, s.show_date, s.show_time, s.price, h.hall_name "
        "FROM showtimes s JOIN halls h ON s.hall_id = h.hall_id "
        "WHERE s.movie_id = %s AND s.show_date >= CURDATE() "
        "ORDER BY s.show_date, s.show_time",
        (movie_id,),
    )
    return format_rows(rows)


def get_seat_map(showtime_id):
    # is_booked = 1 if the seat is already booked for this showtime
    return run_select(
        "SELECT st.seat_id, st.row_label, st.seat_number, "
        "       (bs.seat_id IS NOT NULL) AS is_booked "
        "FROM showtimes s "
        "JOIN seats st ON st.hall_id = s.hall_id "
        "LEFT JOIN booking_seats bs "
        "       ON bs.seat_id = st.seat_id AND bs.showtime_id = s.showtime_id "
        "WHERE s.showtime_id = %s "
        "ORDER BY st.row_label, st.seat_number",
        (showtime_id,),
    )


# ---------- Bookings ----------
def book_seats(user_id, showtime_id, seat_ids):
    if not seat_ids:
        return False, "Please select at least one seat."

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT price FROM showtimes WHERE showtime_id = %s", (showtime_id,))
        row = cursor.fetchone()
        if row is None:
            return False, "Showtime not found."
        total = row["price"] * len(seat_ids)

        cursor.execute(
            "INSERT INTO bookings (user_id, showtime_id, total_price) VALUES (%s, %s, %s)",
            (user_id, showtime_id, total),
        )
        booking_id = cursor.lastrowid

        for seat_id in seat_ids:
            cursor.execute(
                "INSERT INTO booking_seats (booking_id, showtime_id, seat_id) "
                "VALUES (%s, %s, %s)",
                (booking_id, showtime_id, seat_id),
            )
        conn.commit()
        return True, f"Booking confirmed! Total price: {total} EGP"
    except IntegrityError:
        conn.rollback()
        return False, "One of the selected seats was just booked by someone else."
    except Error as e:
        conn.rollback()
        return False, f"Database error: {e}"
    finally:
        cursor.close()
        conn.close()


def get_user_bookings(user_id):
    rows = run_select(
        "SELECT b.booking_id, m.title, h.hall_name, s.show_date, s.show_time, "
        "       GROUP_CONCAT(CONCAT(st.row_label, st.seat_number) "
        "                    ORDER BY st.row_label, st.seat_number SEPARATOR ', ') AS seats, "
        "       b.total_price "
        "FROM bookings b "
        "JOIN showtimes s ON b.showtime_id = s.showtime_id "
        "JOIN movies m ON s.movie_id = m.movie_id "
        "JOIN halls h ON s.hall_id = h.hall_id "
        "JOIN booking_seats bs ON bs.booking_id = b.booking_id "
        "JOIN seats st ON st.seat_id = bs.seat_id "
        "WHERE b.user_id = %s "
        "GROUP BY b.booking_id, m.title, h.hall_name, s.show_date, s.show_time, b.total_price "
        "ORDER BY b.booking_date DESC",
        (user_id,),
    )
    return format_rows(rows)


def cancel_booking(booking_id, user_id):
    # The user_id check makes sure a customer can only cancel their own booking
    deleted = run_write(
        "DELETE FROM bookings WHERE booking_id = %s AND user_id = %s",
        (booking_id, user_id),
    )
    if deleted:
        return True, "Booking cancelled."
    return False, "Booking not found."


# ---------- Admin functions ----------
def add_movie(title, genre, duration_min):
    try:
        run_write(
            "INSERT INTO movies (title, genre, duration_min) VALUES (%s, %s, %s)",
            (title, genre, int(duration_min)),
        )
        return True, "Movie added."
    except (Error, ValueError) as e:
        return False, f"Error: {e}"


def update_movie(movie_id, title, genre, duration_min):
    try:
        run_write(
            "UPDATE movies SET title = %s, genre = %s, duration_min = %s WHERE movie_id = %s",
            (title, genre, int(duration_min), movie_id),
        )
        return True, "Movie updated."
    except (Error, ValueError) as e:
        return False, f"Error: {e}"


def delete_movie(movie_id):
    try:
        run_write("DELETE FROM movies WHERE movie_id = %s", (movie_id,))
        return True, "Movie deleted."
    except Error as e:
        return False, f"Error: {e}"


def get_halls():
    return run_select("SELECT * FROM halls ORDER BY hall_name")


def add_showtime(movie_id, hall_id, show_date, show_time, price):
    # show_date format: YYYY-MM-DD, show_time format: HH:MM
    try:
        clash = run_select(
            "SELECT showtime_id FROM showtimes "
            "WHERE hall_id = %s AND show_date = %s AND show_time = %s",
            (hall_id, show_date, show_time),
            one=True,
        )
        if clash:
            return False, "This hall already has a showtime at that date and time."
        run_write(
            "INSERT INTO showtimes (movie_id, hall_id, show_date, show_time, price) "
            "VALUES (%s, %s, %s, %s, %s)",
            (movie_id, hall_id, show_date, show_time, float(price)),
        )
        return True, "Showtime added."
    except (Error, ValueError) as e:
        return False, f"Error: {e}"


def get_all_bookings():
    rows = run_select(
        "SELECT b.booking_id, u.full_name, m.title, s.show_date, s.show_time, "
        "       COUNT(bs.id) AS seats_count, b.total_price "
        "FROM bookings b "
        "JOIN users u ON b.user_id = u.user_id "
        "JOIN showtimes s ON b.showtime_id = s.showtime_id "
        "JOIN movies m ON s.movie_id = m.movie_id "
        "JOIN booking_seats bs ON bs.booking_id = b.booking_id "
        "GROUP BY b.booking_id, u.full_name, m.title, s.show_date, s.show_time, b.total_price "
        "ORDER BY b.booking_date DESC"
    )
    return format_rows(rows)