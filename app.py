import streamlit as st
import datetime
import json
from pathlib import Path
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import schedule
import threading
import time

# App-specific email configuration
REMINDER_EMAIL = "aasifdrive@gmail.com"
EMAIL_PASSWORD = "vxvo zeix ndbp pckz"

APP_TITLE = "💪Fitness Checker"
DATA_FILE = Path("data/progress.json")

COMMON_EXERCISES = [
    "Push-ups", "Squats", "Plank (secs)", "Jumping Jacks", "Burpees", "Lunges", "Sit-ups",
    "Crunches", "Mountain Climbers", "High Knees", "Skipping", "Running (mins)", "Cycling (mins)",
    "Walking (steps)", "Yoga (mins)"
]

st.set_page_config(page_title=APP_TITLE, layout="wide")

# CSS styling
st.markdown("""
    <style>
    html, body, [class*="css"] {
        background-color: #fff0f5 !important;
        color: #5a005a !important;
        font-family: "Comic Sans MS", cursive, sans-serif;
    }
    .stButton button {
        background-color: #ffb6c1;
        color: white;
        font-weight: bold;
        border-radius: 20px;
        padding: 0.5em 1em;
        border: none;
    }
    .stButton button:hover {
        background-color: #ff69b4;
    }
    .calendar-cell {
        display:inline-block;
        width:80px;
        height:80px;
        margin:5px;
        padding:10px;
        border:2px solid #ffb6c1;
        text-align:center;
        font-size: 16px;
        font-weight: bold;
        border-radius: 12px;
        background-color: #ffe4e1;
        box-shadow: 1px 1px 5px #ffc0cb;
    }
    .calendar-cell.star { background-color: #ffe066 !important; }
    .calendar-cell.green { background-color: #b2f2bb !important; }
    .calendar-cell.red { background-color: #ffa8a8 !important; }
    .calendar-cell.incomplete { background-color: #f0f0f0 !important; }
    </style>
""", unsafe_allow_html=True)

st.title(APP_TITLE)

# Helpers
def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.warning("Error: Data file is corrupted or not valid JSON.")
            return {}
    return {}

def save_data(data):
    DATA_FILE.parent.mkdir(exist_ok=True)
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        st.warning(f"Error saving data: {e}")

def send_email(subject, body, to_email):
    msg = MIMEText(body)
    msg["From"] = REMINDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(REMINDER_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        st.warning(f"Email could not be sent: {e}")

def schedule_daily_reminder():
    schedule.every().day.at("07:00").do(lambda: send_email(
        "🌞 Daily Fitness Reminder", "Hey Madhu Priya! Don't forget to complete and log your workout today 💪", "aasif013010@gmail.com"))
    while True:
        schedule.run_pending()
        time.sleep(60)

def start_reminder_thread():
    threading.Thread(target=schedule_daily_reminder, daemon=True).start()

def generate_date_range(start, end):
    return [start + datetime.timedelta(days=i) for i in range((end - start).days + 1)]

def render_calendar(start_date, end_date, log):
    st.markdown("### 📅 Challenge Calendar")
    for day in generate_date_range(start_date, end_date):
        day_str = str(day)
        status = log.get(day_str, {}).get("status", "incomplete")
        symbol = {"green": "✅", "star": "🌟", "red": "❌"}.get(status, "⬜")
        css_class = status if status in ["green", "star", "red"] else "incomplete"
        st.markdown(f"<div class='calendar-cell {css_class}'>{day.day}<br>{symbol}</div>", unsafe_allow_html=True)

def render_summary(log):
    st.markdown("### 📋 View My Stats")
    if not log:
        st.info("No data yet.")
        return
    records = []
    for date, entry in log.items():
        for ex, count in entry.get("entries", {}).items():
            records.append({"date": date, "exercise": ex, "count": count})
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    st.dataframe(df.pivot_table(index="date", columns="exercise", values="count", fill_value=0))
    st.bar_chart(df.groupby("exercise")["count"].sum())

# Load Data
data = load_data()
today = datetime.date.today()

# Set up challenge if not done
if "plan" not in data:
    with st.form("setup_form"):
        st.subheader("💖 Set Your Fitness Challenge")
        start = st.date_input("Start Date", today)
        end = st.date_input("End Date", today + datetime.timedelta(days=14))
        num_ex = st.number_input("Number of Exercises", 1, 10, 3)
        exercises = {}
        for i in range(num_ex):
            col1, col2 = st.columns([2, 1])
            with col1:
                ex = st.selectbox(f"Exercise {i+1}", ["-- Select --"] + COMMON_EXERCISES + ["Other"], key=f"ex_{i}")
                if ex == "Other":
                    ex = st.text_input(f"Custom Exercise {i+1}", key=f"custom_{i}")
            with col2:
                target = st.number_input(f"Target {i+1}", min_value=1, value=10, key=f"target_{i}")
            if ex and ex != "-- Select --":
                exercises[ex] = target
        submitted = st.form_submit_button("💪 Start My Challenge")
        if submitted and start < end:
            data = {"plan": {"start_date": str(start), "end_date": str(end), "exercises": exercises}, "log": {}}
            save_data(data)
            send_email("🎉 Challenge Started!", f"Hey Madhu Priya! Your challenge from {start} to {end} has started! 💖", "aasif013010@gmail.com")
            start_reminder_thread()
            st.success("Challenge created! Daily reminders set 🕖")

    # Add refresh button on form page
    if st.button("🔄 Refresh Page"):
        st.rerun()

    st.stop()

# Use existing plan
plan = data["plan"]
log = data.get("log", {})
start_date = datetime.date.fromisoformat(plan["start_date"])
end_date = datetime.date.fromisoformat(plan["end_date"])

# Calendar view
render_calendar(start_date, end_date, log)

# Log Today
if start_date <= today <= end_date:
    today_str = str(today)
    st.subheader(f"📅 Log for {today.strftime('%A, %d %B %Y')}")
    if today_str not in log:
        user_input = {}
        complete = True
        exceeded = False
        for ex, target in plan["exercises"].items():
            val = st.number_input(f"{ex} completed", 0, 1000, key=ex)
            user_input[ex] = val
            if val < target:
                complete = False
            if val > target:
                exceeded = True
        if st.button("✅ Clock Out"):
            if complete and exceeded:
                status = "star"
            elif complete:
                status = "green"
            else:
                status = "red"
            log[today_str] = {"entries": user_input, "status": status}
            data["log"] = log
            save_data(data)
            st.success("Progress saved 💖")
    else:
        st.info("You've already clocked out for today 💅")

# Stats
if st.button("📊 View My Stats Now"):
    render_summary(log)

# 🔄 Refresh Button
if st.button("🔄 Refresh Page"):
    st.experimental_rerun()

# 🗑️ Clear Challenge Data Button
if st.button("🗑️ Clear Challenge Data"):
    if DATA_FILE.exists():
        DATA_FILE.unlink()
        st.success("Challenge data cleared. Refreshing app...")
        st.experimental_rerun()
    else:
        st.info("No challenge data to clear.")
