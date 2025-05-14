# GigPlus Conversational Simulator

A training and evaluation tool for GigPlus, designed to enhance agent performance during client interactions through realistic conversation simulations with AI-driven customers.

## 📋 Project Overview

GigPlus Conversational Simulator helps agents practice and improve their client interaction skills by:

- Simulating realistic customer conversations
- Providing detailed feedback on agent performance
- Identifying strengths, weaknesses, and missed opportunities
- Tracking improvement over time

## 🏗️ Project Structure

```
multi-agent/
├── backend/               # FastAPI backend
│   ├── main.py            # API endpoints and core logic
│   ├── agents/            # AI conversation agents (customer, evaluator)
│   ├── utils/             # Supabase services, helpers
│   └── requirements.txt   # Python dependencies
├── frontend-react/        # React frontend
│   ├── src/               # React components and logic
│   │   ├── components/    # UI components (HomePage, ChatPage, FeedbackPage)
│   │   └── lib/           # Utilities and service connections
│   └── package.json       # Frontend dependencies
├── Makefile               # Build and run commands
├── .env.example           # Example environment variables
└── .gitignore             # Files to ignore in version control
```

## 🚀 Key Features

- **Scenario-Based Conversations**: Simulates real client interactions with dynamic context
- **Voice Integration**: Speak to the virtual client and hear their responses
- **Phase-Based Conversations**: Simulations follow structured phases of a sales/support conversation
- **Detailed Feedback**: Get scored on performance with specific improvement suggestions
- **Supabase Integration**: Stores conversation scenarios, phases, and evaluation criteria

## 🛠️ Technology Stack

### Backend
- **Python 3.11+** with **FastAPI**
- **Azure OpenAI** for conversation agents (via `openai` Python client)
- **Supabase** for database and authentication

### Frontend  
- **React 19** with functional components
- **Azure Speech SDK** for text-to-speech and speech-to-text
- **React Router** for navigation
- **Chart.js** for feedback visualizations

## 🔧 Environment Setup

### Required Environment Variables

Create a `.env` file in the root directory with:

```bash
# # Backend (create in backend/.env)
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini  # or your deployment name

SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-key

# Frontend (create in frontend-react/.env)
REACT_APP_SUPABASE_URL=https://your-project-id.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-supabase-anon-key
REACT_APP_SPEECH_KEY=your-azure-speech-key
REACT_APP_SPEECH_REGION=westeurope  # or your region
```

## 🗄️ Database Structure

GigPlus Simulator uses Supabase with the following structure:

1. **scenarios** table
   - `id`: Unique identifier
   - `name`: Scenario name
   - `description`: Brief description
   - `context`: Detailed context information for the conversation
   - `initial_prompt`: Starting message from the customer

2. **phases** table
   - `id`: Unique identifier
   - `scenario_id`: Reference to parent scenario
   - `name`: Phase name (e.g., "Introduction", "Discovery", "Closing")
   - `system_prompt`: System prompt for the AI during this phase
   - `on_success`: Next phase on success
   - `on_failure`: Next phase on failure

3. **aspects** table
   - `id`: Unique identifier
   - `phase_id`: Reference to parent phase
   - `name`: Aspect description
   - `type`: One of "critical", "optional", or "red_flag"

## 📥 Installation and Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Make

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nachogutii/multi-agent.git
   cd multi-agent
   ```

2. **Set up environment variables**
   ```bash
   # Copy the example env file and edit with your credentials
   cp .env.example .env
   nano .env  # Add your credentials
   ```

3. **Install dependencies**
   ```bash
   make install
   ```
   This installs both backend and frontend dependencies.

## ▶️ Running the Application

### Development Mode

```bash
# Run both backend and frontend together
make start

# Or run them separately
make run-backend
make run-frontend
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### Production Build

```bash
make build
```

## 🔄 Application Flow

1. **Login**: Users authenticate with Supabase
2. **Scenario Selection**: Choose from available conversation scenarios
3. **Conversation**: Interact with the virtual customer
4. **Feedback**: View detailed performance evaluation

## 📊 Evaluation System

The Observer Agent evaluates conversations based on:
- Critical aspects (must address)
- Optional aspects (good to address)
- Red flags (should avoid)

Each aspect is tracked during the conversation, contributing to an overall score.

## 🌐 Deployment

### Backend Deployment (Render)
1. Create a new Web Service
2. Connect to your GitHub repository
3. Set build command: `pip install -r backend/requirements.txt`
4. Set start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables

### Frontend Deployment (Netlify)
1. Connect to your GitHub repository
2. Set build command: `cd frontend-react && npm install && npm run build`
3. Set publish directory: `frontend-react/build`
4. Add environment variables

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch: `git checkout -b new-feature`
3. Make your changes
4. Submit a pull request

## 📬 Support

For questions or issues, please contact the GigPlus development team.

