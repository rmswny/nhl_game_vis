from pynhl.event import Event
from pynhl.player import Player
from pynhl.shift import Shift

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


class Game(Event):
    # Game will have Players who will have shifts and each shift can/will have event(s)
    '''
    This class will take in a JSON DICT of game data
    And parse out the necessary data (players, events)
    Which will then be used to generate Player/Event classes
    '''

    def __init__(self, game_json, shift_json):
        self.game_json = game_json
        self.shift_json = shift_json
        self.game_id = game_json['gameData']['game']['pk']
        self.game_season = game_json['gameData']['game']['season']
        self.home_team = ''
        self.away_team = ''
        self.final_score = ''
        # Functions & Variables to parse Game Data
        self.fetch_teams_from_game_data()
        self.players_in_game = []
        self.retrieve_players_in_game()
        self.penalties_in_game = set()
        self.faceoffs_in_game = set()
        self.hits_in_game = set()
        self.shots_in_game = set()
        self.goals_in_game = set()
        self.takeaways_in_game = set()
        self.giveaways_in_game = set()
        self.retrieve_events_in_game()
        # Functions & Variables to parse Shift data
        self.retrieve_shifts_from_game()
        a = 5

    def __str__(self):
        return "{}:{}:{} v {}, score -> {}".format(self.game_id, self.game_season, self.home_team, self.away_team,
                                                   self.final_score)

    def fetch_teams_from_game_data(self):
        """
        Parse self.json_data for HOME/AWAY teams in game
        and final score
        """
        try:
            self.away_team = self.game_json['gameData']['teams']['away']['triCode']
            self.home_team = self.game_json['gameData']['teams']['home']['triCode']
            return self
        except KeyError as k:
            print(k)

    def retrieve_players_in_game(self):
        """
        Parse self.json_data for PLAYERS in the game
        Update self.players_in_game to be a list of [Player objects]
        """
        player_dict = self.game_json['gameData']['players']
        for player in player_dict:
            # Add all players from game
            temp_name = player_dict[player]['fullName']  # name
            # jersey number
            temp_num = player_dict[player]['primaryNumber']
            temp_team = player_dict[player]['currentTeam']['triCode']  # team
            temp = Player(temp_name, temp_num, temp_team)
            if temp not in self.players_in_game:
                self.players_in_game.append(temp)
                print(temp.shifts)
        return self.players_in_game

    def retrieve_events_in_game(self):
        """
        Parse self.json_data and retrieve all events reported in the game
        Helper function for each type of event, since each have their own little quirks
        """
        events = self.game_json['liveData']['plays']['allPlays']
        for event in events:
            event_type = event['result']['event']  # Type of event
            if event_type in TRACKED_EVENTS:
                temp = Event(type_of_event=event_type)
                self.parse_event(temp, event)
            elif event_type not in NOT_TRACKED_EVENTS:
                print(event_type)
        # Update final score based off last event
        self.final_score = "{}-{}".format(temp.score[1], temp.score[0])
        return self

    def add_event(self, temp):
        """
        Adds event to it's proper set based off of it's type
        """
        if "Penalty" in temp.type_of_event:
            self.penalties_in_game.add(temp)
        elif "Faceoff" in temp.type_of_event:
            self.faceoffs_in_game.add(temp)
        elif "Shot" in temp.type_of_event:
            self.shots_in_game.add(temp)
        elif "Goal" in temp.type_of_event:
            self.goals_in_game.add(temp)
        elif "Hit" in temp.type_of_event:
            self.hits_in_game.add(temp)
        elif "Takeaway" in temp.type_of_event:
            self.takeaways_in_game.add(temp)
        elif "Giveaway" in temp.type_of_event:
            self.giveaways_in_game.add(temp)
        else:
            raise NotImplementedError
        return self

    def parse_event(self, temp, event):
        """
        Parses event from NHL API
        Functions handle edge cases for different events
        """
        temp = temp.get_players(event)
        temp = temp.get_team(event)
        temp = temp.get_period(event)
        temp = temp.get_time(event)
        temp = temp.get_score(event)
        temp = temp.get_x(event)
        temp = temp.get_y(event)
        self.add_event(temp)

    def retrieve_shifts_from_game(self):
        """
        Assign shifts in game to it's corresponding player
        """
        # Creating shift class
        temp = Shift()
        for shifts in self.shift_json['data']:
            temp.team = shifts['teamAbbrev']
            temp.name = shifts['firstName'] + " " + shifts['lastName']
            temp.period = shifts['period']
            temp.start = shifts['startTime']
            temp.end = shifts['endTime']
            temp.duration = shifts['duration']
            score = shifts['homeScore'], shifts['visitingScore']
            if temp.team == self.home_team:
                rel_score = score[0] - score[1]
            else:
                rel_score = score[1] - score[0]
            temp.score = rel_score
        # Find player, add shift to their object
        # if Player(name=temp.name, team=temp.team) in self.players_in_game:
    # TODO: Getting the player object inside the set
    # Make sure player already has the game object


"""
Does it make more sense to generate the events, shifts and the combination before generating the player list?
Simply add events, shifts to each player hwen they are all calculated
"""
