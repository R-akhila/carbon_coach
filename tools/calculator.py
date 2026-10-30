
from tools.factors import EMISSION_FACTORS


def calculate_emissions(activity, subtype, quantity):

    # Validate the activity category
    if activity not in EMISSION_FACTORS:
        raise ValueError("Invalid activity category")

    # Validate the selected activity type
    if subtype not in EMISSION_FACTORS[activity]:
        raise ValueError("Invalid activity type")

    # Validate quantity
    if isinstance(quantity, bool) or not isinstance(quantity, (int, float)):
        raise ValueError("Quantity must be a number")

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")

    # Get the emission factor
    details = EMISSION_FACTORS[activity][subtype]

    factor = details["factor"]

    # Calculate carbon emissions
    emissions = quantity * factor

    # Return calculation details
    return {
        "activity": activity,
        "type": subtype,
        "quantity": quantity,
        "emission_factor": factor,
        "unit": details["unit"],
        "emissions_kg": round(emissions, 3),
        "status": details["status"],
        "source": details["source"]
    }


# Travel calculation
def calculate_travel_emissions(mode, km):

    return calculate_emissions(
        "Travel",
        mode,
        km
    )


# Electricity calculation
def calculate_electricity_emissions(kwh):

    return calculate_emissions(
        "Electricity",
        "Electricity",
        kwh
    )


# Food calculation
def calculate_food_emissions(meal_type, servings=1):

    return calculate_emissions(
        "Food",
        meal_type,
        servings
    )


# Waste calculation
def calculate_waste_emissions(waste_type, kg):

    return calculate_emissions(
        "Waste",
        waste_type,
        kg
    )
