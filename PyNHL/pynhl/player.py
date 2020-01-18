class Player:
    # Player will have shifts where each shift can have event(s)
    def __init__(self, name, jersey_num, team):
        self.name = name
        self.jersey_num = jersey_num
        self.team = team
        self.shifts = {}  # Dict makes it faster lookup for adding shifts/events

    def __eq__(self, other):
        """
        Two players are equal if team == team AND name == name AND num == num
        """
        return self.name == other.name and self.jersey_num \
               and other.jersey_num and self.team == other.team

    def __hash__(self):
        return hash(self.name) + hash(self.jersey_num) + hash(self.team)