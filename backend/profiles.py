CUSTOMER_PROFILES = {
    "personalities": {
    "open": {
        "label": "Open",
        "description": "Open to new ideas and willing to explore solutions",
        "traits": ["curious", "asks exploratory questions", "engaged"]
    },
    "direct": {
        "label": "Direct",
        "description": "Prefers straight-to-the-point conversations",
        "traits": ["brief", "assertive", "no patience for fluff"]
    }
    },


    "tech_levels": {
    "beginner": {
        "label": "Beginner",
        "description": "Limited technical background",
        "traits": ["asks basic questions", "needs guidance"]
    },
    "intermediate": {
        "label": "Intermediate",
        "description": "Some hands-on experience with tech tools",
        "traits": ["asks how-to questions", "seeks practical applications"]
    },
    "advanced": {
        "label": "Advanced",
        "description": "Deep understanding of IT systems",
        "traits": ["asks architecture-level questions", "interested in integrations"]
    }
    },

    "roles": {
    "it_manager": {
        "label": "IT Manager",
        "description": "Responsible for selecting and implementing technology",
        "traits": ["focused on security", "cost-aware", "asks implementation questions"]
    },
    "executive": {
        "label": "Executive",
        "description": "Decision maker interested in business impact",
        "traits": ["ROI-driven", "asks strategic questions", "wants efficiency"]
    }
    },

    "industries": {
    "technology": {
        "label": "Technology",
        "concerns": ["scalability", "integration", "performance"]
    },
    "finance": {
        "label": "Finance",
        "concerns": ["compliance", "security", "auditability"]
    }
    },

    "company_size": {
    "small": {
        "label": "Small",
        "description": "Fewer than 100 employees",
        "traits": ["budget conscious", "agile", "looking for all-in-one solutions"]
    },
    "medium": {
        "label": "Medium",
        "description": "100-500 employees",
        "traits": ["growing", "interested in scalability", "focused on collaboration"]
    },
    "large": {
        "label": "Large",
        "description": "More than 500 employees",
        "traits": ["structured", "complex needs", "multi-team coordination"]
    }
    },

    "interested_customer": {
        "role": "IT Manager",
        "personality": "open and inquisitive",
        "intent": "learn more about Microsoft 365 Copilot",
        "emotional_state": "neutral",
        "phase_slots": ["introduction_discovery", "closing"]
    },
    "busy_customer": {
        "role": "Executive",
        "personality": "direct and impatient",
        "intent": "assess Copilot quickly",
        "emotional_state": "hurried",
        "phase_slots": ["introduction_discovery", "immediate_closure"]
    }
}

PRODUCT_INFO = {
    "name": "Copilot",
    "description": "A powerful AI assistant to enhance productivity and collaboration.",
    "features": [
        "Automated task management",
        "Intelligent scheduling",
        "Real-time collaboration insights",
        "Advanced data analysis"
    ],
    "key_features": [
        "Automated task management",
        "Intelligent scheduling",
        "Real-time collaboration insights",
        "Advanced data analysis"
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