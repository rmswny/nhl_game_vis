class Shift:
    """
    Shift that contains general information
    Things to add:
    Events that happened during shift
    Time since previous shift
    Average duration of shift
    Average events per shift
    """

    def __init__(self, team=None, name=None, period=None, start=None, end=None, duration=None, score=None):
        self.team = team
        self.name = name
        self.period = period
        self.start = start
        self.end = end
        self.duration = duration
        self.score = score  # If negative, player's team is behind in score, pos they are ahead
        self.events = []
