from operator import itemgetter, attrgetter


class Shift():
    # Shift can have events
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = ''
        self.events = []


class Event():
    """
    Events are shots, hits, faceoffs, takeaways, giveaways, goals, penalties
    """
    TYPE_OF_EVENTS = {

    }

    def __init__(self, type_of_event, period, time, x_loc=None, y_loc=None):
        self.type_of_event = type_of_event
        self.period = period
        self.time = time
        self.x_loc = x_loc
        self.y_loc = y_loc

    def __eq__(self, other):
        return self.type_of_event == other.type_of_event and self.period == other.type_of_event \
            and self.time == other.time and self.x_loc == self.x_loc and self.y_loc == self.y_loc

    def __hash__(self):
        return hash(self.type_of_event)+hash(self.period)+hash(self.time)


class Player():
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


class Game():
    # Game will have Players who will have shifts and each shift can/will have event(s)
    '''
    This class will take in a JSON DICT of game data
    And parse out the necessary data (players, events)
    Which will then be used to generate Player/Event classes
    '''

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
        Parse self.json_data for EVENTS in the game
        """
        try:
            events = self.json_data['liveData']['plays']['allPlays']
            for event in events:
                #type_of_event, time, x_loc, y_loc
                e_type = event['result']['event']
                e_period = event['about']['period']
                e_time = event['about']['periodTime']
                if event['coordinates']:
                    e_x = event['coordinates']['x']
                    e_y = event['coordinates']['y']
                try:
                    temp_event = Event(e_type, e_period, e_time, e_x, e_y)
                except NameError:
                    temp_event = Event(e_type, e_period, e_time)
                self.events_in_game.add(temp_event)
            [print(x.type_of_event, x.period, x.time, x.x_loc, x.y_loc)
             for x in self.events_in_game]
        except KeyError as k:
            print(k)

    def retrieve_penalties_in_game(self):
        """
        Retrieve penalties from self.events
        """
        pass

    def retrieve_shots_in_game(self):
        """
        Retrieve all shots in game
                Should we separate into missed/on-net/blocked?
        """
        pass

    def retrieve_faceoffs_in_game(self):
        """
        Retrieve all faceoffs in game
        """
        pass
