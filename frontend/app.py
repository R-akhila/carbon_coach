
import os
import sys
import uuid
import sqlite3
import asyncio

from pathlib import Path
from datetime import datetime, timezone

import streamlit as st
import plotly.express as px

from dotenv import load_dotenv
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService


# =====================================================
# 1. PROJECT CONFIGURATION
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FOLDER = PROJECT_ROOT / "database"
DATABASE_FOLDER.mkdir(exist_ok=True)

DB_PATH = DATABASE_FOLDER / "carbon_coach.db"

load_dotenv(PROJECT_ROOT / ".env")

APP_NAME = "carbon_coach"
USER_ID = "demo-user"

MODEL_NAME = "gemini-3.8-flash"


# =====================================================
# 2. EMISSION FACTORS
# =====================================================

EMISSION_FACTORS = {
    "Travel": {
        "Bus": 0.08,
        "Car": 0.21,
        "Motorcycle": 0.10,
        "Train": 0.04
    },

    "Electricity": {
        "Electricity": 0.716
    },

    "Food": {
        "Vegetarian": 0.7,
        "Non-vegetarian": 2.5
    },

    "Waste": {
        "Plastic": 2.5,
        "Paper": 1.0,
        "Organic": 0.5
    }
}

FACTOR_STATUS = {
    "Bus": "Illustrative project example",
    "Car": "Provisional demo assumption",
    "Motorcycle": "Provisional demo assumption",
    "Train": "Provisional demo assumption",
    "Electricity": "Provisional grid factor; verify latest CEA data",
    "Vegetarian": "Provisional demo assumption",
    "Non-vegetarian": "Provisional demo assumption",
    "Plastic": "Provisional demo assumption",
    "Paper": "Provisional demo assumption",
    "Organic": "Provisional demo assumption"
}


# =====================================================
# 3. DATABASE FUNCTIONS
# =====================================================

def get_connection():

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def init_db():

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS activities (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id TEXT NOT NULL,

            activity TEXT NOT NULL,

            subtype TEXT NOT NULL,

            quantity REAL NOT NULL,

            emission_factor REAL NOT NULL,

            emissions_kg REAL NOT NULL,

            unit TEXT NOT NULL,

            factor_status TEXT,

            source TEXT,

            created_at TEXT NOT NULL

        )
    """)

    connection.commit()
    connection.close()


def save_activity(result, user_id=USER_ID):

    connection = get_connection()

    cursor = connection.execute("""
        INSERT INTO activities (
            user_id,
            activity,
            subtype,
            quantity,
            emission_factor,
            emissions_kg,
            unit,
            factor_status,
            source,
            created_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        result["activity"],
        result["type"],
        result["quantity"],
        result["emission_factor"],
        result["emissions_kg"],
        result["unit"],
        result["status"],
        result["source"],
        datetime.now(timezone.utc).isoformat()
    ))

    activity_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return activity_id


def get_activities(user_id=USER_ID):

    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM activities
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def is_today(timestamp):

    try:

        date_value = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )

        if date_value.tzinfo is None:
            date_value = date_value.replace(tzinfo=timezone.utc)

        local_date = date_value.astimezone().date()

        return local_date == datetime.now().astimezone().date()

    except (ValueError, TypeError):
        return False


def get_summary(period="all", user_id=USER_ID):

    activities = get_activities(user_id)

    if period == "today":

        activities = [
            row for row in activities
            if is_today(row["created_at"])
        ]

    elif period == "week":

        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        activities = [
            row for row in activities
            if datetime.fromisoformat(
                row["created_at"].replace("Z", "+00:00")
            ) >= cutoff
        ]

    elif period == "month":

        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        activities = [
            row for row in activities
            if datetime.fromisoformat(
                row["created_at"].replace("Z", "+00:00")
            ) >= cutoff
        ]

    total = round(
        sum(row["emissions_kg"] for row in activities), 3
    )

    by_activity = {}

    for row in activities:

        category = row["activity"]

        by_activity[category] = (
            by_activity.get(category, 0)
            + row["emissions_kg"]
        )

    by_activity = {
        key: round(value, 3)
        for key, value in by_activity.items()
    }

    return {
        "total_activities": len(activities),
        "total_emissions": total,
        "by_activity": by_activity
    }


# =====================================================
# 4. CARBON CALCULATOR
# =====================================================

def calculate_emissions(activity, subtype, quantity):

    if activity not in EMISSION_FACTORS:
        raise ValueError("Invalid activity category")

    if subtype not in EMISSION_FACTORS[activity]:
        raise ValueError("Invalid activity type")

    if isinstance(quantity, bool) or not isinstance(
        quantity, (int, float)
    ):
        raise ValueError("Quantity must be a number")

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")

    factor = EMISSION_FACTORS[activity][subtype]

    emissions = round(quantity * factor, 3)

    unit = {
        "Travel": "kg CO2e/passenger-km",
        "Electricity": "kg CO2e/kWh",
        "Food": "kg CO2e/serving",
        "Waste": "kg CO2e/kg"
    }[activity]

    return {
        "activity": activity,
        "type": subtype,
        "quantity": quantity,
        "emission_factor": factor,
        "unit": unit,
        "emissions_kg": emissions,
        "status": FACTOR_STATUS[subtype],
        "source": "Carbon Coach prototype emission-factor table"
    }


# =====================================================
# 5. AI AGENT TOOLS
# =====================================================

def record_travel(mode: str, km: float) -> str:

    """Calculate and save travel emissions."""

    result = calculate_emissions("Travel", mode, km)

    activity_id = save_activity(result)

    return (
        f"Travel activity saved. ID: {activity_id}. "
        f"Emissions: {result['emissions_kg']} kg CO2e. "
        f"Factor status: {result['status']}."
    )


def record_electricity(kwh: float) -> str:

    """Calculate and save electricity emissions."""

    result = calculate_emissions(
        "Electricity", "Electricity", kwh
    )

    activity_id = save_activity(result)

    return (
        f"Electricity activity saved. ID: {activity_id}. "
        f"Emissions: {result['emissions_kg']} kg CO2e. "
        f"Factor status: {result['status']}."
    )


def record_food(meal_type: str, servings: float) -> str:

    """Calculate and save food emissions."""

    result = calculate_emissions("Food", meal_type, servings)

    activity_id = save_activity(result)

    return (
        f"Food activity saved. ID: {activity_id}. "
        f"Emissions: {result['emissions_kg']} kg CO2e. "
        f"Factor status: {result['status']}."
    )


def record_waste(waste_type: str, kg: float) -> str:

    """Calculate and save waste emissions."""

    result = calculate_emissions("Waste", waste_type, kg)

    activity_id = save_activity(result)

    return (
        f"Waste activity saved. ID: {activity_id}. "
        f"Emissions: {result['emissions_kg']} kg CO2e. "
        f"Factor status: {result['status']}."
    )


def get_carbon_summary(period: str = "all") -> str:

    """Retrieve saved carbon-emission summary."""

    if period not in ["today", "week", "month", "all"]:
        return "Choose today, week, month, or all."

    summary = get_summary(period)

    return (
        f"Period: {period}. "
        f"Activities: {summary['total_activities']}. "
        f"Total emissions: {summary['total_emissions']} kg CO2e. "
        f"Categories: {summary['by_activity']}."
    )


# =====================================================
# 6. CREATE GEMINI AGENT
# =====================================================

root_agent = LlmAgent(

    name="carbon_coach",

    model=MODEL_NAME,

    description=(
        "An AI environmental assistant that tracks "
        "and helps reduce carbon footprints."
    ),

    instruction="""
    You are Carbon Coach, a friendly environmental AI agent.

    Your responsibilities:

    1. Help users understand their carbon footprint.
    2. Record travel, electricity, food and waste activities.
    3. Use your tools for all carbon calculations.
    4. Retrieve saved activity summaries when requested.
    5. Give practical recommendations to reduce emissions.
    6. Explain calculations clearly.
    7. Never invent activity records or emission values.
    8. Clearly identify provisional emission factors as estimates.
    9. Ask for missing information before recording an activity.
    10. Do not claim an activity was saved unless the tool confirms it.

    Use simple, friendly language.
    Keep answers concise and useful.
    """,

    tools=[
        record_travel,
        record_electricity,
        record_food,
        record_waste,
        get_carbon_summary
    ]
)


# =====================================================
# 7. GEMINI ADK RUNNER
# =====================================================

@st.cache_resource
def get_agent_runner():

    session_service = InMemorySessionService()

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    return runner, session_service


async def ask_carbon_agent(prompt, session_id):

    runner, session_service = get_agent_runner()

    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id
    )

    if session is None:

        await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id
        )

    message = types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=prompt)
        ]
    )

    answer = ""

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message
    ):

        if event.is_final_response() and event.content:

            for part in event.content.parts:

                if part.text:
                    answer += part.text

    return answer or "Please try asking your question again."


# =====================================================
# 8. LOCAL DATABASE QUESTION ANSWERS
# =====================================================

def answer_from_database(prompt):

    question = prompt.lower().strip()

    history_questions = [
        "what activities have i recorded today",
        "what activities did i record today",
        "what did i record today",
        "show my activities today",
        "activities recorded today",
        "today's activities",
        "my activities today"
    ]

    if not any(q in question for q in history_questions):
        return None

    activities = get_activities(USER_ID)

    today_activities = [
        row for row in activities
        if is_today(row["created_at"])
    ]

    if not today_activities:

        return (
            "You haven't recorded any activities today. "
            "Add an activity in Track Activities! 🌱"
        )

    total = sum(
        float(row["emissions_kg"])
        for row in today_activities
    )

    answer = "🌱 **Your activities recorded today:**\n\n"

    quantity_units = {
        "Travel": "km",
        "Electricity": "kWh",
        "Food": "servings",
        "Waste": "kg"
    }

    for index, row in enumerate(today_activities, start=1):

        quantity_unit = quantity_units.get(
            row.get("activity"), ""
        )

        answer += (
            f"**{index}. {row.get('activity')} – "
            f"{row.get('subtype')}**\n"
            f"- Quantity: {row.get('quantity')} {quantity_unit}\n"
            f"- Emissions: {row.get('emissions_kg')} kg CO₂e\n\n"
        )
        

    return answer


# =====================================================
# 9. INITIALIZE APPLICATION
# =====================================================

init_db()

st.set_page_config(
    page_title="Carbon Coach",
    page_icon="🌿",
    layout="wide"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_session_id" not in st.session_state:
    st.session_state.agent_session_id = str(uuid.uuid4())


# =====================================================
# 10. CSS DESIGN
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #f5f8f3;
}

[data-testid="stSidebar"] {
    background-color: #153d2b;
}

[data-testid="stSidebar"] * {
    color: white;
}

.main-title {
    color: #17452f;
    font-size: 36px;
    font-weight: 800;
}

.subtitle {
    color: #738477;
}

.hero {
    background: linear-gradient(120deg,#17452f,#28734a);
    padding: 28px;
    border-radius: 18px;
    color: white;
    margin-bottom: 20px;
}

.hero h2 {
    color: white;
}

.hero p {
    color: #e0eee3;
}

.stButton > button {
    background-color: #28734a;
    color: white;
    border-radius: 10px;
    border: none;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 11. SIDEBAR NAVIGATION
# =====================================================

with st.sidebar:

    st.title("🌿 Carbon Coach")

    st.caption("YOUR SUSTAINABILITY PARTNER")

    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "Track Activities",
            "AI Coach",
            "History"
        ]
    )

    st.divider()

    st.write("🌍 Think Green. Live Green.")


# =====================================================
# 12. DASHBOARD
# =====================================================

if page == "Dashboard":

    st.markdown(
        '<p class="main-title">Dashboard 🌱</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">Your sustainability overview</p>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="hero">
        <h2>Make Every Action Count!</h2>
        <p>
        Track your activities and discover
        smarter ways to protect our planet.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Carbon Footprint Overview")

    period = st.selectbox(
        "Select Report Period",
        ["Today", "Last 7 Days", "Last 30 Days", "All Time"]
    )

    period_mapping = {
        "Today": "today",
        "Last 7 Days": "week",
        "Last 30 Days": "month",
        "All Time": "all"
    }

    summary = get_summary(period_mapping[period])

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Activities",
        summary["total_activities"]
    )

    c2.metric(
        "Carbon Footprint",
        f"{summary['total_emissions']} kg CO₂e"
    )

    c3.metric(
        "Activity Categories",
        len(summary["by_activity"])
    )

    st.subheader("Emissions by Category")

    if summary["by_activity"]:

        fig = px.bar(
            x=list(summary["by_activity"].keys()),
            y=list(summary["by_activity"].values()),
            labels={
                "x": "Activity",
                "y": "Emissions (kg CO₂e)"
            },
            title="Carbon Emissions Analysis"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info("No activities recorded for this period.")
        st.subheader("Your Activities")

    if summary["by_activity"]:

        fig = px.pie(
            names=list(summary["by_activity"].keys()),
            values=list(summary["by_activity"].values()),
            hole=0.5,
            title="Today's Carbon Emissions"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "Start recording activities to see your footprint."
        )


# =====================================================
# 13. TRACK ACTIVITIES
# =====================================================

elif page == "Track Activities":

    st.subheader("Track Activities 🚀")

    activity = st.selectbox(
        "Activity",
        ["Travel", "Electricity", "Food", "Waste"]
    )

    if activity == "Travel":

        subtype = st.selectbox(
            "Transport mode",
            ["Bus", "Car", "Motorcycle", "Train"]
        )

        quantity = st.number_input(
            "Distance (km)",
            min_value=0.1,
            value=1.0
        )

    elif activity == "Electricity":

        subtype = "Electricity"

        quantity = st.number_input(
            "Electricity consumed (kWh)",
            min_value=0.1,
            value=1.0
        )

    elif activity == "Food":

        subtype = st.selectbox(
            "Meal type",
            ["Vegetarian", "Non-vegetarian"]
        )

        quantity = st.number_input(
            "Number of servings",
            min_value=0.1,
            value=1.0
        )

    elif activity == "Waste":

        subtype = st.selectbox(
            "Waste type",
            ["Plastic", "Paper", "Organic"]
        )

        quantity = st.number_input(
            "Waste quantity (kg)",
            min_value=0.1,
            value=1.0
        )

    if st.button("Save Activity"):

        try:

            result = calculate_emissions(
                activity,
                subtype,
                quantity
            )

            activity_id = save_activity(result)

            st.success(
                f"Activity saved successfully! ID: {activity_id} 🌱"
            )

            st.metric(
                "Carbon Emissions",
                f"{result['emissions_kg']} kg CO₂e"
            )

            st.caption(
                f"Emission factor status: {result['status']}"
            )

        except Exception as error:

            st.error(f"Error: {error}")


# =====================================================
# 14. AI COACH
# =====================================================

elif page == "AI Coach":

    st.markdown(
        '<p class="main-title">AI Eco Coach 🤖</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">Talk to your personal carbon assistant</p>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="hero">
        <h2>Hello! Welcome to Carbon Coach 🌿</h2>
        <p>
        Tell me about your activities or ask me
        how to reduce your carbon footprint.
        </p>
    </div>
    """, unsafe_allow_html=True)

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Ask Carbon Coach something..."
    )

    if prompt:

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):

            if prompt:
                with st.spinner("Getting your activity summary..."):

                    answer = answer_from_database(prompt)

                if answer is None:
                    try:
                        answer = asyncio.run(
                            ask_carbon_agent(
                                prompt,
                                st.session_state.agent_session_id
                            )
                        )
                    except Exception as e:
                        answer = f"AI service error: {e}"

            st.write(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })


# =====================================================
# 15. HISTORY
# =====================================================

elif page == "History":

    st.markdown(
        '<p class="main-title">Activity History 📋</p>',
        unsafe_allow_html=True
    )

    activities = get_activities(USER_ID)

    if activities:

        st.dataframe(
            activities,
            use_container_width=True,
            hide_index=True
        )

        all_summary = get_summary("all")

        st.metric(
            "Total Carbon Emissions",
            f"{all_summary['total_emissions']} kg CO₂e"
        )

        if all_summary["by_activity"]:

            fig = px.pie(
                names=list(all_summary["by_activity"].keys()),
                values=list(all_summary["by_activity"].values()),
                title="Emissions by Activity",
                hole=0.5
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    else:

        st.info("No saved activities yet.")


# =====================================================
# 16. FOOTER
# =====================================================

st.divider()

st.caption(
    "🌿 Carbon Coach | Think Green. Live Green."
)
