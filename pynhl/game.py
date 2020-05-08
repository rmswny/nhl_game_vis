from pynhl.event import Event
from pynhl.player import Player
from pynhl.shift import Shift
import pynhl.helpers as helpers
import bisect


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
        for p_i, player in enumerate(self.players):
            for other_player in {k: v for k, v in self.players.items() if k != player}:
                if self.players[other_player].team == self.players[player].team:
                    # Check to see if the player has been added from this or a previous game
                    if player in self.players[other_player].ice_time_with_players:
                        # Check to see if this game has been done already
                        if self.game_id in self.players[other_player].ice_time_with_players[player]:
                            # Skip this player, they have already been calculated
                            continue
                    # Calculate the time between the two players in this function
                    self.get_time_together_between_two_players(self.players[player], self.players[other_player])

        # Testing function
        # for player in self.players:
        #     t = {p: helpers.seconds_to_minutes(sum(self.players[player].ice_time_with_players[p][self.game_id])) for p
        #          in self.players[player].ice_time_with_players}
        #     a = 5

    def __str__(self):
        return f"Game ID: {self.game_id}, Season: {self.game_season}: {self.home_team} vs. {self.away_team} Final Score: {self.final_score}"

    def __repr__(self):
        return self.__str__()

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
            if type_of_event in helpers.TRACKED_EVENTS:
                temp_event = Event(curr_event, self.home_team, self.away_team)
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
        '''TODO:
        While adding strength to each event, determine the time since previous event & shot (goal as well)
        And also add the players on for each event as a dict
            
            TEAM:set(players)
        
        '''
        goalies = self.home_goalie.union(self.away_goalie)
        for i, event_to_parse in enumerate(self.events_in_game):
            for player in self.players:
                if player not in goalies:
                    event_to_parse.get_players_for_event(self.players[player].shifts[self.game_id])
            # Based off players on the ice, determine the strength (5v5, 6v5 etc)
            event_to_parse.determine_event_state(self.home_team, self.away_team)
            event_to_parse.calculate_time_since_shot(self.events_in_game[:i])
        return self

    def get_time_together_between_two_players(self, player, other):
        """
        For each player in the game, find their teammates & opposition for
        every second they are on the ice in that game
        """
        for p_shift in player.shifts[self.game_id]:
            i = bisect.bisect_left(other.shifts[self.game_id], p_shift)
            if i == len(other.shifts[self.game_id]):
                i -= 1
            closest_shift = other.shifts[self.game_id][i]
            if helpers.do_shifts_overlap(p_shift, closest_shift):
                time_shared, lb, ub = helpers.get_time_shared(p_shift, closest_shift)
                if time_shared > 0:
                    '''
                    Each second of the game has a current score and a game_state
                    How to divide it inside the player class?
                    self.ice_time_with_players[PLAYER_NAME][GAME_ID][STATE][SCORE]
                    [3v3][3v4][3v5][3v6][4v3][4v4][4v5][4v6][5v3][5v4][5v5][5v6][6v3][6v4][6v5][6v6]
                    [-10]...[10] - Score is RELATIVE to player's team (negative if trailing, positive if leading)
                    '''
                    player.add_shared_toi(self.game_id, other.name, time_shared)
                    other.add_shared_toi(self.game_id, player.name, time_shared)

    # def determine_score_during_interval(self, shift, shared_start, shared_end, total_time_together):
    #     """
    #     Given a start & end time, find the scores during the interval
    #     Returns a list of scores during the shift interval
    #     """
    #     # Subsetting the original list
    #     subset_start = bisect.bisect_left(self.events_in_game, shift.period)
    #     subset_end = bisect.bisect_left(self.events_in_game, shift.period + 1)
    #     start_index = bisect.bisect_right(self.events_in_game, shared_start, lo=subset_start, hi=subset_end)
    #     end_index = bisect.bisect_right(self.events_in_game, shared_end, lo=subset_start, hi=subset_end)
    #
    #     # Gettin the time & values here
    #     scores, strengths = {}, {}
    #     if self.events_in_game[start_index:end_index]:
    #         moving_lb = shared_start
    #         # If there is at least one evnet during the shift interval
    #         for e in self.events_in_game[start_index:end_index]:
    #             if e.time > shared_end:
    #                 break
    #             # Grab the difference and the strength/score from the difference
    #             time_diff = helpers.subtract_two_time_objects(moving_lb, e.time)
    #             if e.score not in scores:
    #                 scores[e.score] = 0
    #             if e.strength not in strengths:
    #                 strengths[e.strength] = 0
    #             scores[e.score] += time_diff
    #             strengths[e.strength] += time_diff
    #
    #     else:
    #         # There are no events, grab the start_index -1 strength & scor enad the entire time shared
    #         scores[self.events_in_game[start_index].score] = total_time_together
    #         strengths[self.events_in_game[start_index].strength] = total_time_together
    #     return scores, strengths
