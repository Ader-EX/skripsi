from datetime import time, timedelta, datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from model.timeslot_model import TimeSlot

def create_timeslots():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    start_morning = time(8, 0)
    end_morning = time(11, 40)
    start_afternoon = time(13, 0)
    end_day = time(18, 0)
    interval = timedelta(minutes=50)

    # Use SessionLocal from database.py
    session = SessionLocal()

    try:
        for day in days:
            if day == "Friday":
                # Special time slots for Friday
                current_time = start_morning

                # Morning slots
                while current_time < end_morning:
                    end_time = (datetime.combine(datetime.min, current_time) + interval).time()
                    if end_time <= end_morning:
                        timeslot = TimeSlot(
                            day=day,
                            start_time=current_time,
                            end_time=end_time
                        )
                        session.add(timeslot)
                    current_time = end_time

                # Afternoon slots
                current_time = start_afternoon
                while current_time < end_day:
                    end_time = (datetime.combine(datetime.min, current_time) + interval).time()
                    if end_time <= end_day:
                        timeslot = TimeSlot(
                            day=day,
                            start_time=current_time,
                            end_time=end_time
                        )
                        session.add(timeslot)
                    current_time = end_time
            else:
                # Regular time slots for other days
                current_time = start_morning

                # Morning slots
                while current_time < end_morning:
                    end_time = (datetime.combine(datetime.min, current_time) + interval).time()
                    if end_time <= end_morning:
                        timeslot = TimeSlot(
                            day=day,
                            start_time=current_time,
                            end_time=end_time
                        )
                        session.add(timeslot)
                    current_time = end_time

                # Afternoon slots
                current_time = start_afternoon
                while current_time < end_day:
                    end_time = (datetime.combine(datetime.min, current_time) + interval).time()
                    if end_time <= end_day:
                        timeslot = TimeSlot(
                            day=day,
                            start_time=current_time,
                            end_time=end_time
                        )
                        session.add(timeslot)
                    current_time = end_time

        # Commit the session to save changes to the database
        session.commit()
        print("Time slots created successfully.")

    except Exception as e:
        print("Error occurred:", e)
        session.rollback()
    finally:
        session.close()

# Run the script
create_timeslots()