# Define Microsoft 365 customer profiles
CUSTOMER_PROFILES = {
    "personalities": {
        "impatient": {
            "description": "Gets frustrated easily, wants quick solutions, uses short sentences",
            "traits": ["interrupts frequently", "uses phrases like 'just get to the point'", 
                      "shows time pressure", "may use exclamation marks"]
        },
        "curious": {
            "description": "Asks many questions, wants to understand how things work",
            "traits": ["asks follow-up questions", "shows interest in details", 
                      "uses phrases like 'how does that work?'", "explores options"]
        },
        "resistant": {
            "description": "Skeptical about new solutions, prefers familiar approaches",
            "traits": ["expresses doubt", "mentions previous solutions", 
                      "uses phrases like 'I'm not sure about this'", "needs convincing"]
        },
        "budget-conscious": {
            "description": "Primarily concerned with costs and ROI",
            "traits": ["asks about pricing frequently", "mentions budget constraints", 
                      "compares with existing solutions", "focuses on business value"]
        },
        "security-focused": {
            "description": "Prioritizes data security and compliance",
            "traits": ["asks about security features", "mentions compliance requirements", 
                      "concerned about data access", "asks about certifications"]
        }
    },
    "tech_levels": {
        "beginner": {
            "description": "Limited technical knowledge, needs simple explanations",
            "traits": ["asks basic questions", "may misuse technical terms", 
                      "prefers step-by-step guidance", "gets confused by jargon"]
        },
        "intermediate": {
            "description": "Understands core concepts but may struggle with advanced topics",
            "traits": ["familiar with common terms", "can follow technical explanations", 
                      "occasionally needs clarification", "some hands-on experience"]
        },
        "advanced": {
            "description": "High technical proficiency, understands complex concepts",
            "traits": ["uses technical terminology correctly", "asks sophisticated questions", 
                      "refers to technical documentation", "has extensive hands-on experience"]
        }
    },
    "roles": {
        "IT Admin": {
            "description": "Responsible for implementation, security, and maintenance",
            "traits": ["concerned with tenant management", "interested in security controls", 
                      "thinks about deployment", "wants technical specifications"]
        },
        "Business Manager": {
            "description": "Focuses on business impact, ROI, and team productivity",
            "traits": ["concerned with costs", "interested in productivity gains", 
                      "thinks about user adoption", "less interested in technical details"]
        },
        "Knowledge Worker": {
            "description": "End user focused on productivity and task completion",
            "traits": ["interested in ease of use", "concerned with daily workflows", 
                      "thinks about time savings", "wants practical examples"]
        },
        "Developer": {
            "description": "Focuses on extensibility, APIs, and integration",
            "traits": ["interested in API capabilities", "concerned with customization", 
                      "thinks about integration with existing systems", "detail-oriented"]
        },
        "Compliance Officer": {
            "description": "Focuses on data governance, security, and regulatory compliance",
            "traits": ["concerned with data protection", "interested in audit trails", 
                      "thinks about regulatory requirements", "questions data handling"]
        }
    },
    "industries": {
        "Healthcare": {
            "concerns": ["HIPAA compliance", "patient data security", "workflow efficiency"],
            "terminology": ["patient records", "clinical workflows", "care coordination"]
        },
        "Financial Services": {
            "concerns": ["financial regulations", "data security", "client confidentiality"],
            "terminology": ["client portfolios", "compliance", "risk management"]
        },
        "Education": {
            "concerns": ["student privacy", "collaboration tools", "classroom integration"],
            "terminology": ["learning management", "student engagement", "educational outcomes"]
        },
        "Retail": {
            "concerns": ["customer data", "operational efficiency", "marketing insights"],
            "terminology": ["customer experience", "inventory management", "omnichannel"]
        },
        "Manufacturing": {
            "concerns": ["supply chain visibility", "operational efficiency", "knowledge sharing"],
            "terminology": ["production processes", "quality control", "supply chain"]
        }
    },
    "company_size": {
        "Small": {
            "description": "Under 50 employees",
            "traits": ["budget sensitive", "wears multiple hats", "quick decision making", "flexible adoption"]
        },
        "Medium": {
            "description": "50-500 employees",
            "traits": ["balanced approach", "departmental needs", "moderate approval process", "growing infrastructure"]
        },
        "Enterprise": {
            "description": "500+ employees",
            "traits": ["complex requirements", "formal procurement", "extensive testing", "global deployment needs"]
        }
    }
}

# Define Microsoft Copilot product information
PRODUCT_INFO = {
    "name": "Microsoft Copilot for Microsoft 365",
    "description": "An AI-powered productivity assistant that integrates across Microsoft 365 apps",
    "key_features": [
        "AI-powered writing assistance in Word, Outlook, and PowerPoint",
        "Data analysis and insights in Excel",
        "Meeting summaries and action items in Teams",
        "Intelligent search across all content",
        "Business Chat for cross-app productivity",
        "Natural language queries for data"
    ],
    "pricing": {
        "Copilot for Microsoft 365": {
            "price": "$30 per user/month",
            "requirements": "Requires Microsoft 365 E3/E5 or Business Standard/Premium subscription"
        },
        "Copilot Pro": {
            "price": "$20 per user/month",
            "features": "Enhanced AI capabilities for individual users"
        },
        "Copilot Studio": {
            "price": "Starting at $10 per user/month",
            "features": "Build and deploy custom copilots"
        }
    },
    "prerequisites": [
        "Microsoft 365 subscription",
        "Minimum of 300 seats for enterprise customers",
        "Azure Active Directory",
        "Proper licensing for all users"
    ],
    "common_issues": [
        "Deployment requirements and prerequisites",
        "Integration with existing workflows",
        "Data privacy and security concerns",
        "User adoption and training needs",
        "ROI and productivity measurement",
        "Licensing and pricing questions"
    ]
}

# Define scenario templates
SCENARIOS = [
    {
        "title": "Initial Inquiry",
        "description": "Customer is exploring Microsoft Copilot capabilities",
        "customer_context": "Heard about {product_name} and wants to understand how it could benefit their organization",
        "initial_query": "We're looking to improve our productivity and I've heard about Microsoft Copilot. Can you tell me more about what it can do for us?"
    },
    {
        "title": "Licensing and Pricing",
        "description": "Customer has questions about licensing requirements and pricing",
        "customer_context": "Considering {product_name} but needs to understand the cost structure",
        "initial_query": "I'm trying to figure out the licensing for Copilot. How does it work with our existing Microsoft 365 subscriptions?"
    },
    {
        "title": "Security and Compliance",
        "description": "Customer has concerns about data security and compliance",
        "customer_context": "Interested in {product_name} but worried about data privacy",
        "initial_query": "Before we consider implementing Copilot, I need to understand how it handles our sensitive data and whether it meets our compliance requirements."
    },
    {
        "title": "Implementation Planning",
        "description": "Customer needs guidance on implementation approach",
        "customer_context": "Approved {product_name} purchase and planning deployment",
        "initial_query": "We've decided to move forward with Copilot. What's the best approach to roll it out to our organization?"
    },
    {
        "title": "Use Case Exploration",
        "description": "Customer wants to understand specific use cases for their industry",
        "customer_context": "Evaluating {product_name} for specific department needs",
        "initial_query": "I'm wondering how other companies in our industry are using Copilot. Can you share some specific examples that might be relevant to us?"
    },
    {
        "title": "Technical Integration",
        "description": "Customer has questions about technical integration",
        "customer_context": "IT team evaluating {product_name} integration requirements",
        "initial_query": "We have a complex IT environment with custom applications. How does Copilot integrate with our existing systems and what do we need to prepare?"
    },
    {
        "title": "Training and Adoption",
        "description": "Customer needs guidance on user adoption strategy",
        "customer_context": "Concerned about user adoption of {product_name}",
        "initial_query": "What kind of training and change management do we need to implement to ensure our users actually get value from Copilot?"
    }
] 