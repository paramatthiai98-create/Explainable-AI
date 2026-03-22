import streamlit as st
import random
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from ultralytics import YOLO
import cv2
import tempfile
import time

st.set_page_config(layout="wide")

# auto refresh (สำหรับ dashboard)
st_autorefresh(interval=2000, key="datarefresh")

# ------------------------
# LOAD MODEL
# ------------------------
@st.cache_resource
def load_model():
    return YOLO("yolov8n.pt")

model = load_model()

# ------------------------
# GENERATE MACHINE DATA
# ------------------------
def generate_data():
    return {
        "vibration": random.randint(0, 100),
        "temperature": random.randint(25, 80)
    }

# ------------------------
# RISK CALCULATION
# ------------------------
def calculate_risk(helmet, distance, vibration):
    risk = 0
    reasons = []

    if not helmet:
        risk += 30
        reasons.append("No helmet detected")

    if distance < 30:
        risk += 40
        reasons.append("Worker too close to machine")

    if vibration > 70:
        risk += 35
        reasons.append("High machine vibration")

    return risk, reasons

def decision_logic(risk):
    if risk > 80:
        return "HIGH RISK", "STOP MACHINE"
    elif risk > 50:
        return "WARNING", "CHECK SYSTEM"
    else:
        return "SAFE", "NORMAL OPERATION"

# ------------------------
# UI
# ------------------------
st.title("🛡️ SmartSafe Co-Pilot Dashboard (Video AI)")

mode = st.sidebar.selectbox(
    "Demo Mode",
    ["Auto", "Force Safe", "Force Risk"]
)

uploaded_file = st.file_uploader("📹 Upload Video", type=["mp4", "mov", "avi"])

frame_placeholder = st.empty()

# ------------------------
# HISTORY
# ------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# ------------------------
# PROCESS VIDEO
# ------------------------
if uploaded_file:
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())

    cap = cv2.VideoCapture(tfile.name)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # YOLO detect
        results = model(frame)[0]
        annotated = results.plot()

        # หา person
        person_boxes = []
        for box in results.boxes:
            label = model.names[int(box.cls[0])]
            if label == "person":
                person_boxes.append(box)

        # ------------------------
        # Fake Helmet + Distance
        # ------------------------
        total_risk = 0
        reasons_all = []

        for i, box in enumerate(person_boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # helmet logic
            if mode == "Force Safe":
                helmet = True
            elif mode == "Force Risk":
                helmet = False
            else:
                helmet = (i % 2 == 0)

            # distance fake (ใช้ตำแหน่งแทน)
            distance = random.randint(10, 100)

            # machine data
            d = generate_data()

            risk, reasons = calculate_risk(helmet, distance, d["vibration"])
            total_risk += risk
            reasons_all.extend(reasons)

            # วาดกรอบ
            if helmet:
                color = (0, 255, 0)
                text = "Safe"
            else:
                color = (0, 0, 255)
                text = "No Helmet"

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.putText(annotated, text, (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # ------------------------
        # Dashboard
        # ------------------------
        if len(person_boxes) > 0:
            avg_risk = int(total_risk / len(person_boxes))
        else:
            avg_risk = 0

        status, action = decision_logic(avg_risk)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Worker Status")
            st.write(f"People detected: {len(person_boxes)}")

        with col2:
            st.subheader("Machine Status")
            st.write(f"Vibration: {d['vibration']}")
            st.write(f"Temperature: {d['temperature']} °C")

        with col3:
            st.subheader("Risk Analysis")
            st.metric("Risk Score", avg_risk)

            if status == "HIGH RISK":
                st.error(status)
            elif status == "WARNING":
                st.warning(status)
            else:
                st.success(status)

        st.subheader("AI Decision Support")
        st.write(f"Recommended Action: **{action}**")

        st.subheader("Explainable AI")
        for r in set(reasons_all):
            st.write(f"- {r}")

        # history
        st.session_state.history.append({"risk": avg_risk})
        df = pd.DataFrame(st.session_state.history)
        st.line_chart(df)

        # show video
        frame_placeholder.image(annotated, channels="BGR")

        time.sleep(0.05)

    cap.release()
