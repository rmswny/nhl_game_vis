from pynhl.event import Event, is_time_within_range, find_start_index
from pynhl.player import Player
from pynhl.shift import Shift
from datetime import datetime, date, timedelta
from operator import attrgetter, itemgetter

STOPPAGES = {
    "Stoppage",
    "Period Start"
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
NOT_TRACKED_EVENTS = {
    "Period Start",
    "Game Official",
    "Game End",
    "Period End",
    "Game Scheduled",
    "Period Ready",
    "Period Official"
}


def subtract_two_time_objects(left, right):
    """
    Select two datetime.time objects
    And normalize return to seconds
    """
    result = timedelta(minutes=left.minute, seconds=left.second) - \
             timedelta(minutes=right.minute, seconds=right.second)
    if result.days == -1:
        temp = (timedelta(days=1) - result)
        return (temp.seconds // 3600) * 60 + temp.seconds
    else:
        return (result.seconds // 3600) * 60 + result.seconds


def get_time_shared(curr_shift, other_shift):
    """Function to return the time shared while on the ice together"""
    """
    How to get the time shared?
    Current method -> find the start/end time when both are on the ice, subtract that differnece, move on
        but it requires increasing the lower bound and decreasing the upper bound
        Min : start or end time? 
        max(start), min(end)
        subtract that difference!
    """
    lower_bound = max(curr_shift.start, other_shift.start)
    upper_bound = min(curr_shift.end, other_shift.end)
    temp = datetime.combine(date.today(), upper_bound) - datetime.combine(date.today(), lower_bound)
    return temp.seconds


class Game:
    # Game will have Players who will have shifts and each shift can/will have event(s)
    '''
    This class will take in a JSON DICT of game data
    And parse out the necessary data (players, events)
    Which will then be used to generate Player/Event classes
    '''

    def __init__(self, game_json, shift_json):
        # Basic game information
        self.game_json = game_json
        self.shift_json = shift_json
        self.game_id = self.game_json['gameData']['game']['pk']
        self.game_season = self.game_json['gameData']['game']['season']
        self.away_team = self.game_json['gameData']['teams']['away']['triCode']
        self.home_team = self.game_json['gameData']['teams']['home']['triCode']
        self.away_goalie = set()
        self.home_goalie = set()
        self.final_score = ''
        # Players and shifts for each game
        self.shifts_in_game = {}
        self.retrieve_shifts_from_game()
        self.sort_shifts()
        self.players_in_game = {}
        self.retrieve_players_in_game()
        self.events_in_game = []
        self.retrieve_events_in_game()
        # Clear unnecessary data from the game API
        self.cleanup()
        # Extra functionality that doesn't require game/shift json
        self.parse_events_in_game()
        self.generate_line_times()

    def __str__(self):
        # return f"Game ID: {self.game_id} , Season: {self.game_season} : {self.home_team} " \
        #        f"vs. {self.away_team} Final Score: {self.final_score}"
        return "Game ID: {} Season: {} {} vs. {} Final Score: {}".format(self.game_id, self.game_season, self.home_team,
                                                                         self.away_team, self.final_score)

    def cleanup(self):
        self.game_json = None
        self.shift_json = None

    def add_goalie(self, player_object):
        """
        If a player is a goalie, adds it to home/away_goalie variable
        """
        if isinstance(player_object, Player):
            if 'G' in player_object.position:
                if player_object.team == self.home_team:
                    self.home_goalie.add(player_object.name)
                else:
                    self.away_goalie.add(player_object.name)
        return self

    def retrieve_players_in_game(self):
        """
        Parse self.json_data for PLAYERS in the game
        Update self.players_in_game to be a list of [Player objects]
        """
        all_players = self.game_json["gameData"]["players"]
        for player_id in all_players:
            # Add all players from game
            temp = Player(all_players[player_id])
            if temp.team not in self.players_in_game:
                self.players_in_game[temp.team] = []
            if temp not in self.players_in_game[temp.team]:
                self.players_in_game[temp.team].append(temp)
            self.add_goalie(temp)
        return self.players_in_game

    def get_final_score(self, last_event):
        """
        Retrieve final score from json data
        """
        self.final_score = "{}-{}".format(last_event.score[1], last_event.score[0])
        return self

    def normalize_score(self, team, score):
        if team == self.home_team:
            score = score[0] - score[1]
        else:
            score = score[1] - score[0]
        return score

    def create_shift(self, shift):
        team = shift['teamAbbrev']
        name = "{} {}".format(shift['firstName'], shift['lastName'])
        period = int(shift['period'])
        shift_start = shift['startTime']
        shift_end = shift['endTime']
        shift_dur = shift["duration"]
        score = self.normalize_score(team, (shift['homeScore'], shift['visitingScore']))
        temp = Shift(game_id=self.game_id, team=team, name=name, period=period, start=shift_start, end=shift_end,
                     duration=shift_dur,
                     score=score)
        return temp

    def sort_shifts(self, sort_key='end'):
        """Helper function to find the correct placement to"""
        for period in self.shifts_in_game:
            for player in self.shifts_in_game[period]:
                self.shifts_in_game[period][player].sort(key=attrgetter(sort_key))
        return self

    def retrieve_shifts_from_game(self):
        """
        Assign shifts in game to it's corresponding player
        """
        # Creating shift class
        for shift in self.shift_json['data']:
            temp = self.create_shift(shift)
            # Shifts separated by player in game
            if temp.period not in self.shifts_in_game:
                self.shifts_in_game[temp.period] = {}
            if temp.name not in self.shifts_in_game[temp.period]:
                self.shifts_in_game[temp.period][temp.name] = []
            self.shifts_in_game[temp.period][temp.name].append(temp)
        return self

    def retrieve_events_in_game(self):
        """
        Function to retrieve all events, and their necessary information
        to the class object
        """
        events = self.game_json['liveData']['plays']['allPlays']
        add_events = self.events_in_game.append
        for index, curr_event in enumerate(events):
            type_of_event = curr_event['result']['event']
            if type_of_event in TRACKED_EVENTS:
                temp_event = Event(curr_event)
                add_events(temp_event)
            # elif type_of_event in STOPPAGES:
            #     self.add_stoppage(curr_event)
        try:
            # Last events holds the final score of the game
            self.get_final_score(temp_event)
        except UnboundLocalError as no_events_in_game:
            print("Somehow not one event was in a game")
            print(no_events_in_game)
        return self

    def parse_events_in_game(self):
        """
        Function to find the players who are on ice for the event, and determine the state at time of the event
        :return:
        """
        for i, event_to_parse in enumerate(self.events_in_game):
            if isinstance(event_to_parse, Event):
                event_to_parse.get_players_for_event(self.shifts_in_game[event_to_parse.period],
                                                     self.home_goalie.union(self.away_goalie))
                event_to_parse.determine_event_state()
                self.events_in_game[i] = event_to_parse
        return self

    def get_all_shifts_per_player(self, player_name):
        """Helper function to retrieve all shifts from the game for a given player"""
        all_shifts_by_player = {}  # period:(start,end)
        for period in self.shifts_in_game:
            try:
                for shift in self.shifts_in_game[period][player_name]:
                    if period not in all_shifts_by_player:
                        all_shifts_by_player[period] = []
                    all_shifts_by_player[period].append(shift)
            except KeyError as no_shifts_this_period_error:
                continue
        return all_shifts_by_player

    def generate_line_times(self):
        """
        Function to generate the amount of time EACH player played with EACH player IF they were on the ice together
        """
        for team in self.players_in_game:  # Calculate for each team in game
            for player in self.players_in_game[team]:  # Calculate for each player on each team
                shifts_from_player = self.get_all_shifts_per_player(player.name)  # Check every shift from each player
                for period in shifts_from_player:  # For each period
                    for shift in shifts_from_player[period]:  # For each shift in each period
                        for other_player in {p.name for p in self.players_in_game[team] if player.name not in p.name}:
                            try:
                                other_shifts = self.get_all_shifts_per_player(other_player)[period]
                                other_index = find_start_index(other_shifts, shift.start)
                                other_shift = other_shifts[other_index]
                                if is_time_within_range(shift.start, other_shift.start, other_shift.end):
                                    # Get time both players were on the ice
                                    time_shared = get_time_shared(shift, other_shift)
                                    if other_player not in player.ice_time_with_players:
                                        player.ice_time_with_players[other_player] = []
                                    # Add time to player object
                                    player.ice_time_with_players[other_player].append(time_shared)
                                else:
                                    continue  # If they aren't on the ice together, move on
                            except KeyError:  # Catches edge case where player did not have a shift in the same period
                                continue
        '''
        Time together varies greatly between my algo and NST
        http://naturalstattrick.com/game.php?season=20192020&game=20645
        Debug!
        '''
        player.sum_time_together(game_id=self.game_id)
        a = 5
        return self
