from pynhl.event import Event
from pynhl.player import Player
from pynhl.shift import Shift
import pynhl.helpers as helpers
import bisect, datetime


class Game:
    # Game will have Players who will have shifts and each shift can have event(s)

    # Edit for reading a JSON input or a CSV one
    def __init__(self, game_json, shift_json):
        # Basic game information provided by the API
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

        # remove unnecessary data in memory before prolonged processing
        self.cleanup()

        # Extra functionality that doesn't require game/shift json
        self.add_strength_players_to_event()

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
        for player in self.players:
            for o in self.players[player].ice_time_with_players:
                x = self.players[player].ice_time_with_players[o][self.game_id]
                s_x = [helpers.seconds_to_minutes(y) for y in x.values()]
                a = 5

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

    def add_strength_players_to_event(self):
        """
        Function to find the players who are on ice for the event
        Alters event.strength based off number of players on for the event
        """
        # TODO: When a penalty occurs, the play receiving the penalty should be included
        goalies = self.home_goalie.union(self.away_goalie)
        for i, event_to_parse in enumerate(self.events_in_game):
            for player in self.players:
                if player not in goalies:
                    event_to_parse.get_players_for_event(self.players[player].shifts[self.game_id])
            # Based off players on the ice, determine the strength (5v5, 6v5 etc)
            event_to_parse.determine_event_state(self.home_team, self.away_team)
            event_to_parse.calculate_time_since_shot(self.events_in_game[:i])
        return self

    def get_period_range_in_events_list(self, period_to_find):
        temp = {}
        if period_to_find not in temp:
            per_index = bisect.bisect_left(self.events_in_game, period_to_find)
            per_end = bisect.bisect_left(self.events_in_game, period_to_find + 1)
            return (per_index, per_end)

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
            period_ranges = {}
            if helpers.do_shifts_overlap(p_shift, closest_shift):
                time_shared, time_lb, time_ub = helpers.get_time_shared(p_shift, closest_shift)
                if time_shared > 0:
                    if p_shift.period not in period_ranges:
                        period_ranges[p_shift.period] = self.get_period_range_in_events_list(p_shift.period)
                    values = self.separate_time_shared_by_strengths(time_lb, time_ub, time_shared,
                                                                    period_ranges[p_shift.period][0],
                                                                    period_ranges[p_shift.period][1])
                    swapped = helpers.swap_states(values)
                    # TODO: Think of better location for this function, ugly
                    if player.team == self.away_team:
                        player.add_shared_toi(self.game_id, other.name, swapped)
                    else:
                        player.add_shared_toi(self.game_id, other.name, values)
                    if other.team == self.away_team:
                        other.add_shared_toi(self.game_id, player.name, swapped)
                    else:
                        other.add_shared_toi(self.game_id, player.name, values)

    def separate_time_shared_by_strengths(self, lb, ub, time_shared, low_i, high_i):
        """
        Splits the time shared between two players on a shift (time_shared) by the intervals found in
        self.strength_intervals

        lb / ub refer to the interval shared by the two players, a time between 00:00 and 19:59
        low_i/high_i refer to the start and end index for a given period in the game
        """

        start = bisect.bisect_left(self.events_in_game, lb, low_i, high_i)
        if start > 0:
            start -= 1
        end = bisect.bisect_left(self.events_in_game, ub, low_i, high_i)
        if end < len(self.events_in_game):
            end += 1
        #
        prev_strength = self.events_in_game[start].strength
        strengths_during_shift = {prev_strength: 0}  # strength:seconds
        for event in self.events_in_game[start:end]:
            # Break immediately, don't care about any events anymore
            if event.time > ub:
                break
            # Add strength to dict
            if event.strength not in strengths_during_shift:
                strengths_during_shift[event.strength] = 0
            if event.time < lb:
                # Gets the strength just before the beginning of the shift
                prev_strength = event.strength
                strengths_during_shift[prev_strength] = 0
            elif event.time < ub:
                diff = helpers.subtract_two_time_objects(lb, event.time)
                # Set the new lower bound
                lb = event.time
                # Add the difference and on to the next
                strengths_during_shift[event.strength] += diff
        # Generate the remaining time here
        '''
        event.strength shouldn't be used, what's the alternative?
        Assignment is taking the last strength and and finding the difference between the remaining time left and whats
        already been assigned to the two players
        
        But by taking the iterated event assumes that the event was one during their time together, when that isn't true
        
        So, use last strength in strengths_during_shift instead?
            Fine, but what if empty?
                If empty, self.events[start].strength should be used?
        '''
        strengths_during_shift[prev_strength] += time_shared - sum(strengths_during_shift.values())
        # Ignoring strengths with a time of 0
        return {k: v for k, v in strengths_during_shift.items() if v != 0}
