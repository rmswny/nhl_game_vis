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


class Game:
    # Game will have Players who will have shifts and each shift can/will have event(s)
    '''
    This class will take in a JSON DICT of game data
    And parse out the necessary data (players, events)
    Which will then be used to generate Player/Event classes
    '''
    TRACKED_EVENTS = {
        "Shot",
        "Faceoff",
        "Giveaway",
        "Takeaway",
        "Penalty",
        "Missed Shot",
        "Blocked Shot",
        "Goal",
        "Hit"
    }

    def __init__(self, json_input):
        self.json_data = json_input
        self.home_team = ''
        self.away_team = ''
        self.final_score = ''
        self.players_in_game = set()  # set of players
        self.events_in_game = set()
        # self.penalties_in_game = set()
        # self.faceoffs_in_game = set()
        # self.shots_in_game = set()
        # self.goals_in_game = set()
        # Functions after init
        self.fetch_teams_from_game_data()
        self.retrieve_players_in_game()
        self.retrieve_events_in_game()
        print(self.events_in_game)

    def fetch_teams_from_game_data(self):
        """
        Parse self.json_data for HOME/AWAY teams in game
        and final score
        """
        try:
            self.away_team = self.json_data['gameData']['teams']['away']['triCode']
            self.home_team = self.json_data['gameData']['teams']['home']['triCode']
            return self
        except KeyError as k:
            print(k)

    def retrieve_players_in_game(self):
        """
        Parse self.json_data for PLAYERS in the game
        Update self.players_in_game to be a list of [Player objects]
        """
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


    def parse_event(self, event):
        """
        Parses event from NHL API
        Functions handle edge cases for different events
        """
        temp = Event
        temp.player_for, temp.player_against = self.get_players(event)
        # Blocked shot tracks WHO blocked it, not who SHOT it
        # Must use players in game to get other team
        temp.team_of_player = self.get_team(event)
        temp.period = self.get_period(event)
        temp.time = self.get_time(event)
        temp.score = self.get_score(event)
        temp.x_loc = self.get_x(event)
        temp.y_locself.get_y(event)
        return temp
