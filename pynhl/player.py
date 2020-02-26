class Player:
    # Player will have shifts where each shift can have event(s)
    def __init__(self, player_json):
        self.json_info = player_json
        """
        p_name = self.game_json['gameData']['players'][player]['fullName']  # name
        p_number = self.game_json['gameData']['players'][player]['primaryNumber']
        p_team = self.game_json['gameData']['players'][player]['currentTeam']['triCode']  # team
        """
        self.name = self.json_info["fullName"]
        self.position = self.json_info["primaryPosition"]["type"]
        self.parse_position_type()
        self.jersey_num = self.json_info["primaryNumber"]
        self.team = self.json_info["currentTeam"]["triCode"]
        # Each shift can have events
        self.shifts = {}  # GameID:[shifts]
        self.direct_events_for = []
        self.direct_events_against = []
        self.events_on_for = []
        self.events_on_against = []
        # Calculations/Features
        self.shifts_per_game = None
        self.average_time_per_shift = None
        self.average_time_since_previous_shift = None
        self.average_events_per_shift = None
        self.most_common_teammates_per_game = {}  # Game:Players
        self.ice_time_with_players = {}  # Player Name : [toi_per_game]
        # After creating the object, remove any unnecessary information
        self.cleanup()

    def __eq__(self, name):
        """
        Two players are equal if name==name, team==team
        How to check for it existing other than ensuring a Player object is created
        """
        return self.name == name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        # return f"{self.name} : {self.team} : {self.jersey_num}"
        return "{},{},{},{}".format(self.name, self.position, self.team, self.jersey_num)

    def cleanup(self):
        self.json_info = None

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
