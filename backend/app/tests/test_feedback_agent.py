import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.agents.feedback import FeedbackAgent

conversation_history = [
    "Could you tell me about your issues with copilot?",
    "I've had a frustrating experience with Copilot, particularly in Excel. It has crashed a couple of times when I was trying to use it, which is really inconvenient during busy times. Also, the accuracy of the basic formulas it applies to rows is just off, which doesn't make sense for a tool that's supposed to assist with data analysis. I do appreciate its drafting capabilities, but for the data work I need, it feels like it's not quite there yet.",
    "Okay, I understand your issues and I appreciate your feedback so much. Could you tell me more about what kind of prompts are you using?",
    "I've primarily been using prompts for data analysis, like creating pivot tables or summarizing data sets. But when it comes to handling complex formulas, it just doesn't deliver what I expect. It's frustrating because I really want to rely on it to help manage our campaigns more efficiently. Have these issues been reported by others?",
    "Okay, so are you sending as a context the tables of the context? Most of times Copilot doesn't work properly due to a lack of context. If you want, I can share you a documentation of how to make successful prompts. Im sure this will improve your results a lot",
    "I appreciate the suggestion, but to be honest, I feel like I'm already inputting enough context for it to understand what I need. It's just frustrating that it doesn't seem to process that accurately. Thanks for your help, though. I'll look into the documentation if I have time, but I hope these issues get sorted out soon."
]

conditions = [
    "Agent mentions they are from Microsoft",
    "Agent ask about positive experience with Copilot",
    "Agent asks details",
    "Agent aligns to business goals",
    "Agent ask about issues or bad experiences with Copilot"
]

accumulated_conditions = [
    "Agent mentions they are from Microsoft",
    "Agent asks details",
    "Agent ask about issues or bad experiences with Copilot"
]

if __name__ == "__main__":
    agent = FeedbackAgent()
    feedback = agent.generate_feedback(
        conversation_history="\n".join(conversation_history),
        conditions=conditions,
        accumulated_conditions=accumulated_conditions,
        optional_aspects=0,
        red_flags=0
    )
    import pprint
    pprint.pprint(feedback) 