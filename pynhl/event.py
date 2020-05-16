import datetime, bisect, pynhl.helpers as helpers


class Event:
    '''
    Class handling all necessary attributes of an EVENT from the NHL Game Data API
    '''

    def __init__(self, event_json, home, away):
        self.event_json = event_json
        self.type_of_event = self.get_type()
        self.players_on = {}  # Team : set(of players)
        self.team_of_player = self.get_team()
        self.other_team = away if self.team_of_player == home else home
        self.period = self.get_period()
        self.time = self.get_time()
        self.x_loc = self.get_x()
        self.y_loc = self.get_y()
        self.score = self.get_score()
        self.strength = 0
        try:
            self.penalty_duration = event_json['result']['penaltyMinutes'] * 60
        except KeyError:
            self.penalty_duration = None
        # Null event_json after all necessary information is fetched, to save memory during runtime
        self.players_involved = {home: set(), away: set()}
        self.get_involved_players()  # Team : set(of players)
        self.event_json = None
        # Features
        self.time_since_last_event = None  # seconds
        self.time_since_last_shot = None  # seconds
        '''
        Flip coordinates for HOME and AWAY differences (so the player graph cna use it asap)
        Calculate distance to center of goal from X/Y for each event
        '''

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
        return (f"Team: {self.team_of_player}, "
                f"Event: {self.type_of_event}, Time: {self.period}:{self.time}, X : {self.x_loc}, Y: {self.y_loc}")

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

    def get_involved_players(self):
        """
        Return the player who DID the event
        [0] is player who did the action, [1] is the player who received the action
        Missed shots do not have the 2nd player, goals/other shots do
        """
        if 'Blocked' in self.type_of_event:
            # Blocked shot is determined by WHO BLOCKS, and not who SHOT it
            # We are reversing that, we care about the shooter, not the blocker
            '''
            When blocked shot occurs, the teams should be reversed
            So self.team_of_player == shooter, other_team == blocker
            '''
            # Swap teams, blocked shot API is related to the blocker, not the shooter
            self.team_of_player, self.other_team = self.other_team, self.team_of_player
            self.players_involved[self.team_of_player].add(self.event_json['players'][1]['player']['fullName'])
            self.players_involved[self.other_team].add(self.event_json['players'][0]['player']['fullName'])
        elif "Goal" in self.type_of_event:
            # A goal may have 0, 1 or 2 assists
            for p in self.event_json['players']:
                if p['player']['fullName'] in self.event_json['result']['description']:
                    self.players_involved[self.team_of_player].add(p['player']['fullName'])
                else:
                    self.players_involved[self.other_team].add(p['player']['fullName'])
        elif 'Missed' in self.type_of_event or 'Giveaway' in self.type_of_event or "Takeaway" in self.type_of_event:
            # These three events involve only one player
            self.players_involved[self.team_of_player].add(self.event_json['players'][0]['player']['fullName'])
        else:
            # Faceoff, Shot, Penalty, Hit
            self.players_involved[self.team_of_player].add(self.event_json['players'][0]['player']['fullName'])
            try:
                self.players_involved[self.other_team].add(self.event_json['players'][1]['player']['fullName'])
            except IndexError:
                # Delay of game penalty, only one player involved here
                print(self.event_json['result']['description'])
        return self

    def get_team(self):
        """
        Returns the team of the player who DID the event
        abbreviated (BUF) format not full (Buffalo Sabres)
        """
        return self.event_json['team']['triCode']

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

    def get_score(self):
        """
        Adds the score at the time of the event
        """
        return self.event_json['about']['goals']['home'], self.event_json['about']['goals']['away']

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

    def determine_event_state(self, home, away):
        """
        Determines the number of skaters on for the event BASED ON HOME v AWAY
        6v5 / 5v5 / 4v4 / 5v4 / 4v3 / etc
        """
        self.strength = f"{len(self.players_on[home])}v{len(self.players_on[away])}"
        return self

    def calculate_time_since_shot(self, events):
        """
        Iterates in reverse order from events, finding hte first "SHOT" type
        subtracts that time difference (if different periods, return will be -1)
        Will also set the time_since_last_event category, it does all the leg work anyways
        """
        for e in reversed(events):
            if not self.time_since_last_event:
                if e.period == self.period:
                    self.time_since_last_event = helpers.subtract_two_time_objects(e.time, self.time)
                else:
                    self.time_since_last_event = -1
            if "Shot" in e.type_of_event or "Goal" in e.type_of_event:
                if e.period == self.period:
                    self.time_since_last_shot = helpers.subtract_two_time_objects(e.time, self.time)
                else:
                    self.time_since_last_shot = -1
                break
        #
        if not self.time_since_last_shot:
            self.time_since_last_shot = -1
        if not self.time_since_last_event:
            self.time_since_last_event = -1
        return self

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
        if helpers.time_check_event(self.time, shift_start.start, shift_start.end, self.type_of_event):
            self.assign_player_to_event(shift_start.player, shift_start.team)
        return self

    def assign_player_to_event(self, player_name, team_of_player):
        """
        Helper function to assign player to the correct team
        Previous functions DETERMINE whether player SHOULD be added to event or not
        """
        if team_of_player not in self.players_on:
            self.players_on[team_of_player] = set()
        self.players_on[team_of_player].add(player_name)
        return self
