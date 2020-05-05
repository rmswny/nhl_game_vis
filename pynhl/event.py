import datetime, bisect, pynhl.helpers as helpers


class Event:
    '''
    Class handling all necessary attributes of an EVENT from the NHL Game Data API
    '''

    def __init__(self, event_json):
        self.event_json = event_json
        # Attributes from the JSON
        self.type_of_event = self.get_type()
        self.players_direct_for = set()
        self.players_direct_against = set()
        self.players_on_for = set()
        self.players_on_against = set()
        self.team_of_player = self.get_team()
        self.period = self.get_period()
        self.time = self.get_time()
        self.x_loc = self.get_x()
        self.y_loc = self.get_y()
        self.score = self.get_score()  # ([0],[1]) where 0 is the PLAYERS TEAMS SCORE
        self.strength = 0
        # Null event_json after all necessary information is fetched, to save memory during runtime
        self.event_json = None

    def __lt__(self, other):
        if isinstance(other, Event):
            return self.period < other.period and self.time < other.time
        elif isinstance(other, datetime.time):
            return self.time < other
        elif isinstance(other, int):
            # Checking for periods
            return self.period < other
        elif other.start:
            # For Shift & Event comparison, avoids circular import
            if self.period == other.period:
                return self.time < other.start
            else:
                return self.period < other.period

    def __gt__(self, other):
        return not self.__lt__(other)

    def __eq__(self, other):
        if isinstance(other, Event):
            return self.type_of_event == other.type_of_event and self.period == other.period and self.time == other.time
        else:
            raise NotImplementedError("What to do here, yo {}".format(other))

    def __hash__(self):
        return hash(self.type_of_event) + hash(self.period) + hash(self.time)

    def __str__(self):
        return ("Player : {}, Team: {}, Event: {}, Period: {}, Time: {}, X : {}, Y: {}".format
                (self.players_direct_for, self.team_of_player, self.type_of_event, self.period, self.time, self.x_loc,
                 self.y_loc))

    def __repr__(self):
        return self.__str__()

    def transform_score(self):
        """
        Convert tuple of (PLAYERS_TEAM_SCORE,OTHER_TEAMS_SCORE) -> -(integer) if down, 0 if tied, +(integer) if leading
        """
        self.score = self.score[0] - self.score[1]
        return self

    def get_type(self):
        """
        Return the type of event from NHL API
        ie "result": {"event": "Faceoff"}
        """
        self.type_of_event = self.event_json["result"]["event"]
        return self.type_of_event

    def get_players(self):
        """
        Return the player who DID the event
        [0] is player who did the action, [1] is the player who received the action
        Missed shots do not have the 2nd player, goals/other shots do
        """
        if 'Blocked' in self.type_of_event:
            # API Puts the person who blocked the shot, before the person who shot the shot
            self.players_direct_for = [self.event_json['players'][1]['player']['fullName']]
            self.players_direct_against = [self.event_json['players'][0]['player']['fullName']]
        elif "Goal" in self.type_of_event:
            self.players_direct_for = [x['player']['fullName'] for x in self.event_json['players'] if
                                       "Goalie" not in x['playerType']]
            self.players_direct_against = [x['player']['fullName'] for x in self.event_json['players'] if
                                           "Goalie" in x['playerType']]
        elif 'Missed' in self.type_of_event or 'Giveaway' in self.type_of_event or "Takeaway" in self.type_of_event \
                or "Penalty" in self.type_of_event:
            # Missed shots do not a second player tracked (goalie etc)
            # Takeaways or Giveaways do not track who it was from / given to
            self.players_direct_for, self.players_direct_against = [self.event_json['players'][0]['player'][
                                                                        'fullName']], [None]
        else:
            # Shooter , Goalie, Hitter, Hittee
            self.players_direct_for = [self.event_json['players'][0]['player']['fullName']]
            self.players_direct_against = [self.event_json['players'][1]['player']['fullName']]
        return self

    def get_team(self):
        """
        Returns the team of the player who DID the event
        abbreviated (BUF) format not full (Buffalo Sabres)
        """
        self.team_of_player = self.event_json['team']['triCode']
        return self.team_of_player

    def get_period(self):
        """
        Returns the period when the event occurred
        """
        self.period = self.event_json['about']['period']
        return self.period

    def get_time(self):
        """
        Returns the time, in seconds, when the event occurred
        MM:SS -> SS
        """
        self.time = datetime.datetime.strptime(self.event_json['about']['periodTime'], "%M:%S").time()
        return self.time

    def get_score(self, ):
        """
        Adds the score at the time of the event
        """
        score_at_time_of_event = self.event_json['about']['goals']['home'], self.event_json['about']['goals']['away']
        # score is relative to home team
        return score_at_time_of_event[0] - score_at_time_of_event[1]

    def get_x(self):
        """
        Return x coordinate from event
        """
        self.x_loc = self.event_json['coordinates']['x']
        return self.x_loc

    def get_y(self):
        """
        Return y value from event
        """
        self.y_loc = self.event_json['coordinates']['y']
        return self.y_loc

    def determine_event_state(self, is_for_home_team):
        """
        Determines the number of skaters on for the event
        6v5 / 5v5 / 4v4 / 5v4 / 4v3 / etc

        is_for_home_team checks if PLAYER_DIRECT_FOR.TEAM == GAME.HOME_TEAM
        if true -> for == home_team, false -> against == home_team
        """
        if is_for_home_team:
            self.strength = f"{len(self.players_on_for)}v{len(self.players_on_against)}"
        else:
            self.strength = f"{len(self.players_on_against)}v{len(self.players_on_for)}"
        return self

    def are_goalies_on(self, goalies):
        """
        Intersect the players on with the goalies in the game to determine which goalies are on the ice for the event
        Used for establishing 5v5, 6v5 etc
        """
        players = set(self.players_on_for + self.players_on_against)
        return goalies.intersection(players)

    def get_players_for_event(self, shifts_for_player):
        """
        Determine which players are on the ice for the event (self)
        Input is the shifts for a given player
        Based off this, see if there's a shift for the player during the event
        """
        finder = bisect.bisect_right(shifts_for_player, self)  # Returns index in shifts_for_player
        if finder != 0:
            finder -= 1
        shift_start = shifts_for_player[finder]
        if helpers.time_check_event(self.time, shift_start.start, shift_start.end):
            self.assign_player_to_event(shift_start.player, shift_start.team)
        return self

    def assign_player_to_event(self, player_name, team_of_player):
        """
        Helper function to assign player to the correct team
        Previous functions DETERMINE whether player SHOULD be added to event or not
        """
        if team_of_player == self.team_of_player:
            self.players_on_for.add(player_name)
        else:
            self.players_on_against.add(player_name)
        return self
