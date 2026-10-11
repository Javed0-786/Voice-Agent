// Aura Wellness Voice Concierge Frontend
// Integrated with LiveKit WebRTC and Gemini Live Data Channel

let currentRoom = null;
let callStartTime = null;
let timerInterval = null;
let isMuted = false;

// DOM Elements
const callBtn = document.getElementById('callBtn');
const callBtnText = document.getElementById('callBtnText');
const muteBtn = document.getElementById('muteBtn');
const muteBtnText = document.getElementById('muteBtnText');
const avatarContainer = document.getElementById('avatarContainer');
const statusHeading = document.getElementById('statusHeading');
const statusDesc = document.getElementById('statusDesc');
const callTimer = document.getElementById('callTimer');
const activityFeed = document.getElementById('activityFeed');
const emptyFeed = document.getElementById('emptyFeed');
const bookingsTableBody = document.getElementById('bookingsTableBody');
const bookingCount = document.getElementById('bookingCount');
const refreshBtn = document.getElementById('refreshBtn');
const remoteAudio = document.getElementById('remoteAudio');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    fetchBookings();
    
    callBtn.addEventListener('click', toggleCall);
    muteBtn.addEventListener('click', toggleMute);
    refreshBtn.addEventListener('click', fetchBookings);
});

// Format call timer
function updateTimer() {
    if (!callStartTime) return;
    const elapsedSec = Math.floor((Date.now() - callStartTime) / 1000);
    const mins = String(Math.floor(elapsedSec / 60)).padStart(2, '0');
    const secs = String(elapsedSec % 60).padStart(2, '0');
    callTimer.textContent = `${mins}:${secs}`;
}

async function toggleCall() {
    if (currentRoom) {
        await disconnectCall();
    } else {
        await startCall();
    }
}

async function startCall() {
    try {
        callBtn.disabled = true;
        callBtnText.textContent = 'Connecting...';
        statusHeading.textContent = 'Connecting to Concierge...';
        statusDesc.textContent = 'Securing encrypted WebRTC media session with LiveKit server...';

        // 1. Fetch token from server API
        const tokenRes = await fetch('/api/token');
        if (!tokenRes.ok) throw new Error('Failed to fetch LiveKit access token from backend.');
        const tokenData = await tokenRes.json();

        // 2. Initialize LiveKit Room
        const { Room, RoomEvent } = LivekitClient;
        const room = new Room({
            adaptiveStream: true,
            dynacast: true,
            audioCaptureDefaults: {
                autoGainControl: true,
                echoCancellation: true,
                noiseSuppression: true,
            }
        });

        // 3. Set up event listeners with detailed logging
        addEventCard('default', {
            title: 'Connecting Signal',
            message: `Initiating WebRTC handshake with ${tokenData.url} for room ${tokenData.room}...`
        });

        room.on(RoomEvent.Connected, () => {
            addEventCard('created', {
                title: 'WebRTC Room Connected',
                message: `Joined ${tokenData.room} as ${tokenData.identity}. Waiting for AI agent to join...`
            });
        });

        room.on(RoomEvent.ParticipantConnected, (participant) => {
            addEventCard('created', {
                title: 'Participant Joined Room',
                message: `Identity: ${participant.identity} (${participant.name || 'AI Worker'})`
            });
            if (participant.identity.startsWith('agent-') || participant.identity.includes('agent')) {
                statusHeading.textContent = 'Aura Connected';
                statusDesc.textContent = 'AI Concierge joined the room. Speak or listen now.';
            }
        });

        room.on(RoomEvent.ParticipantDisconnected, (participant) => {
            addEventCard('cancelled', {
                title: 'Participant Left',
                message: `Identity: ${participant.identity} has disconnected from the room.`
            });
            if (participant.identity.startsWith('agent-') || participant.identity.includes('agent')) {
                statusHeading.textContent = 'Agent Disconnected';
                statusDesc.textContent = 'The AI agent exited the room. Check your agent worker terminal logs.';
            }
        });

        room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
            if (track.kind === 'audio') {
                track.attach(remoteAudio);
                statusHeading.textContent = 'Aura Connected & Ready';
                statusDesc.textContent = 'Speak naturally to inquire, book, check slots, or manage appointments.';
                addEventCard('availability', {
                    title: 'Audio Track Attached',
                    message: `Subscribed to live audio from ${participant.identity}. AI is ready to talk!`
                });
            }
        });

        room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
            const isAgentSpeaking = speakers.some(s => s.identity.startsWith('agent-') || s.name === 'gemini-talk-agent');
            if (isAgentSpeaking) {
                avatarContainer.classList.add('speaking');
                statusHeading.textContent = 'Aura is speaking...';
            } else {
                avatarContainer.classList.remove('speaking');
                if (currentRoom) {
                    statusHeading.textContent = 'Listening to you...';
                }
            }
        });

        // Listen for live database events published by Gemini tools
        room.on(RoomEvent.DataReceived, (payload, participant, kind, topic) => {
            try {
                const text = new TextDecoder().decode(payload);
                const data = JSON.parse(text);
                handleAgentEvent(data);
            } catch (err) {
                console.error('Error decoding data channel message:', err);
            }
        });

        room.on(RoomEvent.Disconnected, (reason) => {
            addEventCard('cancelled', {
                title: 'Call Disconnected',
                message: `Session closed (${reason || 'user disconnected'})`
            });
            resetCallUI();
        });

        // 4. Connect to server
        let wsUrl = tokenData.url;
        if (window.location.hostname === 'localhost' && wsUrl.includes('127.0.0.1')) {
            wsUrl = wsUrl.replace('127.0.0.1', 'localhost');
        } else if (window.location.hostname === '127.0.0.1' && wsUrl.includes('localhost')) {
            wsUrl = wsUrl.replace('localhost', '127.0.0.1');
        }
        await room.connect(wsUrl, tokenData.token);
        
        // 5. Enable microphone
        await room.localParticipant.setMicrophoneEnabled(true);

        currentRoom = room;
        callStartTime = Date.now();
        timerInterval = setInterval(updateTimer, 1000);

        // Update UI to in-call state
        avatarContainer.classList.add('active');
        callBtn.disabled = false;
        callBtn.classList.add('hangup');
        callBtnText.textContent = 'End Voice Call';
        muteBtn.disabled = false;
        callTimer.style.display = 'inline-block';
        statusHeading.textContent = 'Connected • Listening';
        statusDesc.textContent = 'Say: "What services do you offer?" or "Book a massage for tomorrow at 2 PM"';

        addEventCard('SESSION_CONNECTED', {
            title: 'Call Established',
            message: `Connected to Aura Clinic Voice Room (${tokenData.room})`
        });

    } catch (err) {
        console.error('Call connection error:', err);
        statusHeading.textContent = 'Connection Error';
        statusDesc.textContent = err.message || 'Could not connect. Ensure LiveKit and Agent are running.';
        callBtn.disabled = false;
        callBtnText.textContent = 'Start Voice Call';
    }
}

async function disconnectCall() {
    if (currentRoom) {
        await currentRoom.disconnect();
        currentRoom = null;
    }
    resetCallUI();
}

function resetCallUI() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    callStartTime = null;
    currentRoom = null;
    isMuted = false;

    avatarContainer.classList.remove('active', 'speaking');
    callBtn.disabled = false;
    callBtn.classList.remove('hangup');
    callBtnText.textContent = 'Start Voice Call';
    muteBtn.disabled = true;
    muteBtn.classList.remove('muted');
    muteBtnText.textContent = 'Mute';
    callTimer.style.display = 'none';
    statusHeading.textContent = 'Call Ended';
    statusDesc.textContent = 'Ready for another session. Click below to reconnect.';
}

async function toggleMute() {
    if (!currentRoom) return;
    isMuted = !isMuted;
    await currentRoom.localParticipant.setMicrophoneEnabled(!isMuted);
    
    if (isMuted) {
        muteBtn.classList.add('muted');
        muteBtnText.textContent = 'Unmute';
    } else {
        muteBtn.classList.remove('muted');
        muteBtnText.textContent = 'Mute';
    }
}

// Handle Real-time Tool Events
function handleAgentEvent(data) {
    const { event, payload } = data;
    if (emptyFeed) emptyFeed.style.display = 'none';

    let cardType = 'default';
    let title = event;
    let message = '';

    if (event === 'BOOKING_CREATED') {
        cardType = 'created';
        title = `Appointment Confirmed (${payload.booking_id})`;
        message = `${payload.customer_name} • ${payload.service_name} on ${payload.booking_date} at ${payload.booking_time}`;
        fetchBookings(); // Auto refresh database table
    } else if (event === 'BOOKING_RESCHEDULED') {
        cardType = 'rescheduled';
        title = `Rescheduled: ${payload.booking_id}`;
        message = `${payload.customer_name} moved to ${payload.new_date} at ${payload.new_time}`;
        fetchBookings();
    } else if (event === 'BOOKING_CANCELLED') {
        cardType = 'cancelled';
        title = `Cancelled: ${payload.booking_id}`;
        message = `Appointment for ${payload.customer_name} has been cancelled.`;
        fetchBookings();
    } else if (event === 'AVAILABILITY_CHECKED') {
        cardType = 'availability';
        title = `Checked Availability (${payload.date})`;
        message = `Available Slots: ${payload.available_slots.join(', ') || 'Fully Booked'}`;
    } else if (event === 'BOOKING_LOOKUP') {
        title = `Lookup: ${payload.id}`;
        message = `${payload.customer_name} (${payload.service_name}) on ${payload.booking_date} @ ${payload.booking_time} [${payload.status}]`;
    } else if (event === 'SERVICES_VIEWED') {
        title = 'Services Queried';
        message = `Consulted clinic catalog (${payload.count} treatments available)`;
    }

    addEventCard(cardType, { title, message });
}

function addEventCard(cardType, { title, message }) {
    if (emptyFeed) emptyFeed.style.display = 'none';

    const card = document.createElement('div');
    card.className = `event-card ${cardType}`;
    card.innerHTML = `
        <div class="event-top">
            <span class="event-title">${title}</span>
            <span style="color: var(--text-muted); font-size: 0.75rem;">${new Date().toLocaleTimeString()}</span>
        </div>
        <div class="event-body">${message}</div>
    `;

    activityFeed.prepend(card);
}

// Fetch database records
async function fetchBookings() {
    try {
        const res = await fetch('/api/bookings');
        if (!res.ok) throw new Error('Failed to fetch bookings');
        const data = await res.json();
        renderBookingsTable(data.bookings || []);
    } catch (err) {
        console.error('Error fetching bookings:', err);
    }
}

function renderBookingsTable(bookings) {
    bookingCount.textContent = `${bookings.length} Bookings`;
    bookingsTableBody.innerHTML = '';

    if (bookings.length === 0) {
        bookingsTableBody.innerHTML = `<tr><td colspan="7" class="loading-td">No appointments registered yet.</td></tr>`;
        return;
    }

    bookings.forEach(b => {
        const tr = document.createElement('tr');
        const statusClass = b.status.toLowerCase();

        tr.innerHTML = `
            <td class="booking-ref">${b.id}</td>
            <td style="font-weight: 600; color: var(--text-primary);">${b.customer_name}</td>
            <td>${b.customer_phone}</td>
            <td>${b.service_name}</td>
            <td>${b.booking_date}</td>
            <td>${b.booking_time}</td>
            <td><span class="status-badge ${statusClass}">${b.status}</span></td>
        `;
        bookingsTableBody.appendChild(tr);
    });
}
