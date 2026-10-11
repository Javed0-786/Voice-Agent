# Aura Wellness Clinic: Autonomous AI Voice Concierge & Booking Agent

An end-to-end, real-time autonomous voice customer service agent built with **LiveKit WebRTC**, **Google Gemini Multimodal Live API**, and an interactive **SQLite database ledger**.

---

## 🌟 End-to-End System Architecture

```text
┌─────────────────────────────────┐
│       Modern Web Browser        │
│   (HTML5 / CSS / Vanilla JS)    │
│  - 1-Click "Start Call" Button  │
│  - Real-Time Audio Visualizer   │
│  - Live Data Channel Activity   │
│  - Real-Time Bookings Ledger    │
└───────────────▲─────────────────┘
                │ WebRTC Audio + LiveKit Data Channel
                ▼
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     LiveKit WebRTC Server       │◄─────►│    Gemini Voice Agent Worker    │
│    (ws://localhost:7880)        │       │           (agent.py)            │
│  Ultra-low latency SFU engine   │       │  Powered by Gemini Realtime     │
└───────────────▲─────────────────┘       └────────────────▲────────────────┘
                │                                          │ Function Calling
                │                                          ▼
┌───────────────▼─────────────────┐       ┌─────────────────────────────────┐
│    Web & API Server (server.py) │       │   SQLite Database (database.py) │
│     http://localhost:3000       │◄─────►│   - Services & Pricing          │
│  - Token Generator (/api/token) │       │   - Live Bookings Table         │
│  - Bookings API (/api/bookings) │       │   - Availability Slot Engine    │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

---

## 🚀 1-Click Quickstart

To launch the complete system (LiveKit server, Gemini voice agent, web dashboard, and browser window) all at once:

```powershell
.\start-all.ps1
```

This starts:
1. **LiveKit Server** on `ws://localhost:7880`
2. **Gemini Agent Worker** registered as default room agent
3. **Web Dashboard & Token Server** on `http://localhost:3000`
4. Automatically opens `http://localhost:3000` in your default browser!

---

## 🛠️ Individual Launch Commands (If Running Separately)

### 1. Terminal 1: LiveKit WebRTC Server
```powershell
.\start-livekit.ps1
```

### 2. Terminal 2: Gemini Voice Agent Worker
```powershell
.\start-agent.ps1
# or: python agent.py dev
```

### 3. Terminal 3: Web Dashboard & Token Server
```powershell
python server.py
```
Then visit **[http://localhost:3000](http://localhost:3000)** in your browser!

---

## 🧠 Autonomous Concierge Tools (Gemini Function Calling)

The agent (`Aura`) has 6 real-time database tools implemented with `@llm.function_tool`:

| Tool Name | Trigger Prompt Examples | Database Action | Data Channel Event |
| :--- | :--- | :--- | :--- |
| `get_clinic_services` | *"What treatments do you offer?"* / *"How much is a massage?"* | Queries `services` catalog with duration & pricing | `SERVICES_VIEWED` |
| `check_slot_availability` | *"Do you have any openings tomorrow?"* / *"Is 2 PM available?"* | Computes available hourly slots from 09:00 to 17:00 | `AVAILABILITY_CHECKED` |
| `book_appointment` | *"Book a facial therapy for John on 2026-10-15 at 11 AM"* | Inserts confirmed booking & returns `BK-XXXX` ref | `BOOKING_CREATED` |
| `lookup_appointment` | *"Can you check the status of my appointment BK-1001?"* | Searches by booking ID, customer name, or phone | `BOOKING_LOOKUP` |
| `reschedule_appointment`| *"Please reschedule BK-1001 to 2026-10-16 at 3 PM"* | Verifies slot availability & updates record | `BOOKING_RESCHEDULED` |
| `cancel_appointment` | *"I need to cancel booking BK-1002"* | Flags status as `CANCELLED` | `BOOKING_CANCELLED` |

---

## 💬 Sample Testing Dialogues

Once connected via the web UI at `http://localhost:3000`, try speaking these real-world scenarios into your microphone:

### Scenario A: Service Inquiries & Pricing
* **User**: *"Hi Aura, what kinds of services do you offer and what do they cost?"*
* **Aura**: *"We offer consultations, deep tissue massage, facial skin therapy, acupuncture, and chiropractic alignments starting at seventy-five dollars. Would you like details on any of these?"*

### Scenario B: Checking Availability & Booking
* **User**: *"Do you have any slots available tomorrow for a massage?"*
* **Aura**: *(Calls `check_slot_availability`)* *"Yes! Available slots for tomorrow are 9:00 AM, 10:00 AM, 11:00 AM, 1:00 PM, and 3:00 PM. Which time suits you best?"*
* **User**: *"Let's do 10:00 AM. My name is Mark Davis and my number is 555-0199."*
* **Aura**: *(Calls `book_appointment`)* *"Your appointment is confirmed! Your reference ID is BK-7412 for Mark Davis on tomorrow at 10:00 AM."*
* *(Notice: An event card slides into the Activity Feed and the Bookings Ledger updates instantly!)*

### Scenario C: Looking Up and Rescheduling
* **User**: *"Can you look up my existing booking BK-1001?"*
* **Aura**: *(Calls `lookup_appointment`)* *"I found your booking BK-1001 for Alex Turner for a Deep Tissue Massage tomorrow at 2:00 PM. How can I help with it?"*
* **User**: *"Could you reschedule that to 4:00 PM?"*
* **Aura**: *(Calls `reschedule_appointment`)* *"Done! Booking BK-1001 for Alex Turner is now rescheduled to tomorrow at 4:00 PM."*

### Scenario D: Cancellation
* **User**: *"I need to cancel my booking BK-1002."*
* **Aura**: *(Calls `cancel_appointment`)* *"Booking BK-1002 for Samantha Hayes has been cancelled. Let me know if there's anything else I can do for you."*

---

## 📁 Key File Structure

* [`agent.py`](./agent.py) — Voice AI Agent with Gemini Multimodal Live API & 6 autonomous database tools
* [`database.py`](./database.py) — SQLite persistent database with services, bookings, availability logic, and seed data
* [`server.py`](./server.py) — Lightweight Web & Token server providing `/api/token`, `/api/bookings`, and frontend hosting
* [`web/index.html`](./web/index.html) — Glassmorphic dashboard with 1-click calling orb, live feed, and database ledger
* [`web/styles.css`](./web/styles.css) — Modern dark theme styling, audio animations, and status pills
* [`web/app.js`](./web/app.js) — LiveKit client WebRTC connection, active speaker detection, and data channel sync
* [`start-all.ps1`](./start-all.ps1) — Single-command master launcher for the entire stack
