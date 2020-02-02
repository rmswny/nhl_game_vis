import datetime


class Event:
    def __init__(self, game_id=None, player_for=None, player_against=None, team=None, type_of_event=None, period=None,
                 time=None, score=None, x_loc=None, y_loc=None):
        self.game_id = game_id
        self.players_for = player_for
        self.players_against = player_against
        self.team_of_player = team
        self.type_of_event = type_of_event
        self.period = period
        self.time = time
        self.x_loc = x_loc
        self.y_loc = y_loc
        self.score = score  # tuple of (away_goals,home_goals) transform to -> Tied, Leading, Trailing
        # self.state = 3v5, 4v5, 3v4, 3v3,4v4,5v5, 5v3,5v4,6v5
        # self.gwg = True/False
        # self.empty_net = True/False

    def __eq__(self, other):
        return self.type_of_event == other.type_of_event and self.period == other.type_of_event \
               and self.time == other.time and self.x_loc == self.x_loc and self.y_loc == self.y_loc

    def __hash__(self):
        return hash(self.type_of_event) + hash(self.period) + hash(self.time)

    def __str__(self):
        return ("Player : {}, Team: {}, Event: {}, Period: {}, Time: {}, X : {}, Y: {}".format
                (self.player_for, self.team_of_player, self.type_of_event, self.period, self.time,
                 self.x_loc, self.y_loc))

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
            self.players_for, self.players_against = [event['players'][1]['player']['fullName']], \
                                                     [event['players'][0]['player']['fullName']]
        elif "Goal" in self.type_of_event:
            self.players_for = [x['player']['fullName'] for x in event['players'] if "Goalie" not in x['playerType']]
            self.players_against = [x['player']['fullName'] for x in event['players'] if "Goalie" in x['playerType']]
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
