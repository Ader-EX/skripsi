from datetime import time, datetime, timedelta, date

def generate_time_slots():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    slots = []

    for day in days:
        if day == "Friday":
            start_time = time(13, 30)
        else:
            start_time = time(7, 0)
        
        end_time = time(18, 0)
        current_time = start_time

        while current_time < end_time:
            next_time = (datetime.combine(date.today(), current_time) + timedelta(minutes=50)).time()
            if day != "Friday" and current_time == time(12, 0):
                current_time = time(13, 0)
                continue
            if next_time > end_time:
                break
            slots.append((day, current_time, next_time))
            current_time = next_time

    return slots


from sqlalchemy.orm import Session
from database import engine
from model.timeslot_model import TimeSlot


def insert_time_slots():
    slots = generate_time_slots()
    session = Session(engine)

    for day, start_time, end_time in slots:
        timeslot = TimeSlot(day=day, start_time=start_time, end_time=end_time)
        session.add(timeslot)

    session.commit()
    session.close()

if __name__ == "__main__":
    insert_time_slots()