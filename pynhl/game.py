from pynhl.event import Event, find_overlapping_shifts
from pynhl.player import Player
from pynhl.shift import Shift
from datetime import datetime, date, timedelta
from operator import attrgetter
from copy import deepcopy

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
    return temp.seconds, lower_bound, upper_bound


def split_score_or_state_times(total_time, events_container, lb, ub):
    """
    Function to iterate through interval_dict (time:score OR state)
    and find the time per state/score
    ub/lb == datetime.time() objects of minutes:seconds

    This function is used in conjunction with determining the score & state of each second the players
    are on the ice together
    """
    # reference_time = events_container[0]
    if len(events_container) == 1:
        # No events, total_time == the amount of time at the previous score & state
        temp = {v: total_time for v, t in events_container}
    else:
        temp = {v: 0 for v, t in events_container[1:]}
        # At least one event during the shift interval, must do the work to determine times per each  interval
        for score_or_state, event_time in events_container[1:]:
            # Fetch the time spent at the current score/stat
            old_value = temp[score_or_state]
            # Determine how much time to add to the current score/state
            interval_to_add = subtract_two_time_objects(event_time, lb)
            # Add the new chunk of time to the current score/state
            temp[score_or_state] = (old_value + interval_to_add)
            # Reset the lower bound, since lb is used for the subtraction
            lb = event_time
        # Need to add the last value here, ub - i_time
        interval_to_add = subtract_two_time_objects(ub, event_time)
        # Use state from last event, can not change until next event
        old_value = temp[score_or_state]
        # Set the new value, should == total_time
        temp[score_or_state] = (old_value + interval_to_add)
    return temp


def seconds_to_minutes(seconds):
    """
    Takes an int input (seconds) and converts to time() object of minutes/seconds
    NHL does not deal with hours so ignoring this functionality
    """
    if isinstance(seconds, int):
        minutes = seconds // 60
        seconds = seconds - (minutes * 60)
        time_string = f"{minutes}:{seconds}"
        return datetime.strptime(time_string, "%M:%S").time()
    else:
        raise SystemExit("Incorrect type for function, must be int")


class Game:
    # Game will have Players who will have shifts and each shift can have event(s)

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
        self.active_players = self.retrieve_active_players()
        self.events_in_game = []
        self.retrieve_events_in_game()
        # Clear unnecessary data from the game API
        self.cleanup()
        # Extra functionality that doesn't require game/shift json
        self.parse_events_in_game()
        # Determine how much time each player played with every other player
        self.needs_a_new_name_for_shared_toi()
        a = 5

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
            if temp_shift.duration != 0:
                if temp_shift.period not in self.shifts_by_period:
                    self.shifts_by_period[temp_shift.period] = {}
                if temp_shift.player not in self.shifts_by_period[temp_shift.period]:
                    self.shifts_by_period[temp_shift.period][temp_shift.player] = []
                self.shifts_by_period[temp_shift.period][temp_shift.player].append(temp_shift)
            else:
                continue
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
        except UnboundLocalError:
            raise SystemExit("No events in game???")
        self.events_in_game = sorted(self.events_in_game, key=attrgetter("period", "time"))
        return self

    def parse_events_in_game(self):
        """
        Function to find the players who are on ice for the event, and determine the state at time of the event
        :return:
        """
        goalies = self.home_goalie.union(self.away_goalie)
        for i, event_to_parse in enumerate(self.events_in_game):
            event_to_parse.get_players_for_event(self.shifts_by_period[event_to_parse.period], goalies)
            event_to_parse.determine_event_state(event_to_parse.team_of_player == self.home_team)
            self.events_in_game[i] = event_to_parse
        return self

    def retrieve_shifts_for_two_players(self, player_name, other_name):
        """
        Retrieves all shifts for two players
        Input is two player objects, not strings (player.name)
        """
        player_shifts = {}
        other_player_shifts = {}
        for period in self.shifts_by_period:
            try:
                player_shifts[period] = self.shifts_by_period[period][player_name]
            except KeyError as k:
                a = 5
            try:
                other_player_shifts[period] = self.shifts_by_period[period][other_name]
            except KeyError:
                pass
        return player_shifts, other_player_shifts

    def fetch_player_from_string(self, team, player_name):
        """
        Function to retrieve the player object from strings containing the team abbreviation AND name of the player

        This function is used ONLY when KNOWN unique values! .index returns first index, not all indices
        """
        if not isinstance(team, str) or not isinstance(player_name, str):
            raise SystemExit("Improper usage of fetch_player_from_string, requires string inputs")
        try:
            return self.players_in_game[team][self.players_in_game[team].index(player_name)]
        except KeyError as incorrect_team_or_player:
            print(incorrect_team_or_player)
            raise SystemExit("Player and/or team not correct")

    def retrieve_active_players(self):
        """
        Generates a set of player names for all players that had AT LEAST ONE shift in the game
        """
        temp_active = {}
        for period in self.shifts_by_period:
            for player in self.shifts_by_period[period]:
                curr_player = self.shifts_by_period[period][player][0].player
                temp_team = self.shifts_by_period[period][player][0].team
                if temp_team not in temp_active:
                    temp_active[temp_team] = set()
                if curr_player not in temp_active[temp_team]:
                    temp_active[temp_team].add(self.fetch_player_from_string(temp_team, curr_player))
        return temp_active

    def needs_a_new_name_for_shared_toi(self):
        """
        driver function to iterate through players for shared TOI
        """
        temp_active = deepcopy(self.active_players)
        team = "BUF"  # testing variable
        # for team in self.players_in_game:
        for player in self.active_players[team]:
            if player in temp_active[team]:
                temp_active[team].remove(player)
            for other_player in temp_active[team]:
                self.determine_time_together(player, other_player)

    def retrieve_score_and_state_during_interval(self, shift_lb, shift_ub, shift_period):
        """
        Determines the score and state (5v5, 5v4, 3v3 etc) during a time interval (shift.start,shift.end)
        Accounts for changes during the interval

        shift_ is a time object of minutes:seconds
        """
        states_during_interval = ['']  # state:time
        score_during_interval = ['']  # score:time
        for i, event in enumerate(self.events_in_game):
            if event.period == shift_period:
                if shift_lb <= event.time <= shift_ub:
                    states_during_interval.append((event.state, event.time))
                    score_during_interval.append((event.score, event.time))
                elif event.time < shift_lb:
                    # Get state of event JUST BEFORE the interval
                    states_during_interval[0] = (event.state, event.time)
                    score_during_interval[0] = (event.score, event.time)
                    if len(score_during_interval) > 1 or len(states_during_interval) > 1:
                        raise SystemExit("This should never be true!")
            elif event.period > shift_period:
                break
        return states_during_interval, score_during_interval

    def calculate_time_shared(self, shift, other_player_shifts):
        """
        Fetches total time shared and then separated by score & state
        """
        overlapping_shifts = find_overlapping_shifts(shift, other_player_shifts)  # set of indices
        split_states, split_scores = {}, {}
        for s in overlapping_shifts:
            o_shift = other_player_shifts[s]
            time_shared, shared_lb, shared_ub = get_time_shared(shift, o_shift)
            if time_shared == 0:
                continue
            else:
                states, scores = self.retrieve_score_and_state_during_interval(shared_lb, shared_ub, shift.period)
                split_states = split_score_or_state_times(time_shared, states, shared_lb, shared_ub)
                split_scores = split_score_or_state_times(time_shared, scores, shared_lb, shared_ub)
        return split_states, split_scores

    def determine_time_together(self, player, other_player):
        """
        Given two player names, fetch all their shifts and determine how much time they shared
        Parent function will iterate through all players and call this function
        """
        player_shifts, other_player_shifts = self.retrieve_shifts_for_two_players(player.name, other_player.name)
        for period, shifts in player_shifts.items():
            for shift in shifts:
                # Finds time shared
                states, scores = self.calculate_time_shared(shift, other_player_shifts[period])
                if states and scores:
                    # Allows us to know TOI per state, toi per state/score/ and TOI per player
                    player.add_toi_by_scores(self.game_id, states, other_player.name)
                else:
                    # Players didn't share time together, shouldn't do anything
                    continue
        ############################################ Testing stuff here, can remove this later
        try:
            # minutes = player.ice_time_summed[other_player.name][self.game_id] // 60
            # seconds = player.ice_time_summed[other_player.name][self.game_id] - (minutes * 60)
            # _time = f"{minutes}:{seconds}"
            return self
        except KeyError:
            pass
