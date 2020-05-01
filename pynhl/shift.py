import datetime


def convert_to_time(str_to_time):
    """
    Takes a string and converts it to datetime.time() object
    """
    return datetime.datetime.strptime(str_to_time, "%M:%S").time()


class Shift:
    def __init__(self, game_id, home_team, shift_json):
        self.game_id = game_id
        self.team = shift_json['teamAbbrev']
        self.player = f"{shift_json['firstName']} {shift_json['lastName']}"
        self.shift_number_in_game = shift_json['shiftNumber']
        self.period = int(shift_json['period'])
        self.start = convert_to_time(shift_json['startTime'])
        self.end = convert_to_time(shift_json['endTime'])
        self.duration = shift_json['duration']
        self.duration_to_seconds()
        self.score = (shift_json['homeScore'], shift_json['visitingScore'])
        self.normalize_score(home_team)
        self.events_during_shift = []  # Events that happened during the shift

    def __eq__(self, other):
        if self.period == other.period:
            return self.end < other.end
        else:
            return self.period < other.period

    def __hash__(self):
        return hash(self.period) + hash(self.duration)

    def __str__(self):
        return f"{self.player} , {self.period} , {self.start} : {self.end}"

    def __lt__(self, other):
        if isinstance(other, Shift):
            if self.period == other.period:
                return self.start < other.start
            else:
                return self.period < other.period
        else:
            # Comparing datetime's, not a shift
            return self.start < other

    def __gt__(self, other):
        return not (self < other)

    def normalize_score(self, home_team):
        if self.team == home_team:
            self.score = self.score[0] - self.score[1]
        else:
            self.score = self.score[1] - self.score[0]
        return self.score

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
