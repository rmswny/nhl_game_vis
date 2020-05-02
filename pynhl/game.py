from pynhl.event import Event
from pynhl.player import Player
from pynhl.shift import Shift
from datetime import datetime, date, timedelta
from operator import attrgetter
import bisect

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


def get_time_shared(curr_shift, other_shift):
    """
    Finds the shared min and shared max, and subtracts the two time objects
    Returns the value in seconds (timedelta doesn't track minutes/hours)
    """

    lower_bound = max(curr_shift.start, other_shift.start)
    upper_bound = min(curr_shift.end, other_shift.end)
    temp = datetime.combine(date.today(), upper_bound) - datetime.combine(date.today(), lower_bound)
    return temp.seconds, lower_bound, upper_bound


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
        # Home - Away normalized
        self.final_score = f"{self.game_json['liveData']['plays']['allPlays'][-1]['about']['goals']['home']}-" \
                           f"{self.game_json['liveData']['plays']['allPlays'][-1]['about']['goals']['away']}"

        self.players = self.assign_shifts_to_players()
        self.events_in_game = self.retrieve_events_in_game()
        self.score_intervals = self.create_score_interval()

        # remove unnecessary data in memory before prolonged processing
        self.cleanup()

        # Extra functionality that doesn't require game/shift json
        self.add_strength_players_to_event()
        self.strength_intervals = self.create_strength_intervals()

        # Determine how much time each player played with every other player
        self.needs_a_new_name_for_shared_toi()

    def __str__(self):
        return f"Game ID: {self.game_id}, Season: {self.game_season}: {self.home_team} vs. {self.away_team} Final Score: {self.final_score}"

    def cleanup(self):
        self.game_json = None
        self.shift_json = None

    def add_goalie(self, player_object):
        """
        If a player is a goalie, adds it to home/away_goalie variable
        """
        if player_object.team == self.home_team:
            self.home_goalie.add(player_object.name)
        else:
            self.away_goalie.add(player_object.name)
        return self

    def retrieve_players_in_game(self, active_players):
        """
        Parse self.json_data for PLAYERS in the game
        Update self.players_in_game to be a list of [Player objects]
        """
        players_dict = {}
        all_players = self.game_json["gameData"]["players"]
        for player_id in all_players:
            temp = Player(all_players[player_id])
            if temp.name in active_players:
                players_dict[temp.name] = temp
                if 'G' in temp.position:
                    self.add_goalie(temp)
        return players_dict

    def retrieve_shifts_from_game(self):
        """
        Fetch shift information and generate a Shift object for each shift in the game
        """
        shifts = []
        sorted_ins = bisect.insort
        for shift in self.shift_json['data']:
            temp_shift = Shift(self.game_id, self.home_team, shift)
            if temp_shift.duration != 0:
                # Maintains sorted order based off __eq__ inside shift object
                sorted_ins(shifts, temp_shift)
        return shifts

    def assign_shifts_to_players(self):
        """
        Assigns shifts from each period in the game to the player object
        Shifts are separated by [GameID][Period] = [Shifts in the period, in that game]
        """
        shifts = self.retrieve_shifts_from_game()
        players = self.retrieve_players_in_game(active_players=set([s.player for s in shifts]))
        for shift in shifts:
            if self.game_id not in players[shift.player].shifts:
                players[shift.player].shifts[self.game_id] = []
            players[shift.player].shifts[self.game_id].append(shift)
        return players

    def retrieve_events_in_game(self):
        """
        Function to retrieve all events, and their necessary information to the class object
        """
        # All events from the input JSON data
        events = self.game_json['liveData']['plays']['allPlays']
        events_in_game = []
        add_events = bisect.insort
        for curr_event in events:
            type_of_event = curr_event['result']['event']
            if type_of_event in TRACKED_EVENTS:
                temp_event = Event(curr_event)
                add_events(events_in_game, temp_event)
        return events_in_game

    def create_score_interval(self):
        """
        Based off all the goals in the game, create a range of times during the score
        """
        temp = {}  # Time of goal (Per:Time) : Score
        goals = (g for g in self.events_in_game if "Goal" in g.type_of_event)
        for goal in goals:
            if goal.period not in temp:
                temp[goal.period] = {}
            temp[goal.period][goal.time] = goal.score
        return temp

    def create_strength_intervals(self):
        """
        Based off all the strengths in the game, find times where it changes throughout the game
        """
        temp = {}  # Time of state change : New state change
        last_strength = self.events_in_game[0].strength
        for e in self.events_in_game:
            if e.strength != last_strength:
                if e.period not in temp:
                    temp[e.period] = {}
                temp[e.period][e.time] = e.strength
                last_strength = e.strength
        return temp

    def add_strength_players_to_event(self):
        """
        Function to find the players who are on ice for the event
        Alters event.strength based off number of players on for the event
        """
        goalies = self.home_goalie.union(self.away_goalie)
        for i, event_to_parse in enumerate(self.events_in_game):
            for player in self.players:
                if player not in goalies:
                    event_to_parse.get_players_for_event(self.players[player].shifts[self.game_id])
            # Based off players on the ice, determine the strength (5v5, 6v5 etc)
            _on = len(event_to_parse.players_on_for) + len(event_to_parse.players_on_against)
            # Error handling
            if _on > 11 or _on < 9:
                print(i, event_to_parse)
                print(_on)
            #
            event_to_parse.determine_event_state(event_to_parse.team_of_player == self.home_team)
        return self

    def needs_a_new_name_for_shared_toi(self):
        """
        For each player in the game, find their teammates & opposition for
        every second they are on the ice in that game
        """
        for player in self.players:
            player_shifts = self.players[player].shifts[self.game_id]
            for shift in player_shifts:
                # Find the teammates / opposition for each shift
                for other_player in self.players:
                    if other_player != player:
                        self.find_players_on_during_a_shift(shift, self.players[other_player].shifts[self.game_id])

    def find_players_on_during_a_shift(self, plyr_shift, other_player_shifts):
        """
        Determines if two players , during one shift, were on the ice together
        If so, calculate their time shared and create subsets based on score & strength
        """
        index = bisect.bisect_right(other_player_shifts, plyr_shift)
        if index != 0: index -= 1
        closest_shift = other_player_shifts[index]
        time_shared, start_shared, end_shared = get_time_shared(plyr_shift, closest_shift)
        if time_shared > 0:
            '''
            By here, it's decided that they were on the ice together for at least one second
            Now, for tracking purposes, find how the score & strength changed over the course of this interval
            '''
            pass
            a = 5
