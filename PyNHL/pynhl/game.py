import datetime
from pynhl.event import Event
from pynhl.player import Player

NOT_TRACKED_EVENTS = {
    "Period Start",
    "Game Official",
    "Game End",
    "Period End",
    "Game Scheduled",
    "Period Ready",
    "Period Official",
    "Stoppage"
}


def get_type(event):
    """
    Return the type of event from NHL API
    ie "result": {"event": "Faceoff"}
    """
    return event["result"]["event"]


def get_players(event):
    """
    Return the player who DID the event
    """
    return event['players'][0]['player']['fullName']


def get_team(event):
    """
    Returns the team of the player who DID the event
    abbreviated (BUF) format not full (Buffalo Sabres)
    """
    return event['team']['triCode']


def get_period(event):
    """
    Returns the period when the event occurred
    """
    return event['about']['period']


def get_time(event):
    """
    Returns the time, in seconds, when the event occurred
    MM:SS -> SS
    """
    temp = datetime.datetime.strptime(event['about']['periodTime'], "%M:%S").time()
    return int(datetime.timedelta(minutes=temp.minute, seconds=temp.second).total_seconds())


def get_score(event):
    """
    Adds the score at the time of the event
    """
    return event['about']['goals']['away'], event['about']['goals']['home']


def get_x(event):
    """
    Return x coordinate from event
    """
    return event['coordinates']['x']


def get_y(event):
    """
    Return y value from event
    """
    return event['coordinates']['y']


def parse_shot(event):
    """
    Parse a shot event from the NHL API game data
    """
    e_type = get_type(event)
    e_player_for = get_players(event)
    e_team = get_team(event)
    e_period = get_period(event)
    e_time = get_time(event)
    e_score = get_score(event)
    e_x = get_x(event)
    e_y = get_y(event)
    return Event(e_player_for, e_team, e_type, e_period, e_time, e_score, e_x, e_y)


def parse_faceoff(event):
    """
    Parse a faceoff event from the NHL API game data
    """
    return Event(player_for=get_players(event), team=get_team(event), type_of_event=get_type(event),
                 period=get_period(event), time=get_time(event), score=get_score(event), x_loc=get_x(event),
                 y_loc=get_y(event))


class Game:
    # Game will have Players who will have shifts and each shift can/will have event(s)
    '''
    This class will take in a JSON DICT of game data
    And parse out the necessary data (players, events)
    Which will then be used to generate Player/Event classes
    '''
    # "Hit",
    # "Giveaway",
    # "Goal",
    # "Missed Shot",
    # "Penalty",
    # "Takeaway",
    # "Blocked Shot"
    TRACKED_EVENTS = {
        "Shot": parse_shot,
        "Faceoff": parse_faceoff,
    }

    def __init__(self, json_input):
        self.json_data = json_input
        self.home_team = ''
        self.away_team = ''
        self.final_score = ''
        self.players_in_game = set()  # set of players
        self.events_in_game = set()
        self.penalties_in_game = set()
        self.faceoffs_in_game = set()
        self.shots_in_game = set()
        self.goals_in_game = set()
        # Functions after init
        self.fetch_teams_from_game_data()
        self.retrieve_players_in_game()
        self.retrieve_events_in_game()

    def fetch_teams_from_game_data(self):
        """
        Parse self.json_data for HOME/AWAY teams in game
        and final score
        """
        try:
            self.away_team = self.json_data['gameData']['teams']['away']['name']
            self.home_team = self.json_data['gameData']['teams']['home']['name']
            return self
        except KeyError as k:
            print(k)

    def retrieve_players_in_game(self):
        """
        Parse self.json_data for PLAYERS in the game
        Update self.players_in_game to be a list of [Player objects]
        """
        try:
            player_dict = self.json_data['gameData']['players']
            for player in player_dict:
                # Add all players from game
                temp_name = player_dict[player]['fullName']  # name
                # jersey number
                temp_num = player_dict[player]['primaryNumber']
                temp_team = player_dict[player]['currentTeam']['name']  # team
                temp = Player(temp_name, temp_num, temp_team)
                if temp not in self.players_in_game:
                    self.players_in_game.add(temp)
            return self.players_in_game
        except KeyError as k:
            print(k)

    def retrieve_events_in_game(self):
        """
        Parse self.json_data and retrieve all events reported in the game
        Helper function for each type of event, since each have their own little quirks
        """
        events = self.json_data['liveData']['plays']['allPlays']
        for event in events:
            e_type = event['result']['event']  # Type of event
            if e_type in self.TRACKED_EVENTS:
                self.events_in_game.add(self.TRACKED_EVENTS[e_type](event))
        return self.events_in_game
