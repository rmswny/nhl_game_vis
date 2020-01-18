class Event:
    """
    Events are shots, hits, faceoffs, takeaways, giveaways, goals, penalties
    """

    def __init__(self, player_for, team, type_of_event, period, time, x_loc=None, y_loc=None):
        self.player_for = player_for
        self.team_of_player = team
        self.type_of_event = type_of_event
        self.period = period
        self.time = time
        self.x_loc = x_loc
        self.y_loc = y_loc

    def __eq__(self, other):
        return self.type_of_event == other.type_of_event and self.period == other.type_of_event \
               and self.time == other.time and self.x_loc == self.x_loc and self.y_loc == self.y_loc

    def __hash__(self):
        return hash(self.type_of_event) + hash(self.period) + hash(self.time)

    def __str__(self):
        return ("{},{},{},{},{},{},{},{}".format(self.player_for, self.team_of_player, self.type_of_event, self.period,
                                                 self.time, self.x_loc, self.y_loc))
