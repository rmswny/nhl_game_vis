import datetime


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
            self.players_direct_for = [self.event_json['players'][1]['player']['fullName']],
            self.players_direct_against = [self.event_json['players'][0]['player']['fullName']]
        elif "Goal" in self.type_of_event:
            self.players_direct_for = [x['player']['fullName'] for x in self.event_json['players'] if
                                       "Goalie" not in x['playerType']]
            self.players_direct_against = [x['player']['fullName'] for x in self.event_json['players'] if
                                           "Goalie" in x['playerType']]
        elif 'Missed' in self.type_of_event or 'Giveaway' in self.type_of_event or "Takeaway" in self.type_of_event or "Penalty" in self.type_of_event:
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
