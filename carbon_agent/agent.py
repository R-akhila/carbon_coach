
from dotenv import load_dotenv
from google.adk.agents import LlmAgent

from database.db import save_activity, get_summary
from tools.calculator import (
    calculate_travel_emissions,
    calculate_electricity_emissions,
    calculate_food_emissions,
    calculate_waste_emissions,
    calculate_emissions
)

load_dotenv()

USER_ID = "demo-user"


def record_travel(mode: str, km: float):
    """Calculate and save travel emissions."""

    try:
        result = calculate_travel_emissions(mode, km)
        activity_id = save_activity(result, USER_ID)

        return {
            "message": "Travel saved successfully",
            "activity_id": activity_id,
            **result
        }

    except (ValueError, KeyError) as error:
        return {"error": str(error)}


def record_electricity(kwh: float):
    """Calculate and save electricity emissions."""

    try:
        result = calculate_electricity_emissions(kwh)
        activity_id = save_activity(result, USER_ID)

        return {
            "message": "Electricity saved successfully",
            "activity_id": activity_id,
            **result
        }

    except (ValueError, KeyError) as error:
        return {"error": str(error)}


def record_food(meal_type: str, servings: float):
    """Calculate and save food emissions."""

    try:
        result = calculate_food_emissions(meal_type, servings)
        activity_id = save_activity(result, USER_ID)

        return {
            "message": "Food saved successfully",
            "activity_id": activity_id,
            **result
        }

    except (ValueError, KeyError) as error:
        return {"error": str(error)}


def record_waste(waste_type: str, kg: float):
    """Calculate and save waste emissions."""

    try:
        result = calculate_waste_emissions(waste_type, kg)
        activity_id = save_activity(result, USER_ID)

        return {
            "message": "Waste saved successfully",
            "activity_id": activity_id,
            **result
        }

    except (ValueError, KeyError) as error:
        return {"error": str(error)}


def get_carbon_summary(period: str = "all"):
    """Get saved emissions for today, week, month or all time."""

    try:
        return get_summary(period, USER_ID)

    except ValueError as error:
        return {"error": str(error)}


def estimate_reduction(activity: str, subtype: str, quantity: float):
    """Estimate hypothetical avoided emissions."""

    try:
        result = calculate_emissions(
            activity,
            subtype,
            quantity
        )

        return {
            "estimate_type": "Hypothetical avoided emissions",
            "estimated_avoided_emissions_kg": result["emissions_kg"],
            "factor_status": result["status"],
            "factor_source": result["source"],
            "unit": result["unit"],
            "assumption": (
                "This is a hypothetical estimate, not a measured saving."
            )
        }

    except (ValueError, KeyError) as error:
        return {"error": str(error)}


# MAIN AI AGENT

root_agent = LlmAgent(
    name="carbon_coach",

    model="gemini-3.8-flash",
    
    description=(
        "An AI sustainability assistant that tracks "
        "carbon emissions and suggests ways to reduce them."
    ),

    instruction="""
    You are Carbon Coach, an intelligent environmental assistant.

    Your responsibilities:

    1. Understand the user's daily activities.
    2. Record travel, electricity, food and waste.
    3. Calculate emissions using Python tools.
    4. Retrieve saved carbon summaries.
    5. Suggest practical environmental improvements.
    6. Estimate hypothetical reductions when requested.

    Rules:

    - Always use Python tools for calculations.
    - Never invent emissions or claim an activity was saved
      unless the relevant tool succeeds.
    - Display results in kg CO2e.
    - Clearly identify provisional emission factors.
    - Never present hypothetical savings as actual savings.
    - Ask questions if activity details are missing.
    - Explain everything in simple language.
    - Reply in Telugu if the user asks in Telugu.
    """,

    tools=[
        record_travel,
        record_electricity,
        record_food,
        record_waste,
        get_carbon_summary,
        estimate_reduction
    ]
)
