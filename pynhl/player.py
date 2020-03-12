import pynhl.game


class Player:
    # Player will have shifts where each shift can have event(s)
    def __init__(self, player_json):
        self.name = player_json["fullName"]
        self.position = player_json["primaryPosition"]["type"]
        self.parse_position_type()
        self.jersey_num = player_json["primaryNumber"]
        self.team = player_json["currentTeam"]["triCode"]

        # Each shift can have events
        self.shifts_per_game = {}  # GameID:[shifts]
        self.direct_events_for = []
        self.direct_events_against = []
        self.events_on_for = []
        self.events_on_against = []

        # {GameID}{Player Name} = [toi_by_shift]
        self.ice_time_with_players = {}
        self.ice_time_with_players_states = {}
        self.ice_time_with_players_scores = {}

        # Calculations/Features
        # self.average_time_per_shift = None
        # self.average_time_since_previous_shift = None
        # self.average_events_per_shift = None
        # self.most_common_teammates_per_game = {}  # Game:Players
        # self.ice_time_per_game = {}  # GameID:Total

    def __eq__(self, other):
        if isinstance(other, Player):
            return self.name == other.name and self.team == other.team
        elif isinstance(other, str):
            return self.name == other
        else:
            raise SystemExit("Not implemented for this type => {}".format(type(other)))

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        # return f"{self.name} : {self.team} : {self.jersey_num}"
        return "{},{},{},{}".format(self.name, self.position, self.team, self.jersey_num)

    def parse_position_type(self):
        """
        Forward -> F
        Defenseman -> D
        Goalie -> G
        """
        if self.position[0] == 'F':
            self.position = 'F'
        elif self.position[0] == 'D':
            self.position = 'D'
        elif self.position[0] == 'G':
            self.position = 'G'
        else:
            raise NotImplementedError
        return self.position

    def sum_time_together(self, game_id):
        """
        Function to sum the values in ice_time_with_players
        Separated by player, by game
        """
        for teammate in self.ice_time_with_players:
            total = sum(self.ice_time_with_players[teammate])
            if teammate not in self.ice_time_summed:
                self.ice_time_summed[teammate] = {}
            self.ice_time_summed[teammate][game_id] = total
        return self

    def sum_all_shifts_per_game(self, game_id):
        """
        Function to sum the shifts in each game to determine total TOI
        """
        temp_period_total = []
        for period in self.shifts_per_game.keys():
            period_sum = 0
            for shift in self.shifts_per_game[period]:
                shared_time = pynhl.game.subtract_two_time_objects(shift.start, shift.end)
                period_sum += shared_time
            temp_period_total.append(period_sum)
        self.ice_time_per_game[game_id] = sum(temp_period_total)

    def add_toi_by_states(self, game_id, dict_states, other_player):
        """
        Mimics toi_by_scores but does it for states as a key, rather than score
        Make this take both?
        """
        # TODO: Think of a way not to re-create the logic with _by_scores
        if game_id not in self.ice_time_with_players_states:
            self.ice_time_with_players_states[game_id] = {}
        if other_player not in self.ice_time_with_players_states[game_id]:
            self.ice_time_with_players_states[game_id][other_player] = {}  # Score:[TOI]
        for state, _time in dict_states.items():
            if state not in self.ice_time_with_players_states[game_id][other_player]:
                self.ice_time_with_players_states[game_id][other_player][state] = []
            self.ice_time_with_players_states[game_id][other_player][state].append(_time)
        return self

    def add_toi_by_scores(self, game_id, dict_scores, other_player):
        """
        Adds the Game-State-Score-Time separated values from a game to the player object

        Requirements - GameID, dicts of states & scores, and the other player
        """
        # player.ice_time_with_players = {Game_ID}{Score}{Other_Player_Name}
        if game_id not in self.ice_time_with_players_scores:
            self.ice_time_with_players_scores[game_id] = {}
        if other_player not in self.ice_time_with_players_scores[game_id]:
            self.ice_time_with_players_scores[game_id][other_player] = {}  # Score:[TOI]
        for score, _time in dict_scores.items():
            if score not in self.ice_time_with_players_scores[game_id][other_player]:
                self.ice_time_with_players_scores[game_id][other_player][score] = []
            self.ice_time_with_players_scores[game_id][other_player][score].append(_time)
            # TODO: Can we somehow maintain the sum here? Let's create a separate function to do this and move on
        return self

    def retrieve_shifts_from_game(self, shifts_from_game):
        """Function to grab all the shifts from a game object"""
        pass

    def get_average_time_per_shift(self):
        """Determine the mean/median from all shifts in a game, across all games as well"""
        pass

    def get_previous_shift_in_game(self):
        """Helper function to fetch the previous shift in a game"""
        pass

    def get_average_time_between_shifts(self):
        """Function to determine how long the player is off the ice"""
        pass

    def get_average_events_per_shift(self):
        """Function to fetch how many events occur per shift the player is on the ice"""

    def determine_players_most_common_partners(self):
        """
        For each game, determine the player's most common two forwards & defenseman
        :return:
        """
        pass
