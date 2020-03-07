from pynhl.event import Event, time_check_shift, find_start_index
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
    result = timedelta(minutes=left.minute, seconds=left.second) - timedelta(minutes=right.minute, seconds=right.second)
    if result.days == -1:
        temp = (timedelta(days=1) - result)
        return (temp.seconds // 3600) * 60 + temp.seconds
    else:
        return (result.seconds // 3600) * 60 + result.seconds


def get_time_shared(curr_shift, other_shift):
    """
    Finds the shared min and shared max, and subtracts the two time objects
    Returns the value in seconds (timedelta doesn't track minutes/hours)
    """

    lower_bound = max(curr_shift.start, other_shift.start)
    upper_bound = min(curr_shift.end, other_shift.end)
    temp = datetime.combine(date.today(), upper_bound) - datetime.combine(date.today(), lower_bound)
    return temp.seconds


class Game:
    # Game will have Players who will have shifts and each shift can/will have event(s)

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
        self.shifts_by_period = {}
        self.retrieve_shifts_from_game()
        self.players_in_game = {}
        self.retrieve_players_in_game()
        self.events_in_game = []
        self.retrieve_events_in_game()
        # Clear unnecessary data from the game API
        self.cleanup()
        # Extra functionality that doesn't require game/shift json
        self.parse_events_in_game()
        # self.generate_line_times()
        for p in self.players_in_game["BUF"]:
            self.determine_time_together(self.players_in_game["BUF"][3], p)
        # self.determine_time_together(self.players_in_game["BUF"][3], self.players_in_game["BUF"][17])

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

    def retrieve_shifts_from_game(self):
        """
        Fetch shift information and generate a Shift object for each shift in the game
        """
        for shift in self.shift_json['data']:
            temp_shift = Shift(self.game_id, self.home_team, shift)
            if temp_shift.period not in self.shifts_by_period:
                self.shifts_by_period[temp_shift.period] = {}
            if temp_shift.player not in self.shifts_by_period[temp_shift.period]:
                self.shifts_by_period[temp_shift.period][temp_shift.player] = []
            self.shifts_by_period[temp_shift.period][temp_shift.player].append(temp_shift)
        return self

    def retrieve_events_in_game(self):
        """
        Function to retrieve all events, and their necessary information to the class object
        """
        events = self.game_json['liveData']['plays']['allPlays']
        add_events = self.events_in_game.append
        for index, curr_event in enumerate(events):
            type_of_event = curr_event['result']['event']
            if type_of_event in TRACKED_EVENTS:
                temp_event = Event(curr_event)
                add_events(temp_event)
        try:
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
            event_to_parse.get_players_for_event(self.shifts_by_period[event_to_parse.period],
                                                 self.home_goalie.union(self.away_goalie))
            event_to_parse.determine_event_state()
            self.events_in_game[i] = event_to_parse
        return self

    # def generate_line_times(self):
    #     """
    #     Function to generate the amount of time EACH player played with EACH player IF they were on the ice together
    #     """
    #     for team in self.players_in_game:  # Calculate for each team in game
    #         for player in self.players_in_game[team]:  # Calculate for each player on each team
    #             for period in self.shifts_by_period.keys():  # by Period in the game
    #                 try:
    #                     shifts_from_player = self.shifts_by_period[period][player.name]
    #                     for shift_num, shift in shifts_from_player.items():
    #                         for other_player in [p.name for p in self.players_in_game[team] if
    #                                              player.name not in p.name]:
    #                             try:
    #                                 other_shifts = self.shifts_by_period[period][other_player]
    #                                 other_index = find_start_index(other_shifts.items(), shift.start)
    #                                 other_shift = other_shifts[other_index]
    #                                 if is_time_within_range(shift.start, other_shift.start, other_shift.end) or \
    #                                         is_time_within_range(shift.end, other_shift.start, other_shift.end):
    #                                     # Get time both players were on the ice
    #                                     time_shared = get_time_shared(shift, other_shift)
    #                                     if other_player not in player.ice_time_with_players:
    #                                         player.ice_time_with_players[other_player] = []
    #                                     # Add time to player object
    #                                     player.ice_time_with_players[other_player].append(time_shared)
    #                                 else:
    #                                     continue  # If they aren't on the ice together, move on
    #                             except KeyError:  # Catches edge case where player did not have a shift in the same period
    #                                 continue
    #                 except KeyError as player_not_in_game:
    #                     pass
    #     player.sum_time_together(game_id=self.game_id)
    #     return self

    def determine_time_together(self, player, other_player):
        """
        Given two player names, fetch all their shifts and determine how much time they shared
        Parent function will iterate through all players and call this function
        """
        # Retrieve shifts for both players
        sums = {other_player.name: [], player.name: []}
        player_shifts = {}
        other_player_shifts = {}
        for period in self.shifts_by_period:
            player_shifts[period] = self.shifts_by_period[period][player.name]
            try:
                other_player_shifts[period] = self.shifts_by_period[period][other_player.name]
                sums[player.name].append(sum(
                    [subtract_two_time_objects(x.end, x.start) for x in self.shifts_by_period[period][player.name]]))
                sums[other_player.name].append(sum([subtract_two_time_objects(x.end, x.start) for x in
                                                    self.shifts_by_period[period][other_player.name]]))
            except KeyError:
                pass

        # sum_player = sum(sums[player.name])
        # sum_other = sum(sums[other_player.name])
        # Iterate through the shifts of player
        # Determine shared time for each shift, and add time to both players list
        for period in player_shifts.keys():
            for shift in player_shifts[period]:
                try:
                    # checks the highest index of the shift start and end
                    '''
                    I broke the algorithm again
                    i hate myself and this
                    taking a break
                    '''
                    shift_index = max(find_start_index(other_player_shifts[period], shift.start),
                                      find_start_index(other_player_shifts[period], shift.end))
                    o_shift = other_player_shifts[period][shift_index]
                    if time_check_shift(shift, o_shift):
                        time_shared = get_time_shared(shift, o_shift)
                        if other_player.name not in player.ice_time_with_players:
                            player.ice_time_with_players[other_player.name] = []
                            other_player.ice_time_with_players[player.name] = []
                        player.ice_time_with_players[other_player.name].append(time_shared)
                        other_player.ice_time_with_players[player.name].append(time_shared)
                except KeyError:
                    # Other player did not have a shift in that period
                    pass
        '''
        time is +1 greater than that on NST
        3:38 as opposed to 4:19 for wilson
        Missing 10s with Larsson
        10s with Lazar
        2 m with McCabe 
        '''
        player.sum_time_together(self.game_id)
        s = 0
        try:
            for x in player.ice_time_with_players[other_player.name]:
                s += x
            minutes = player.ice_time_summed[other_player.name][self.game_id] // 60
            seconds = player.ice_time_summed[other_player.name][self.game_id] - (minutes * 60)
            _time = f"{minutes}:{seconds}"
            a = 5
        except KeyError:
            pass
