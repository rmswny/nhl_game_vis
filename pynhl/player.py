import numpy


class Player:
    # Player will have shifts where each shift can have event(s)
    def __init__(self, player_json):
        self.name = player_json["fullName"]
        self.position = player_json["primaryPosition"]["type"]
        self.parse_position_type()
        self.jersey_num = player_json["primaryNumber"]
        self.team = player_json["currentTeam"]["triCode"]
        self.shifts = {}  # [GameID] = [ Shifts in game ]

        # Counting metrics after fetching ALL game data
        # self.shifts_per_game = {}  # GameID:[shifts]
        # self.direct_events_for = []
        # self.direct_events_against = []
        # self.events_on_for = []
        # self.events_on_against = []

        # {GameID}{Player Name} = [toi_by_shift]
        self.ice_time_with_players = {}

        # Calculations/Features/Long term development stuff
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
        return f"{self.name} : {self.team} : {self.jersey_num}"

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

    def add_shared_toi(self, game_id, other_player, time_shared):
        """
        Adds time_shared, which is the time shared on a shift for self.player and other_player

        {Player}{Game_ID} = [ Each index is an int of seconds, each index is a shared value per shift ]
        """
        if other_player not in self.ice_time_with_players:
            self.ice_time_with_players[other_player] = {}
        if game_id not in self.ice_time_with_players[other_player]:
            self.ice_time_with_players[other_player][game_id] = []
        self.ice_time_with_players[other_player][game_id].append(time_shared)
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
