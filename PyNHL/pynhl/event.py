class Event:
    def __init__(self, player_for=None, player_against=None, team=None, type_of_event=None, period=None, time=None,
                 score=None, x_loc=None, y_loc=None):
        self.player_for = player_for
        self.player_against = player_against
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
        return ("{},{},{},{},{},{},{},{}".format(self.player_for, self.team_of_player, self.type_of_event, self.period,
                                                 self.time, self.x_loc, self.y_loc))
    def get_type(self, event):
        """
        Return the type of event from NHL API
        ie "result": {"event": "Faceoff"}
        """
        self.e_type = event["result"]["event"]
        return self

    def get_players(self, event):
        """
        Return the player who DID the event
        [0] is player who did the action, [1] is the player who received the action
        Missed shots do not have the 2nd player, goals/other shots do
        """
        if 'Blocked' in self.e_type:
            # API Puts the person who blocked the shot, before the person who shot the shot
            p_for, p_against = event['players'][1]['player']['fullName'], event['players'][0]['player']['fullName']
        elif 'Missed' in self.e_type or 'Giveaway' in self.e_type or "Takeaway" in self.e_type or "Penalty" in self.e_type:
            # Missed shots do not a second player tracked (goalie etc)
            # Takeaways or Giveaways do not track who it was from / given to
            p_for, p_against = event['players'][0]['player']['fullName'], None
        else:
            # Shooter , Goalie
            # Hitter, Hittee
            p_for, p_against = event['players'][0]['player']['fullName'], event['players'][1]['player']['fullName']
        return p_for, p_against

    def get_team(self, event):
        """
        Returns the team of the player who DID the event
        abbreviated (BUF) format not full (Buffalo Sabres)
        """
        e_team = event['team']['triCode']
        return

    def get_period(self, event):
        """
        Returns the period when the event occurred
        """
        e_period = event['about']['period']
        return e_period

    def get_time(self, event):
        """
        Returns the time, in seconds, when the event occurred
        MM:SS -> SS
        """
        temp = datetime.datetime.strptime(event['about']['periodTime'], "%M:%S").time()
        temp = int(datetime.timedelta(minutes=temp.minute, seconds=temp.second).total_seconds())
        return temp

    def get_score(self, event):
        """
        Adds the score at the time of the event
        """
        self.e_score = event['about']['goals']['away'], event['about']['goals']['home']
        return self

    def get_x(self, event):
        """
        Return x coordinate from event
        """
        self.e_x = event['coordinates']['x']
        return self

    def get_y(self, event):
        """
        Return y value from event
        """
        self.e_y = event['coordinates']['y']
        return self

    def retrieve_events_in_game(self):
        """
        Parse self.json_data and retrieve all events reported in the game
        Helper function for each type of event, since each have their own little quirks
        """
        events = self.json_data['liveData']['plays']['allPlays']
        for event in events:
            self.e_type = event['result']['event']  # Type of event
            if self.e_type in self.TRACKED_EVENTS:
                self.events_in_game.add(self.parse_event(event))
            elif self.e_type not in NOT_TRACKED_EVENTS:
                print(self.e_type)
        return self.events_in_game
