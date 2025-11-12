# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**ConvergenceLab Voice Assistant** - A real-time voice AI assistant for the Universidad de La Sabana's Convergence Lab, built with LiveKit Agents framework and Next.js.

The project consists of:
- **Backend**: Python-based LiveKit agent using OpenAI's real-time API
- **Frontend**: Next.js application with LiveKit React components for voice interaction

## Common Development Commands

### Backend (Python)

Navigate to `backend/` directory first.

**Setup:**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

**Running the agent:**
```powershell
# Main production agent (Sabius)
python agent.py dev

# Simple test agent
python simple_agent.py dev

# Enhanced agent with PURE integration
python enhanced_agent.py dev
```

**Environment configuration:**
Create `.env.local` in backend/ with:
- `OPENAI_API_KEY`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `LIVEKIT_URL`

### Frontend (Next.js)

Navigate to `frontend/` directory first.

**Setup:**
```powershell
# Install dependencies
pnpm install
```

**Development:**
```powershell
# Run development server
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start

# Lint code
pnpm lint
```

**Environment configuration:**
Create `.env.local` in frontend/ with:
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `LIVEKIT_URL`

## Architecture Overview

### Backend Architecture

**Agent System**: The backend uses LiveKit Agents framework with multiple agent implementations:

1. **agent.py** - Main production agent "Sabius"
   - Complete conversational AI for Convergence Lab
   - Extensive institutional knowledge embedded in instructions
   - Integrated with OpenAI GPT-4o real-time API
   - Silero VAD for voice activity detection

2. **simple_agent.py** - Minimal test agent
   - Basic functionality testing
   - Used for development/debugging

3. **enhanced_agent.py** - Extended agent with PURE integration
   - Adds research database context from Universidad de La Sabana's PURE system
   - Dynamic context loading capabilities

**Key Components:**

- **agent_timeout_config.py**: Centralized timeout configuration system
  - Configurable response timeouts (greeting, simple, complex, PURE queries)
  - VAD threshold and silence detection settings
  - Preset configurations: "instant", "fast", "balanced", "thorough"
  - OpenAI model configuration

- **Context Management** (when available):
  - `context_loader.py`: Loads and enhances agent context
  - `pure_*` files: Integration with PURE research database
  - `hybrid_context_builder.py`: Combines multiple context sources
  - `scraping_config.py` / `scrapfly_complete_scraper.py`: Web scraping utilities

**Agent Flow:**
1. Job received → Connect to room
2. Wait for participant
3. Initialize OpenAI realtime model with instructions
4. Create voice pipeline with STT/TTS
5. Start conversation loop
6. Handle user queries with contextual responses

### Frontend Architecture

**Framework**: Next.js 15 with App Router, TypeScript, and Tailwind CSS

**Key Components:**

- **app/page.tsx**: Main voice assistant interface
  - `SimpleVoiceAssistant`: Audio visualization with BarVisualizer
  - `ControlBar`: Connection controls and voice assistant controls
  - LiveKit room management and connection handling
  - Krisp noise filtering integration

- **app/api/connection-details/route.ts**: API endpoint for LiveKit authentication
  - Generates participant tokens
  - Creates random room names
  - Returns connection details for LiveKit client

- **components/**:
  - `CloseIcon.tsx`: Disconnect button icon
  - `NoAgentNotification.tsx`: User feedback when no agent is connected

**State Management:**
- Connection state (connected/disconnected)
- Agent state tracking (disconnected/connecting/listening/thinking/speaking)
- Media device failure handling

**UI/UX:**
- Framer Motion animations for smooth transitions
- Circular avatar image for agent representation
- Gradient button styling
- White background with branded footer

### Communication Flow

```
Frontend (Next.js) → API Route → LiveKit Server
                                      ↓
                                 Backend Agent (Python)
                                      ↓
                                 OpenAI Real-time API
```

1. User clicks connect → Frontend requests connection details
2. Frontend joins LiveKit room with participant token
3. Backend agent receives job → Connects to same room
4. Voice pipeline established: User ↔ Agent ↔ OpenAI
5. Real-time bidirectional audio streaming

## Important Notes

### Agent Configuration

The main agent (`agent.py`) contains extensive hardcoded institutional knowledge about:
- Convergence Lab mission, spaces, and access policies
- Universidad de La Sabana institutional information (2024 data)
- Faculty research groups and professors
- Entrepreneurship center details
- Historical research database (1980-2024)

**When modifying agent instructions:**
- The full context is embedded in the `GovLabAssistant` class constructor
- Timeout configurations should be adjusted via `agent_timeout_config.py`
- Do not modify timeouts directly in agent code

### LiveKit Integration

- Uses LiveKit Agents SDK version 0.8.0+
- OpenAI plugin for GPT-4o-realtime-preview model
- Silero plugin for VAD (Voice Activity Detection)
- Real-time voice pipeline with automatic STT/TTS

### Deployment

**Frontend:**
- GitHub Actions workflow: `.github/workflows/sync-to-production.yaml`
- Syncs `main` branch to `sandbox-production` branch on push
- Deployed via LiveKit Sandbox (referenced in frontend README)

**Backend:**
- Runs as LiveKit worker
- Must be running before frontend can connect
- Accepts jobs for specific room names

### Development Workflow

1. Start backend agent first: `python agent.py dev`
2. In separate terminal, start frontend: `pnpm dev`
3. Open http://localhost:3000
4. Click connect button to start voice interaction
5. Agent logs appear in backend terminal
6. Frontend shows connection status and audio visualizer

### Testing

**Backend:**
- Use `simple_agent.py` for basic connectivity tests
- Check logs for job acceptance and room connections
- Verify environment variables are loaded

**Frontend:**
- Test microphone permissions
- Verify LiveKit connection establishment
- Check audio visualization during speech
- Test disconnect/reconnect flows

## File Structure Highlights

```
ConvergenceLab/
├── backend/
│   ├── agent.py                    # Main production agent
│   ├── simple_agent.py             # Test agent
│   ├── enhanced_agent.py           # Agent with PURE integration
│   ├── agent_timeout_config.py     # Timeout configuration
│   ├── requirements.txt            # Python dependencies
│   └── .env.local                  # Environment variables (not in git)
│
└── frontend/
    ├── app/
    │   ├── page.tsx                # Main UI page
    │   ├── layout.tsx              # Root layout
    │   ├── globals.css             # Global styles
    │   └── api/
    │       └── connection-details/
    │           └── route.ts        # LiveKit auth endpoint
    ├── components/
    │   ├── CloseIcon.tsx           # UI component
    │   └── NoAgentNotification.tsx # UI component
    ├── package.json                # Node dependencies
    ├── next.config.mjs             # Next.js config
    ├── tailwind.config.ts          # Tailwind config
    ├── tsconfig.json               # TypeScript config
    └── .env.local                  # Environment variables (not in git)
```

## Troubleshooting

**Agent not connecting:**
- Verify LIVEKIT_API_KEY and LIVEKIT_API_SECRET match between backend and frontend
- Check LIVEKIT_URL is accessible
- Ensure agent is running before frontend connection attempt

**Voice not working:**
- Grant microphone permissions in browser
- Check Krisp noise filter compatibility (Scale plan feature)
- Verify OpenAI API key has access to real-time API

**Timeout issues:**
- Adjust settings in `agent_timeout_config.py`
- Use preset configurations: `PRESET_CONFIGS["fast"]` or `"balanced"`
- Check VAD_THRESHOLD and SILENCE_DURATION_MS values
