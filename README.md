# Microsoft Copilot PLG Customer Service Roleplay Simulator

This project is a roleplay simulator for practicing sales and technical support conversations related to Microsoft Copilot. The system uses Azure OpenAI to simulate customers with different profiles and scenarios.

## Key Features

- Customer simulation with different profiles and personalities
- Predefined sales and support scenarios
- Real-time feedback system
- Conversation quality analysis
- Azure OpenAI integration

## Prerequisites

- Python 3.7 or higher
- Azure account with Azure OpenAI access
- Environment variables configured:
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_KEY`
  - `AZURE_OPENAI_DEPLOYMENT`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <project-directory>
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
export AZURE_OPENAI_ENDPOINT='your-endpoint'
export AZURE_OPENAI_KEY='your-key'
export AZURE_OPENAI_DEPLOYMENT='your-deployment-name'
```

## Usage

1. Run the simulator:
```bash
python test.py
```

2. Available commands during simulation:
- `/new` or `/reset` - Start a new scenario
- `/quit` or `/exit` - Exit the roleplay
- `/help` - Show help messages
- `/info` - Show current scenario information
- `/list` - Show all possible scenarios
- `/feedback` - Show current conversation feedback

## System Structure

The system consists of several main classes:

1. **RoleplaySystem**: Manages the main roleplay system
2. **CustomerAgent**: Simulates the customer with specific characteristics
3. **DialogueController**: Controls and monitors dialogue to maintain realism
4. **ObserverCoach**: Analyzes interaction and provides feedback

## Available Scenarios

- Initial Inquiry
- Licensing and Pricing
- Security and Compliance
- Implementation Planning
- Use Case Exploration
- Technical Integration
- Training and Adoption

## Customer Profiles

Simulated customers can have different combinations of:

- **Personalities**: Impatient, Curious, Resistant, Budget-conscious, Security-focused
- **Technical Levels**: Beginner, Intermediate, Advanced
- **Roles**: IT Admin, Business Manager, Knowledge Worker, Developer, Compliance Officer
- **Industries**: Healthcare, Financial Services, Education, Retail, Manufacturing
- **Company Size**: Small, Medium, Enterprise

## Scoring System

The system evaluates several aspects of the conversation:

- Clarity and professionalism
- Customer empathy
- Product knowledge
- Problem-solving

## Contributing

If you want to contribute to the project:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

[Include license information here] 