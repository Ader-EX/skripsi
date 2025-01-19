import random
from sqlalchemy.orm import Session
from database import SessionLocal
from model.dosen_model import Dosen
from model.preference_model import Preference
from model.timeslot_model import TimeSlot

def generate_preferences():
    session = SessionLocal()
    try:
        # Fetch all dosens and timeslots
        dosens = session.query(Dosen).all()
        timeslots = session.query(TimeSlot).filter(TimeSlot.id <= 50).all()

        if not timeslots:
            raise ValueError("No timeslots found in the range 1-50.")

        print(f"Found {len(dosens)} dosens and {len(timeslots)} timeslots.")

        # Create a dictionary to track timeslot usage
        timeslot_usage = {timeslot.id: 0 for timeslot in timeslots}

        preferences = []
        for dosen in dosens:
            num_preferences = random.randint(1, 5)  # Each dosen has 1-5 preferences
            preferred_timeslots = random.sample(timeslots, num_preferences)  # Randomly select timeslots

            for timeslot in preferred_timeslots:
                # Ensure timeslot is not overpopulated (e.g., max 5 dosens per timeslot as an example)
                if timeslot_usage[timeslot.id] < 5:
                    # Use weighted probabilities: 80% False, 20% True
                    is_special_needs = random.choices([False, True], weights=[80, 20], k=1)[0]
                    is_high_priority = random.choices([False, True], weights=[80, 20], k=1)[0]

                    preference = Preference(
                        dosen_id=dosen.id,
                        timeslot_id=timeslot.id,
                        is_special_needs=is_special_needs,
                        is_high_priority=is_high_priority,
                        reason=random.choice([
                            None,
                            "Personal preference",
                            "Research project",
                            "Family obligations",
                            "Scheduling constraints"
                        ])
                    )
                    preferences.append(preference)
                    timeslot_usage[timeslot.id] += 1

        # Insert preferences into the database
        session.bulk_save_objects(preferences)
        session.commit()

        print(f"Generated and inserted {len(preferences)} preferences.")
        print("Timeslot usage:")
        for timeslot_id, count in timeslot_usage.items():
            print(f"Timeslot {timeslot_id}: {count} preferences")
    except Exception as e:
        print(f"Error occurred: {e}")
        session.rollback()
    finally:
        session.close()

# Run the generator
generate_preferences()
