class Player:
    def __init__(self, name, team, num):
        self.name = name
        self.team = team
        self.num = num
        self.game_dict = {}

    def __eq__(self, other):
        return self.name == other.name and self.team == other.team

    def __hash__(self):
        return hash((self.name) * (self.team))
