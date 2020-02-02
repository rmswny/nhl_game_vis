from pynhl.event import Event


class Player:
    # Player will have shifts where each shift can have event(s)
    def __init__(self, name=None, jersey_num=None, team=None):
        self.name = name
        self.jersey_num = jersey_num
        self.team = team
        # Each shift can have events
        self.shifts = []
        self.events_on_ice_for = []
        self.event_on_ice_against = []
        self.events_involving = []

    def __eq__(self, name):
        """
        Two players are equal if name==name, team==team
        How to check for it existing other than ensuring a Player object is created
        """
        return self.name == name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return f"{self.name} : {self.team} : {self.jersey_num}"
