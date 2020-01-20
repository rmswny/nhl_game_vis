class Player:
    # Player will have shifts where each shift can have event(s)
    def __init__(self, name=None, jersey_num=None, team=None):
        self.name = name
        self.jersey_num = jersey_num
        self.team = team
        self.shifts = set()

    def __eq__(self, other):
        """
        Two players are equal if team == team AND name == name AND num == num
        """
        return isinstance(other, self.__class__) and self.name == other.name and self.team == other.team

    def __hash__(self):
        return hash(self.name)

    # TODO: How am I doing this wrong?
    def __getitem__(self, item):
        print(type(item))
        return self.shifts[item]
