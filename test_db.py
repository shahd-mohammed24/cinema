import db

print("1. Movies:")
for m in db.get_movies():
    print("  ", m["movie_id"], m["title"], m["genre"])

print("\n2. Login test:")
user = db.login_user("sara@gmail.com", "sara123")
print("  ", user)
print("   Wrong password:", db.login_user("sara@gmail.com", "wrong"))

print("\n3. Showtimes of movie 1:")
for s in db.get_showtimes(1):
    print("  ", s)

print("\n4. Seat map of showtime 1:")
seats = db.get_seat_map(1)
print("   Total seats:", len(seats))
print("   Booked seats:", sum(1 for s in seats if s["is_booked"]))

print("\n5. Booking seats 1 and 2:")
print("  ", db.book_seats(user["user_id"], 1, [1, 2]))

print("\n6. Double booking (must fail):")
print("  ", db.book_seats(user["user_id"], 1, [2, 3]))

print("\n7. My bookings:")
bookings = db.get_user_bookings(user["user_id"])
for b in bookings:
    print("  ", b)

print("\n8. Cancel booking:")
print("  ", db.cancel_booking(bookings[0]["booking_id"], user["user_id"]))

print("\n9. Register duplicate email (must fail):")
print("  ", db.register_user("Sara", "sara@gmail.com", "123"))