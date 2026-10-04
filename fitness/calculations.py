"""Pure calculation helpers, kept free of Flask/DB code so they are easy to unit test."""

from .programs import PROGRAMS


def _positive_number(value, field):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a number")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a number")
    if number <= 0:
        raise ValueError(f"{field} must be greater than zero")
    return number


def estimate_calories(weight_kg, program_code):
    """Daily calorie target = body weight (kg) x the program's calorie factor."""
    weight = _positive_number(weight_kg, "weight_kg")
    program = PROGRAMS.get(str(program_code).strip().upper())
    if program is None:
        raise ValueError(f"Unknown program '{program_code}'")
    return int(weight * program["calorie_factor"])


def calculate_bmi(height_cm, weight_kg):
    """Return (bmi, category) using WHO adult categories."""
    height_m = _positive_number(height_cm, "height_cm") / 100
    weight = _positive_number(weight_kg, "weight_kg")
    bmi = round(weight / (height_m ** 2), 1)
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    return bmi, category


def validate_adherence(value):
    """Weekly adherence is a whole-number percentage between 0 and 100."""
    if isinstance(value, bool):
        raise ValueError("adherence must be an integer")
    try:
        adherence = int(value)
    except (TypeError, ValueError):
        raise ValueError("adherence must be an integer")
    if not 0 <= adherence <= 100:
        raise ValueError("adherence must be between 0 and 100")
    return adherence
