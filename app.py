import streamlit as st
import json
import os
from datetime import datetime
import qrcode
from PIL import Image
import io

# ---------------- CONFIG ---------------- #
DATA_FILE = "reservations.json"
WATERMARK = "athxsec"

st.set_page_config(page_title="🚌 Smart Bus Reservation", page_icon="🚌", layout="wide")

st.markdown(
    """
    <style>
        /* --- (All your awesome CSS is in here) --- */
        body {
            background: linear-gradient(135deg, #2e1a47, #5a3e85);
            color: #ddd;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .block-container {
            padding-top: 2rem;
        }
        h1, h2, h3, h4 {
            color: #d1b3ff;
        }
        .seat-btn {
            border-radius: 6px;
            font-weight: bold;
            width: 40px;
            height: 40px;
            text-align: center;
            line-height: 40px;
            cursor: pointer;
            user-select: none;
            margin: 3px;
            border: none;
            transition: filter 0.2s ease;
        }
        .seat-available {
            background-color: #28a745; /* Green */
            color: white;
        }
        .seat-booked {
            background-color: #dc3545; /* Red */
            color: white;
            cursor: not-allowed;
        }
        .seat-available:hover {
            filter: brightness(1.2); /* Glow on hover */
        }
        .athx-watermark {
            position: fixed;
            bottom: 5px;
            right: 10px;
            opacity: 0.3;
            font-size: 12px;
            color: #bbaaff;
            font-weight: 600;
            user-select: none;
            pointer-events: none;
        }
        .stTabs [role="tablist"] button[aria-selected="true"] {
            background-color: #7b5fcf !important;
            color: white !important;
            font-weight: 700 !important;
        }
        .stTabs [role="tablist"] button {
            background-color: #4a2e7e !important;
            color: #ccc !important;
        }
        .stButton>button {
            background-color: #7b5fcf;
            color: white;
            border-radius: 6px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 600;
        }
        .stButton>button:hover {
            background-color: #9a7fe0;
            color: white;
        }
        .stTextInput>div>input, .stNumberInput>div>input {
            background-color: #4a2e7e;
            color: #eee;
            border-radius: 6px;
            border: 1px solid #7b5fcf;
            padding: 0.3rem 0.5rem;
        }
        .stTextInput>div>input::placeholder {
            color: #bbaaff;
        }
        .stNumberInput>div>input::-webkit-inner-spin-button,
        .stNumberInput>div>input::-webkit-outer-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }
    </style>
    
    <h1 style='text-align:center; margin-bottom:0.2rem;'>🚌 Smart Bus Reservation System</h1>
    <hr style="border-color:#7b5fcf; margin-top:0rem; margin-bottom:1rem;">
    """,
    unsafe_allow_html=True
)

# ---------------- DATA MODEL ---------------- #
class Bus:
    def __init__(self, bus_id, route, rows, seats_per_row, price_per_seat):
        self.bus_id = bus_id
        self.route = route
        self.rows = rows
        self.seats_per_row = seats_per_row
        self.price_per_seat = price_per_seat
        self.seats = [["O" for _ in range(seats_per_row)] for _ in range(rows)]
        self.available_seats = rows * seats_per_row

# ---------------- UTILITIES ---------------- #
def load_reservations():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_reservations(reservations):
    with open(DATA_FILE, "w") as f:
        json.dump(reservations, f, indent=4)

def generate_qr_image(data):
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

# ---------------- SESSION SETUP ---------------- #
if "buses" not in st.session_state:
    st.session_state.buses = [
        Bus("B1", "Kolhapur → Mumbai", 5, 4, 300),
        Bus("B2", "Nagpur → Sangli", 5, 4, 350),
        Bus("B3", "Pune → Bangalore", 5, 4, 400),
        Bus("B4", "Delhi → Chandigarh", 5, 4, 250),
    ]

if "reservations" not in st.session_state:
    st.session_state.reservations = load_reservations()
    for det in st.session_state.reservations.values():
        bus = next((b for b in st.session_state.buses if b.bus_id == det["bus_id"]), None)
        if bus:
            bus.seats[det["row"]][det["seat"]] = "X"
            bus.available_seats -= 1

# For seat selection in reservation tab
if "selected_seat" not in st.session_state:
    st.session_state.selected_seat = None
if "selected_bus_idx" not in st.session_state:
    st.session_state.selected_bus_idx = 0

# ---------------- TABS ---------------- #
tabs = st.tabs(["🚌 View Buses", "🎫 Make Reservation", "📊 Dashboard", "❌ Cancel Reservation", "📋 Show Reservations", "⚙️ Admin Panel"])

# ---------------- VIEW BUSES ---------------- #
with tabs[0]:
    st.subheader("Available Buses")
    for bus in st.session_state.buses:
        total_seats = bus.rows * bus.seats_per_row
        booked = total_seats - bus.available_seats
        percent = booked / total_seats
        st.markdown(f"### {bus.bus_id} - {bus.route}")
        st.progress(percent)
        st.caption(f"Seats Left: {bus.available_seats} | Price: ₹{bus.price_per_seat}")

# ---------------- MAKE RESERVATION ---------------- #
with tabs[1]:
    st.subheader("Reserve Your Seat")

    bus_options = [f"{b.bus_id} - {b.route}" for b in st.session_state.buses]
    selected_bus_index = st.selectbox("Select Bus", range(len(bus_options)), format_func=lambda x: bus_options[x], index=st.session_state.selected_bus_idx)
    bus = st.session_state.buses[selected_bus_index]
    st.session_state.selected_bus_idx = selected_bus_index

    st.markdown(f"**Route:** {bus.route} | **Price per seat:** ₹{bus.price_per_seat}")
    st.markdown("### Seat Layout (Click to select)")

    seat_selected = st.session_state.selected_seat

    cols_per_row = bus.seats_per_row
    for r in range(bus.rows):
        cols = st.columns(cols_per_row)
        for c in range(cols_per_row):
            seat_status = bus.seats[r][c]
            btn_key = f"seat_{r}_{c}"
            if seat_status == "O":
                is_selected = seat_selected == (r, c)
                btn_label = f"{r+1}-{c+1}"
                btn_style = "seat-btn seat-available"
                if is_selected:
                    # Highlight selected seat
                    btn_style += " style='box-shadow: 0 0 8px 3px #d1b3ff;'"
                clicked = cols[c].button(btn_label, key=btn_key, help="Available seat")
                if clicked:
                    st.session_state.selected_seat = (r, c)
            else:
                # Booked seat
                cols[c].button(f"{r+1}-{c+1}", key=btn_key, disabled=True, help="Booked seat", args=None)

    with st.form("reservation_form"):
        name = st.text_input("Your Name")
        if seat_selected:
            row_num, seat_num = seat_selected
            st.markdown(f"Selected Seat: Row {row_num+1}, Seat {seat_num+1}")
        else:
            st.markdown("Selected Seat: None")

        submitted = st.form_submit_button("Reserve Seat 🚀")

        if submitted:
            if not name.strip():
                st.error("⚠️ Please enter your name.")
            elif seat_selected is None:
                st.error("⚠️ Please select a seat by clicking on an available seat.")
            else:
                r_idx, s_idx = seat_selected
                if bus.seats[r_idx][s_idx] == "X":
                    st.error("❌ That seat is already booked.")
                else:
                    res_id = f"{bus.bus_id}_{r_idx}_{s_idx}_{int(datetime.now().timestamp())}"
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    det = {
                        "name": name.strip(),
                        "bus_id": bus.bus_id,
                        "route": bus.route,
                        "row": r_idx,
                        "seat": s_idx,
                        "time": timestamp
                    }
                    st.session_state.reservations[res_id] = det
                    bus.seats[r_idx][s_idx] = "X"
                    bus.available_seats -= 1
                    save_reservations(st.session_state.reservations)

                    st.success(f"✅ Seat {r_idx+1}-{s_idx+1} reserved for **{name}**!")
                    st.markdown("### Reservation Confirmation")
                    st.write(f"**Reservation ID:** `{res_id}`")
                    st.write(f"**Bus ID:** {bus.bus_id}")
                    st.write(f"**Route:** {bus.route}")
                    st.write(f"**Seat:** Row {r_idx+1}, Seat {s_idx+1}")
                    st.write(f"**Passenger Name:** {name.strip()}")
                    st.write(f"**Timestamp:** {timestamp}")

                    qr_img = generate_qr_image(res_id)
                    buf = io.BytesIO()
                    qr_img.save(buf, format="PNG")
                    buf.seek(0)
                    st.image(buf, caption="Reservation QR Code", use_column_width=False)

                    st.session_state.selected_seat = None

# ---------------- DASHBOARD ---------------- #
with tabs[2]:
    st.subheader("Bus Occupancy Dashboard")
    for bus in st.session_state.buses:
        total_seats = bus.rows * bus.seats_per_row
        booked = total_seats - bus.available_seats
        percent = booked / total_seats
        st.markdown(f"#### {bus.route}")
        st.progress(percent)
        st.caption(f"{booked} / {total_seats} seats booked")

# ---------------- CANCEL RESERVATION ---------------- #
with tabs[3]:
    st.subheader("Cancel Reservation")
    rid = st.text_input("Enter Reservation ID to cancel")
    if st.button("Cancel ❌"):
        if rid in st.session_state.reservations:
            det = st.session_state.reservations[rid]
            bus = next((b for b in st.session_state.buses if b.bus_id == det["bus_id"]), None)
            if bus:
                bus.seats[det["row"]][det["seat"]] = "O"
                bus.available_seats += 1
            del st.session_state.reservations[rid]
            save_reservations(st.session_state.reservations)
            st.success(f"✅ Reservation `{rid}` cancelled successfully!")
        else:
            st.error("⚠️ Invalid Reservation ID!")

# ---------------- SHOW RESERVATIONS ---------------- #
with tabs[4]:
    st.subheader("All Reservations")
    if not st.session_state.reservations:
        st.info("No reservations yet.")
    else:
        for rid, det in st.session_state.reservations.items():
            st.write(
                f"🆔 **{rid}** | 👤 {det['name']} | 🚌 {det['bus_id']} | "
                f"📍 {det['route']} | 💺 Row {det['row']+1}, Seat {det['seat']+1} | 🕒 {det['time']}"
            )

# ---------------- ADMIN PANEL ---------------- #
with tabs[5]:
    st.subheader("Admin Controls")
    if st.button("🧹 Clear All Reservations"):
        st.session_state.reservations = {}
        save_reservations({})
        for bus in st.session_state.buses:
            bus.seats = [["O" for _ in range(bus.seats_per_row)] for _ in range(bus.rows)]
            bus.available_seats = bus.rows * bus.seats_per_row
        st.warning("All reservations cleared.")
    st.caption("⚠️ Admin-only operation.")

# ---------------- WATERMARK ---------------- #
st.markdown(f"<div class='athx-watermark'>{WATERMARK}</div>", unsafe_allow_html=True)
