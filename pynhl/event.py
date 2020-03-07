import pynhl.game
import datetime

EVENTS_THAT_CAN_CAUSE_A_STOPPAGE = {
    "Shot",
    "Goal",
    "Penalty"
}


def time_check_event(check_time, start_time, end_time, event_=None):
    """
    Helper function to check whether an event was present during a shift
    """

    is_player_on = False
    if start_time < check_time < end_time:
        is_player_on = True
    elif start_time == check_time and event_ not in EVENTS_THAT_CAN_CAUSE_A_STOPPAGE:
        # Start of shift is when event occurs
        is_player_on = True
    elif end_time == check_time and event_ in EVENTS_THAT_CAN_CAUSE_A_STOPPAGE:
        is_player_on = True
    return is_player_on


def time_check_shift(shift_1, shift_2):
    """
    Helper function to determine whether or not two players were on the ice at a given time
    """
    on_together = False
    """
    Cases:
    -Normal case, time falls between the two range
    -When shift_2 player is already on the ice?
    -Other cases? 
        start is before, end2 is before end1        
    """
    if shift_2.start <= shift_1.start <= shift_2.end:
        on_together = True
    elif shift_2.start <= shift_1.end <= shift_2.end:
        on_together = True
    elif shift_1.start <= shift_2.start <= shift_1.end:
        on_together = True
    elif shift_1.start <= shift_2.end <= shift_1.end:
        on_together = True

    return on_together


def find_start_index(shifts_for_player, time_check):
    """
    Helper function to find the start index for a players shift related to the event start time
    shifts_for_player is already filtered by period
    """
    close_lb = 0
    for index, shift in enumerate(shifts_for_player):
        if shift.end < time_check:
            close_lb = index
        if shift.end > time_check:
            break
    return close_lb


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

    def determine_event_state(self):
        """
        Determines the number of skaters on for the event
        6v5 / 5v5 / 4v4 / 5v4 / 4v3 / etc
        """
        # Finds the goalies currently on the ice, in the case of injury/switches
        # Fetch number of skates for home/away team
        self.state = "{}v{}".format(len(self.players_on_for), len(self.players_on_against))
        return self

    def get_players_for_event(self, shifts_in_period, goalies):
        """
        Determine which players are on the ice for the event
        """
        for player in shifts_in_period:
            # Find the latest shift where the start is less than the time of the event (ignore everything before/after)
            shift_index = find_start_index(shifts_in_period[player], self.time)
            shift_ = shifts_in_period[player][shift_index]
            # If true, player was on for the event. False, ignore and move to the next player
            is_on = time_check_event(self.time, shift_.start, shift_.end, self.type_of_event)
            if is_on:
                # Add player to the event
                self.assign_player_to_event(shifts_in_period[player][shift_index], player, goalies)
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

    def are_goalies_on(self, goalies):
        """
        Intersect the players on with the goalies in the game to determine which goalies are on the ice for the event
        Used for establishing 5v5, 6v5 etc
        """
        players = set(self.players_on_for + self.players_on_against)
        return goalies.intersection(players)
