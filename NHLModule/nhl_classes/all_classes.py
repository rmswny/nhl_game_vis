# From Names to Abbreviations
TEAM_DICT = {
    "Carolina Hurricanes": "CAR",
    "Washington Capitals": "WSH",
    "Pittsburgh Penguins": "PEN",
    "Buffalo Sabres": "BUF",
    "Boston Bruins": "BOS",
    "Toronto Maple Leafs": "TOR",
    "Detroit Red Wings": "DET",
    "Montreal Canadiens": "MTL",
    "Philadelphia Flyers": "PHI",
    "Tampa Bay Lightning": "TBL",
    "New York Rangers": "NYR",
    "Columbus Blue Jackets": "CBJ",
    "New York Islanders": "NYI",
    "Florida Panthers": "FLA",
    "Ottawa Senators": "OTT",
    "New Jersey Devils": "NJD",
    "Colorado Avalanche": "COL",
    "Winnipeg Jets": "WPG",
    "St Louis Blues": "STL",
    "Edmonton Oilers": "EDM",
    "Anaheim Ducks": "ANA",
    "Las Vegas Golden Knights": "LVG",
    "Nashville Predators": "NSH",
    "Calgary Flames": "CGY",
    "Los Angeles Kings": "LAK",
    "Vancouver Canucks": "VAN",
    "Arizona Coyotes": "ARZ",
    "Dallas Stars": "DAL",
    "San Jose Sharks": "SJS",
    "Chicago Blackhawks": "CHI",
    "Minnesota Wild": "MIN"
}
# Tracked and important events
SET_OF_EVENTS = {
    'Takeaway',
    'Giveaway',
    'Penalty',
    'Hit',
    'Faceoff',
    'Missed Shot',
    'Blocked Shot',
    'Shot'
    'Goal',
}


# MM:SS -> Seconds
def time_to_seconds(time):
    # given a string MM:SS
    # convert to seconds
    sep = time.find(':')
    minutes = int(time[:sep])
    seconds = int(time[sep + 1:])
    return (minutes * 60) + (seconds)


class Event:
    def __init__(self, type_of_event, event_by, team, period, time, x_loc, y_loc):
        self.type_of_event = type_of_event
        self.event_by = event_by
        self.team = team
        self.period = period
        self.time = time_to_seconds(time)
        self.x_loc = x_loc
        self.y_loc = y_loc
        # must add pen minutes field
        self.penalty_length = ''  # convert from minutes to seconds
        self.drew_by = ''  # if the penalty was tracked to have someone who drew it


class Player(Event):

    def __init__(self, name, team, num):
        self.name = name
        self.team = TEAM_DICT[team] if team in TEAM_DICT else ''
        self.num = num
        self.game_dict = {}
        self.personal_shots = {'Missed Shot': 0, 'Blocked Shot': 0, 'Shot': 0, 'Goal': 0}
        self.shots = {"for": 0, "against": 0}
        self.penalties = {"for": 0, "against": 0}

    def __eq__(self, other):
        return self.name == other.name and self.team == other.team


class Shift(Player):

    def __init__(self, Player, period, start_time, end_time):
        self.player = Player
        self.period = period
        self.start_time = time_to_seconds(start_time)
        self.end_time = time_to_seconds(end_time)
        self.duration = self.calc_duration()

    def __eq__(self, other):
        return self.player.name == other.player.name and self.start_time == other.start_time

    def calc_duration(self):
        return self.end_time - self.start_time

    # def minutes_convert(self):
    # def calc_median_shift_length(self):
    # def calc_average_shift_length(self):
    # def calc_median_time_since_last_shift(self):
    # def calc_avg_time_since_last_shift(self):x
