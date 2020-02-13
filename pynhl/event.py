import datetime


class Event:
    '''
    Class handling all necessary attributes of an EVENT from the NHL Game Data API
    '''

    def __init__(self, game_id=None, players_for=None, players_against=None, team=None, type_of_event=None, period=None,
                 time=None, score=None, x_loc=None, y_loc=None):
        self.game_id = game_id
        self.players_involved_for = players_for  # Player who shot the puck, did the penalty/hit, won the faceoff, took/gave away the puck
        self.players_involved_against = players_against  # Player who saved/blocked the puck, took the hit/penalty, lost the faceoff
        self.team_of_player = team
        self.type_of_event = type_of_event
        self.period = period
        self.time = time
        self.x_loc = x_loc
        self.y_loc = y_loc
        self.score = score  # ([0],[1]) where 0 is the PLAYERS TEAMS SCORE
        self.state = 0
        self.players_on_for = []
        self.players_on_against = []
        # TODO: Attributes to add later

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

    def get_type(self, event):
        """
        Return the type of event from NHL API
        ie "result": {"event": "Faceoff"}
        """
        self.type_of_event = event["result"]["event"]
        return self

    def get_players(self, event):
        """
        Return the player who DID the event
        [0] is player who did the action, [1] is the player who received the action
        Missed shots do not have the 2nd player, goals/other shots do
        """
        if 'Blocked' in self.type_of_event:
            # API Puts the person who blocked the shot, before the person who shot the shot
            self.players_involved_for = [event['players'][1]['player']['fullName']],
            self.players_involved_against = [event['players'][0]['player']['fullName']]
        elif "Goal" in self.type_of_event:
            self.players_involved_for = [x['player']['fullName'] for x in event['players'] if
                                         "Goalie" not in x['playerType']]
            self.players_involved_against = [x['player']['fullName'] for x in event['players'] if
                                             "Goalie" in x['playerType']]
        elif 'Missed' in self.type_of_event or 'Giveaway' in self.type_of_event \
                or "Takeaway" in self.type_of_event or "Penalty" in self.type_of_event:
            # Missed shots do not a second player tracked (goalie etc)
            # Takeaways or Giveaways do not track who it was from / given to
            self.player_for, self.player_against = [event['players'][0]['player']['fullName']], [None]
        else:
            # Shooter , Goalie, Hitter, Hittee,
            self.player_for, self.player_against = [event['players'][0]['player']['fullName']], \
                                                   [event['players'][1]['player']['fullName']]
        return self

    def get_team(self, event):
        """
        Returns the team of the player who DID the event
        abbreviated (BUF) format not full (Buffalo Sabres)
        """
        self.team_of_player = event['team']['triCode']
        return self

    def get_period(self, event):
        """
        Returns the period when the event occurred
        """
        self.period = event['about']['period']
        return self

    def get_time(self, event):
        """
        Returns the time, in seconds, when the event occurred
        MM:SS -> SS
        """
        self.time = datetime.datetime.strptime(event['about']['periodTime'], "%M:%S").time()
        return self

    def get_score(self, event):
        """
        Adds the score at the time of the event
        """
        self.score = event['about']['goals']['away'], event['about']['goals']['home']
        return self

    def get_x(self, event):
        """
        Return x coordinate from event
        """
        self.x_loc = event['coordinates']['x']
        return self

    def get_y(self, event):
        """
        Return y value from event
        """
        self.y_loc = event['coordinates']['y']
        return self
