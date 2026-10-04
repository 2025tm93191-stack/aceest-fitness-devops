"""Training program catalogue, ported from the ACEest v1.x desktop scripts."""

PROGRAMS = {
    "FL": {
        "name": "Fat Loss",
        "workout": [
            "Mon: Back Squat 5x5 + Core",
            "Tue: EMOM 20min Assault Bike",
            "Wed: Bench Press + 21-15-9",
            "Thu: Deadlift + Box Jumps",
            "Fri: Zone 2 Cardio 30min",
        ],
        "diet": [
            "Breakfast: Egg Whites + Oats",
            "Lunch: Grilled Chicken + Brown Rice",
            "Dinner: Fish Curry + Millet Roti",
        ],
        "calorie_factor": 22,
    },
    "MG": {
        "name": "Muscle Gain",
        "workout": [
            "Mon: Squat 5x5",
            "Tue: Bench 5x5",
            "Wed: Deadlift 4x6",
            "Thu: Front Squat 4x8",
            "Fri: Incline Press 4x10",
            "Sat: Barbell Rows 4x10",
        ],
        "diet": [
            "Breakfast: Eggs + Peanut Butter Oats",
            "Lunch: Chicken Biryani",
            "Dinner: Mutton Curry + Rice",
        ],
        "calorie_factor": 35,
    },
    "BG": {
        "name": "Beginner",
        "workout": [
            "Full Body Circuit: Air Squats, Ring Rows, Push-ups",
            "Focus: Technique & Consistency",
        ],
        "diet": [
            "Balanced Tamil Meals: Idli / Dosa / Rice + Dal",
            "Protein Target: 120g/day",
        ],
        "calorie_factor": 26,
    },
}


def list_programs():
    """Return a lightweight summary of every program."""
    return [{"code": code, "name": p["name"]} for code, p in PROGRAMS.items()]


def get_program(code):
    """Look up a program by its code (case-insensitive). Returns None if unknown."""
    if not isinstance(code, str):
        return None
    key = code.strip().upper()
    program = PROGRAMS.get(key)
    if program is None:
        return None
    return {"code": key, **program}
