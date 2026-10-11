import os
import json
import logging
import asyncio
from datetime import date
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import Agent, AgentServer, AgentSession, llm
from livekit.plugins import google
import database

load_dotenv()
logger = logging.getLogger("aura-agent")
server = AgentServer()

@server.rtc_session()
async def gemini_talk_agent(ctx: agents.JobContext):
    print(f"\n[Aura Agent] === Received job assignment for room: {ctx.room.name} ===")
    print("[Aura Agent] Connecting to WebRTC room...")
    await ctx.connect()
    print(f"[Aura Agent] Connected to {ctx.room.name}! Initializing Gemini Live model...")
    today_str = date.today().strftime("%Y-%m-%d")

    async def broadcast_event(event_name: str, payload: dict):
        """Broadcast live event over LiveKit data channel for the web dashboard."""
        try:
            msg = json.dumps({"event": event_name, "payload": payload, "timestamp": today_str})
            await ctx.room.local_participant.publish_data(msg, topic="clinic_updates")
            logger.info(f"Broadcasted event {event_name}: {payload}")
        except Exception as e:
            logger.warning(f"Could not broadcast event {event_name}: {e}")

    # =========================================================================
    # TOOL DEFINITIONS FOR AUTONOMOUS CUSTOMER SERVICE & BOOKING
    # =========================================================================

    @llm.function_tool
    async def get_clinic_services() -> str:
        """Retrieve the official list of wellness and clinic services, durations, and pricing.
        Use this when a customer asks about what services we offer or how much they cost.
        """
        services = database.get_services()
        summary = []
        for s in services:
            summary.append(f"- {s['name']} (${s['price']:.0f}, {s['duration_minutes']} mins): {s['description']}")
        
        await broadcast_event("SERVICES_VIEWED", {"count": len(services)})
        return "Available Services:\n" + "\n".join(summary)

    @llm.function_tool
    async def check_slot_availability(service_name: str, booking_date: str) -> str:
        """Check available time slots for a specific date (YYYY-MM-DD format).
        Use this before booking or when a caller asks what times are open on a certain day.
        """
        slots = database.check_availability(service_name, booking_date)
        await broadcast_event("AVAILABILITY_CHECKED", {
            "service": service_name,
            "date": booking_date,
            "available_slots": slots
        })
        if not slots:
            return f"I'm sorry, all appointment slots on {booking_date} are fully booked. Would you like to check another date?"
        return f"On {booking_date}, available slots are: {', '.join(slots)}."

    @llm.function_tool
    async def book_appointment(
        customer_name: str,
        customer_phone: str,
        service_name: str,
        booking_date: str,
        booking_time: str
    ) -> str:
        """Book and confirm an appointment.
        Call this when you have collected the customer's name, phone, service, date, and time slot.
        """
        res = database.create_booking(
            customer_name=customer_name,
            customer_phone=customer_phone,
            service_name=service_name,
            booking_date=booking_date,
            booking_time=booking_time
        )
        if not res.get("success"):
            return res.get("error", "Failed to book appointment.")

        await broadcast_event("BOOKING_CREATED", res)
        return (
            f"Appointment confirmed! Booking Reference ID is {res['booking_id']} for "
            f"{customer_name} - {service_name} on {booking_date} at {booking_time}."
        )

    @llm.function_tool
    async def lookup_appointment(search_query: str) -> str:
        """Look up an existing appointment by Booking ID (e.g., 'BK-1001') or customer phone number or customer name.
        Use this when a caller wants to check their booking status, reschedule, or cancel.
        """
        booking = database.lookup_booking(search_query)
        if not booking:
            return f"No appointment found matching '{search_query}'. Please verify your Booking ID or registered phone number."

        await broadcast_event("BOOKING_LOOKUP", booking)
        return (
            f"Found booking {booking['id']} for {booking['customer_name']} "
            f"({booking['service_name']}) on {booking['booking_date']} at {booking['booking_time']}. "
            f"Current status: {booking['status']}."
        )

    @llm.function_tool
    async def reschedule_appointment(booking_id: str, new_date: str, new_time: str) -> str:
        """Reschedule an existing booking to a new date and time slot.
        Always confirm the customer's Booking ID before calling this.
        """
        res = database.reschedule_booking(booking_id, new_date, new_time)
        if not res.get("success"):
            return res.get("error", "Failed to reschedule booking.")

        await broadcast_event("BOOKING_RESCHEDULED", res)
        return (
            f"Booking {booking_id} has been successfully rescheduled to {new_date} at {new_time} "
            f"for {res['customer_name']}."
        )

    @llm.function_tool
    async def cancel_appointment(booking_id: str) -> str:
        """Cancel an existing appointment by Booking ID.
        Call this when the customer explicitly asks to cancel an appointment.
        """
        res = database.cancel_booking(booking_id)
        if not res.get("success"):
            return res.get("error", "Failed to cancel booking.")

        await broadcast_event("BOOKING_CANCELLED", res)
        return f"Booking {booking_id} for {res['customer_name']} has been cancelled."

    # =========================================================================
    # VOICE MODEL & SESSION SETUP
    # =========================================================================

    instructions = (
        "You are Aura, the voice AI concierge for Aura Wellness & Health Clinic. "
        "You speak with clients naturally over a live phone-like voice connection. "
        f"Today's date is {today_str}. "
        "Your role: assist callers with booking appointments, checking available hours, looking up existing bookings, "
        "rescheduling, and cancelling appointments. "
        "Guidelines: "
        "- Speak warmly, professionally, and concisely (1-2 sentences per turn). "
        "- Do not recite long lists; summarize key options and ask how they'd like to proceed. "
        "- When booking: ask for their preferred date and service, check availability using check_slot_availability, "
        "then ask for their name and phone number to finalize using book_appointment. "
        "- When rescheduling or cancelling: look up the booking first using lookup_appointment, confirm details with the user, "
        "then execute the requested action. "
        "- Always be polite and reassuring."
    )

    realtime_model = google.realtime.RealtimeModel(
        voice="Puck",
        instructions=instructions,
    )

    session = AgentSession(
        llm=realtime_model,
    )

    agent_tools = [
        get_clinic_services,
        check_slot_availability,
        book_appointment,
        lookup_appointment,
        reschedule_appointment,
        cancel_appointment
    ]

    await session.start(
        agent=Agent(
            instructions=instructions,
            tools=agent_tools,
        ),
        room=ctx.room,
    )

    # Initial greeting to the caller
    await session.generate_reply(
        instructions="Say hello warmly to the caller, introduce yourself as Aura from Aura Wellness Clinic, and ask how you can help them today."
    )

if __name__ == "__main__":
    agents.cli.run_app(server)
