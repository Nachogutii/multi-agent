# GigPlus Conversational Simulator

This project is a training and evaluation tool developed for **GigPlus**, aimed at enhancing the performance of agents during client interactions. It simulates realistic conversations with customers and provides immediate feedback to improve communication skills and extract more insightful data from calls.

---

## 🎯 Purpose

The main goal of this project is to simulate client-agent phone conversations in order to help GigPlus agents practice and improve their approach. The tool also automatically evaluates the conversations based on various qualitative factors, helping agents understand their strengths and areas for improvement.

---

## 🧠 How It Works

1. **Scenario Generation**
   - At the start, a random scenario is generated with a detailed context and an initial query from the simulated customer.

2. **Conversation Flow**
   - The agent (user) can interact with the simulated customer through a chat interface.
   - The simulated customer is powered by a language model and responds based on a selected profile and the current scenario.

3. **Voice Interaction**
   - The user can choose to interact using their voice (speech-to-text) and hear the customer’s responses out loud (text-to-speech), thanks to integrated voice services.

4. **Conversation Evaluation**
   - At any point, the agent can view a detailed **feedback report** which includes:
     - Strengths
     - Weaknesses
     - Missed opportunities
     - Customer objections
     - Suggestions for improvement

---

## 🧱 Project Structure

```
multi-agent/
├── backend/                # FastAPI backend
│   ├── main.py             # Main backend logic and API routes
│   ├── agents/             # Logic for customer agent, observer, phases...
│   ├── profiles.py         # Customer profiles and scenarios
│   └── ...
├── frontend-react/         # React frontend with voice integration
│   ├── src/components/     # HomePage, ChatPage, FeedbackPage
│   ├── public/
│   └── ...
├── Makefile               # Commands for setup and running
├── .env.example           # Example environment variables
└── requirements.txt       # Python backend dependencies
```

---

## 🚀 Technologies Used

### Backend (FastAPI)
- Python 3.11+
- FastAPI
- Azure OpenAI (via `openai` Python client)
- Conversation simulation and evaluation logic

### Frontend (React)
- React + JSX
- Azure Speech SDK (text-to-speech and speech-to-text)
- Routing with `react-router-dom`
- Custom CSS and minimal Tailwind usage (can be removed)

### Deployment
- **Frontend**: Netlify
- **Backend**: Render

---

## 🔧 Environment Variables

You will need the following variables set in your `.env` files:

### For Backend:
```env
AZURE_OPENAI_ENDPOINT=https://your-openai-endpoint
AZURE_OPENAI_KEY=your-openai-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### For Frontend:
```env
REACT_APP_SPEECH_KEY=your-speech-service-key
REACT_APP_SPEECH_REGION=your-region
```

---

## ▶️ How to Run the App Locally

### 1. Install Everything
```bash
make install
```

### 2. Start Frontend and Backend Together
```bash
make start
```

This will run the backend at `http://localhost:8000` and the frontend at `http://localhost:3000`

---

## 📬 Feedback Page

The feedback button on the chat page leads to a detailed evaluation page, where agents can see:
- Their overall score
- Strengths and weaknesses
- Specific suggestions for improvement
- Customer objections identified

This is crucial to improve communication and selling skills based on previous conversations.

---

## 📦 Deployment Notes
- Ensure CORS is enabled on the backend (already configured).
- Deploy frontend on Netlify (builds with `npm run build`).
- Deploy backend on Render (run with `uvicorn main:app`).
- Update URLs in frontend `.env` to point to the correct backend URL.

---

## ✨ Future Improvements
- Add support for multiple simultaneous scenarios
- Allow agents to select scenario difficulty
- Add progress tracking over time for each agent

---

Built with ❤️ to help GigPlus agents level up their conversations.

