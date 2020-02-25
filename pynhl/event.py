import datetime

EVENTS_THAT_CAN_CAUSE_A_STOPPAGE = {
    "Shot",
    "Goal",
    "Penalty"
}


class Event:
    '''
    Class handling all necessary attributes of an EVENT from the NHL Game Data API
    '''

    def __init__(self, event_json):
        self.event_json = event_json
        # Attributes from the JSON
        self.type_of_event = self.get_type()
        self.players_direct_for = []
        self.players_direct_against = []
        self.players_on_for = []
        self.players_on_against = []
        self.get_players()
        self.team_of_player = self.get_team()
        self.period = self.get_period()
        self.time = self.get_time()
        self.x_loc = self.get_x()
        self.y_loc = self.get_y()
        self.score = self.get_score()  # ([0],[1]) where 0 is the PLAYERS TEAMS SCORE
        self.state = 0
        # Null event_json after all necessary information is fetched, to save memory during runtime
        self.event_json = None

    def __eq__(self, other):
        return self.type_of_event == other.type_of_event and self.period == other.type_of_event \
               and self.time == other.time and self.x_loc == self.x_loc and self.y_loc == self.y_loc

    def __hash__(self):
        return hash(self.type_of_event) + hash(self.period) + hash(self.time)

    def __str__(self):
        return ("Player : {}, Team: {}, Event: {}, Period: {}, Time: {}, X : {}, Y: {}".format
                (self.player_for, self.team_of_player, self.type_of_event, self.period, self.time,
                 self.x_loc, self.y_loc))

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
        self.score = self.event_json['about']['goals']['away'], self.event_json['about']['goals']['home']
        return self.score

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

    ## Functions from game.py

    def determine_event_state(self):
        """
        Determines the number of skaters on for the event
        6v5 / 5v5 / 4v4 / 5v4 / 4v3 / etc
        """
        # Finds the goalies currently on the ice, in the case of injury/switches
        # Fetch number of skates for home/away team
        self.state = "{}v{}".format(len(self.players_on_for), len(self.players_on_against))
        return self

    def retrieve_players_on_ice_for_event(self, shifts_in_period, goalies):
        """
        Retrieve the players who are on the ice for a given event
        """
        for player in shifts_in_period:
            start_index = self.find_start_index(shifts_in_period[player])
            self.determine_player_to_event(player, shifts_in_period[player][start_index], goalies)
        return self

    def determine_player_to_event(self, current_player, current_shift, goalies):
        """
        Some events have the same time as the previous event. This means a stoppage must've occurred.
        This leads to an error in the conditional statements where some events have >6 players on the ice
        This function will then ensure which players are on the ice for an event, when the previous event has the same
        time as the new event
        """
        '''
        Logic for cases:
        < and < -- simple case, shift starts before event and ends after event
        shift.start==event.time AND a stoppage is at the same time
            implying that the player came off the bench, during a whistle, and began play
        shift.end==event.time
            Edge case: event that causes a whistle. Penalty/Goal/Shot
        '''
        if current_shift.start < self.time < current_shift.end:
            self.assign_player_to_event(current_shift, current_player, goalies)
        elif current_shift.start == self.time and self.type_of_event not in EVENTS_THAT_CAN_CAUSE_A_STOPPAGE:
            # Start of shift is when event occurs
            self.assign_player_to_event(current_shift, current_player, goalies)
        elif current_shift.end == self.time and self.type_of_event in EVENTS_THAT_CAN_CAUSE_A_STOPPAGE:
            # TODO: IF event caused a stoppage, the player was on (penalty, goal) VERSUS events following a stoppage (faceoff)
            self.assign_player_to_event(current_shift, current_player, goalies)
        return self

    def assign_player_to_event(self, current_shift, current_player, goalies):
        """
        Helper function to assign player to the correct team
        Previous functions DETERMINE whether player SHOULD be added to event or not

        current_shift: Shift object
        current_event: Event object
        current_player: Player object
        """
        if current_player not in goalies:
            if current_shift.team == self.team_of_player:
                self.players_on_for.append(current_player)
            else:
                self.players_on_against.append(current_player)
            return self

    def find_start_index(self, shifts_for_player):
        """
        Helper function to find the start index for a players shift related to the event start time
        shifts_for_player is already filtered by period
        """
        lower_bound = 0
        for index, shift in enumerate(shifts_for_player):
            if shift.start <= self.time:
                if index > lower_bound:
                    lower_bound = index
            else:
                break
        return lower_bound

    def are_goalies_on(self, goalies):
        """
        Intersect the players on with the goalies in the game to determine which goalies are on the ice for the event
        Used for establishing 5v5, 6v5 etc
        """
        players = set(self.players_on_for + self.players_on_against)
        return goalies.intersection(players)
