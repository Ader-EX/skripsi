from datetime import time, timedelta, datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from model.timeslot_model import TimeSlot

def create_timeslots():
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
    interval = timedelta(minutes=50)

    # Define specific time ranges
    start_morning_regular = time(7, 10)
    end_morning_regular = time(12, 10)
    start_afternoon_regular = time(13, 0)
    end_day_regular = time(18, 0)

    start_morning_friday = time(8, 0)
    end_morning_friday = time(11, 20)
    start_afternoon_friday = time(13, 30)
    end_day_friday = time(17, 30)

    session = SessionLocal()

    try:
        for day in days:
            if day == "Jumat":
                # Friday (Jumat) schedule
                current_time = start_morning_friday
                while current_time < end_morning_friday:
                    end_time = (datetime.combine(datetime.min, current_time) + interval).time()
                    if end_time <= end_morning_friday:
                        session.add(TimeSlot(day=day, start_time=current_time, end_time=end_time))
                    current_time = end_time

                # Break from 11:20 to 13:30
                
                # Afternoon slots
                current_time = start_afternoon_friday
                while current_time < end_day_friday:
                    end_time = (datetime.combine(datetime.min, current_time) + interval).time()
                    if end_time <= end_day_friday:
                        session.add(TimeSlot(day=day, start_time=current_time, end_time=end_time))
                    current_time = end_time

            else:
                # Monday to Thursday (Senin - Kamis) schedule
                current_time = start_morning_regular
                while current_time < end_morning_regular:
                    end_time = (datetime.combine(datetime.min, current_time) + interval).time()
                    if end_time <= end_morning_regular:
                        session.add(TimeSlot(day=day, start_time=current_time, end_time=end_time))
                    current_time = end_time

                # Break from 12:10 to 13:00
                
                # Afternoon slots
                current_time = start_afternoon_regular
                while current_time < end_day_regular:
                    end_time = (datetime.combine(datetime.min, current_time) + interval).time()
                    if end_time <= end_day_regular:
                        session.add(TimeSlot(day=day, start_time=current_time, end_time=end_time))
                    current_time = end_time

        session.commit()
        print("Time slots created successfully.")

    except Exception as e:
        print("Error occurred:", e)
        session.rollback()
    finally:
        session.close()

# Run the script
create_timeslots()
