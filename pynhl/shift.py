import datetime


def convert_to_time(str_to_time):
    """
    Takes a string and converts it to datetime.time() object
    """
    return datetime.datetime.strptime(str_to_time, "%M:%S").time()


class Shift:
    """
    Shift that contains general information
    Things to add:
    Events that happened during shift
    Time since previous shift
    Average duration of shift
    Average events per shift
    Average shifts per period
    """

    def __init__(self, game_id=None, team=None, name=None, period=None, start=None, end=None, duration=None,
                 score=None):
        self.game_id = game_id
        self.team = team
        self.name = name
        self.period = period
        self.start = convert_to_time(start)
        self.end = convert_to_time(end)
        self.duration = duration
        self.score = score  # If negative, player's team is behind in score, pos they are ahead
        self.duration_to_seconds()
        self.events = []  # Events that happened during the shift

    def __eq__(self, other):
        return self.period == other.period and self.start == other.start and self.end == other.end

    def __hash__(self):
        return hash(self.period) + hash(self.duration)

    def __str__(self):
        return f"{self.name} , {self.period} , {self.start} : {self.end}"

    def __lt__(self, other):
        if self.period == other.period:
            return self.start < other.start
        else:
            return self.period < other.period

    def __gt__(self, other):
        return not (self < other)

    def duration_to_seconds(self):
        """
        Converts duration to an int of total seconds
        """
        if not self.duration:
            self.duration = 0
            return self
        if not isinstance(self.duration, datetime.time):
            self.duration = convert_to_time(self.duration)
        minutes = self.duration.minute
        seconds = self.duration.second
        self.duration = minutes * 60 + seconds
        return self
