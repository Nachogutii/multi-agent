class CustomerStateAgent:
    def __init__(self):
        self.state = "neutral"

    def set_initial_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def update_state(self, user_input):
        # Basic simulation: get impatient if user gives long answers
        if len(user_input.split()) > 25:
            self.state = "impatient"
        elif "thanks" in user_input.lower():
            self.state = "satisfied"
        # Could add more rules or even sentiment analysis later
