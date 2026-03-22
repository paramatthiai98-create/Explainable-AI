import streamlit as st
import random
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import time

st.set_page_config(layout="wide")

# auto refresh
st_autorefresh(interval=2000, key="refresh")

st.title("🛡️ SmartSafe Co-Pilot Dashboard (Demo AI)")

# ------------------------
# Sidebar
# ------------------------
mode = st.sidebar.selectbox(
    "Mode",
    ["Auto", "Force Safe", "Force Risk"]
)

# ------------------------
# Generate Data
# ------------------------
def generate_data():
    return {
        "people": random.randint(0, 3),
        "helmet": random.choice([True, False]),
        "distance": random.randint(10, 100),
        "vibration": random.randint(0, 100),
        "temperature": random.randint(25, 80)
    }

# ------------------------
# Risk Logic
# ------------------------
def calculate_risk(d):
    risk = 0
    reasons = []

    if not d["helmet"]:
        risk += 30
        reasons.append("No helmet detected")

    if d["distance"] < 30:
        risk += 40
        reasons.append("Too close to machine")

    if d["vibration"] > 70:
        risk += 35
        reasons.append("High vibration")

    return risk, reasons

def decision_logic(risk):
    if risk > 80:
        return "HIGH RISK", "STOP MACHINE"
    elif risk > 50:
        return "WARNING", "CHECK SYSTEM"
    else:
        return "SAFE", "NORMAL"

# ------------------------
# Main Loop
# ------------------------
if "history" not in st.session_state:
    st.session_state.history = []

placeholder = st.empty()

while True:
    d = generate_data()

    # force mode
    if mode == "Force Safe":
        d["helmet"] = True
    elif mode == "Force Risk":
        d["helmet"] = False

    risk, reasons = calculate_risk(d)
    status, action = decision_logic(risk)

    with placeholder.container():
        col1, col2, col3 = st.columns(3)

        # Worker
        with col1:
            st.subheader("👷 Worker Status")
            st.write(f"People: {d['people']}")
            st.write(f"Helmet: {'YES' if d['helmet'] else 'NO'}")
            st.write(f"Distance: {d['distance']} cm")

        # Machine
        with col2:
            st.subheader("⚙️ Machine Status")
            st.write(f"Vibration: {d['vibration']}")
            st.write(f"Temperature: {d['temperature']} °C")

        # Risk
        with col3:
            st.subheader("⚠️ Risk Analysis")
            st.metric("Risk Score", risk)

            if status == "HIGH RISK":
                st.error(status)
                st.toast("🚨 High Risk Detected!")
            elif status == "WARNING":
                st.warning(status)
            else:
                st.success(status)

        st.subheader("🤖 AI Decision")
        st.write(f"Action: **{action}**")

        st.subheader("🔍 Explainable AI")
        for r in reasons:
            st.write(f"- {r}")

        # chart
        st.session_state.history.append({"risk": risk})
        df = pd.DataFrame(st.session_state.history)
        st.line_chart(df)

    time.sleep(2)
