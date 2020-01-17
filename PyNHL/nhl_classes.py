class Shift():
    # Shift can have events
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = ''
        self.events = []

class Event():
    TYPE_OF_EVENTS = {

    }

    def __init__(self, type_of_event, time, x_loc, y_loc):
        self.type_of_event = type_of_event
        self.time = time
        self.x_loc = x_loc
        self.y_loc = y_loc


class Player():
    # Player will have shifts where each shift can have event(s)
    def __init__(self, name, jersey_num, team):
        self.name = name
        self.jersey_num = jersey_num
        self.team = team
        self.shifts = []


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
        self.players_in_game = []
        self.events_in_game = []
        self.penalties_in_game = []
        self.faceoffs_in_game = []
        self.shots_in_game = []
        self.goals_in_game = []
        #
    def fetch_teams_from_game_data(self):
        """
        Parse self.json_data for HOME/AWAY teams in game
        and final score
        """
        pass
    def retrieve_players_in_game(self):
        """
        Parse self.json_data for PLAYERS in the game
        Update self.players_in_game to be a list of [Player objects]
        """
        pass
    def retrieve_events_in_game(self):
        """
        Parse self.json_data for EVENTS in the game
        """
        pass
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