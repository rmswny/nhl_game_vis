from pynhl.event import Event
from pynhl.player import Player
from pynhl.shift import Shift
import bisect

TRACKED_EVENTS = {
    "Shot",
    "Faceoff",
    "Giveaway",
    "Takeaway",
    "Penalty",
    "Missed Shot",
    "Blocked Shot",
    "Goal",
    "Hit"
}
NOT_TRACKED_EVENTS = {
    "Period Start",
    "Game Official",
    "Game End",
    "Period End",
    "Game Scheduled",
    "Period Ready",
    "Period Official",
    "Stoppage"
}


class Game(Event):
    # Game will have Players who will have shifts and each shift can/will have event(s)
    '''
    This class will take in a JSON DICT of game data
    And parse out the necessary data (players, events)
    Which will then be used to generate Player/Event classes
    '''

    def __init__(self, game_json, shift_json):
        # Basic game information
        self.game_json = game_json
        self.shift_json = shift_json
        self.game_id = self.game_json['gameData']['game']['pk']
        self.game_season = self.game_json['gameData']['game']['season']
        self.away_team = self.game_json['gameData']['teams']['away']['triCode']
        self.home_team = self.game_json['gameData']['teams']['home']['triCode']
        self.away_goalie = set()
        self.home_goalie = set()
        self.final_score = ''
        # Players and shifts for each game
        self.shifts_in_game = {}
        self.retrieve_shifts_from_game()
        self.players_in_game = {}
        self.retrieve_players_in_game()
        self.events_in_game = []
        self.retrieve_events_in_game()
        # Events of each type
        self.penalties_in_game = []
        self.face_offs_in_game = []
        self.hits_in_game = []
        self.shots_in_game = []
        self.goals_in_game = []
        self.takeaways_in_game = []
        self.giveaways_in_game = []
        a = 5

    def __str__(self):
        return f"Game ID: {self.game_id} , Season: {self.game_season} : {self.home_team} " \
               f"vs. {self.away_team} Final Score: {self.final_score}"

    def is_goalie(self, player_id, player_name, player_team):
        """
        Adds player, if they are the goalie to self.goalie
        """
        temp = self.game_json['gameData']['players'][player_id]['primaryPosition']['code']
        if 'G' in self.game_json['gameData']['players'][player_id]['primaryPosition']['code']:
            if player_team == self.home_team:
                self.home_goalie.add(player_name)
            else:
                self.away_goalie.add(player_name)
        return self

    # Is a goalie, find team and add player to that member variable

    def retrieve_players_in_game(self):
        """
        Parse self.json_data for PLAYERS in the game
        Update self.players_in_game to be a list of [Player objects]
        """
        for player in self.game_json['gameData']['players']:
            # Add all players from game
            p_name = self.game_json['gameData']['players'][player]['fullName']  # name
            p_number = self.game_json['gameData']['players'][player]['primaryNumber']
            p_team = self.game_json['gameData']['players'][player]['currentTeam']['triCode']  # team
            temp = Player(p_name, p_number, p_team)
            if p_team not in self.players_in_game:
                self.players_in_game[p_team] = []
            if temp not in self.players_in_game[p_team]:
                self.players_in_game[p_team].append(temp)
            self.is_goalie(player, p_name, p_team)
        return self.players_in_game

    def separate_events_by_type(self, temp):
        """
        Adds event to it's proper set based off of it's type
        """

        if "Penalty" in temp.type_of_event:
            self.penalties_in_game.append(temp)
        elif "Faceoff" in temp.type_of_event:
            self.face_offs_in_game.append(temp)
        elif "Shot" in temp.type_of_event:
            self.shots_in_game.append(temp)
        elif "Goal" in temp.type_of_event:
            self.goals_in_game.append(temp)
        elif "Hit" in temp.type_of_event:
            self.hits_in_game.append(temp)
        elif "Takeaway" in temp.type_of_event:
            self.takeaways_in_game.append(temp)
        elif "Giveaway" in temp.type_of_event:
            self.giveaways_in_game.append(temp)
        else:
            raise NotImplementedError
        return self

    def get_final_score(self, last_event):
        """
        Retrieve final score from json data
        """
        self.final_score = "{}-{}".format(last_event.score[1], last_event.score[0])
        return self

    def normalize_score(self, team, score):
        if team == self.home_team:
            score = score[0] - score[1]
        else:
            score = score[1] - score[0]
        return score

    def create_shift(self, shift):
        team = shift['teamAbbrev']
        name = "{} {}".format(shift['firstName'], shift['lastName'])
        period = int(shift['period'])
        shift_start = shift['startTime']
        shift_end = shift['endTime']
        shift_dur = shift["duration"]
        score = self.normalize_score(team, (shift['homeScore'], shift['visitingScore']))
        temp = Shift(game_id=self.game_id, team=team, name=name, period=period, start=shift_start, end=shift_end,
                     duration=shift_dur,
                     score=score)
        return temp

    def retrieve_shifts_from_game(self):
        """
        Assign shifts in game to it's corresponding player
        """
        # Creating shift class
        for shift in self.shift_json['data']:
            temp = self.create_shift(shift)
            # Shifts separated by player in game
            if temp.period not in self.shifts_in_game:
                self.shifts_in_game[temp.period] = {}
            if temp.name not in self.shifts_in_game[temp.period]:
                self.shifts_in_game[temp.period][temp.name] = []
            bisect.insort(self.shifts_in_game[temp.period][temp.name], temp)
        return self

    def find_start_index(self, shifts_for_player, event_time):
        """
        Helper function to find the start index for a players shift related to the event start time
        shifts_for_player is already filtered by period
        """
        lower_bound = 0
        for index, shift in enumerate(shifts_for_player):
            if isinstance(shift, Shift) and isinstance(event_time, Event):
                if shift.end > event_time.time:
                    lower_bound = index
                    return lower_bound
        return lower_bound

    def stoppage_before(self):
        """
        Edge cases for adding to on_ice_for
        faceoff at :22 seconds period 1

        Conditional event assignment:

        faceoffs -> if end.time == event.time, that player is NOT on the ice
        penalties -> probably also true
        For instance, faceoffs: if shift.end == event.time, that was player not on the ice
        """

    def retrieve_players_on_ice_for_event(self, event_input):
        """
        Retrieve the players who are on the ice for a given event
        """
        shifts_by_period = self.shifts_in_game[event_input.period]
        for player in shifts_by_period:
            start_index = self.find_start_index(shifts_by_period[player], event_input.time)
            curr_shift = shifts_by_period[player][start_index]
            if curr_shift.start <= event_input.time <= curr_shift.end:
                if curr_shift.team == event_input.team_of_player:
                    event_input.players_on_for.append(player)
                else:
                    event_input.players_on_against.append(player)
        # After all players have been checked, return
        num_players = len(event_input.players_on_for) + len(event_input.players_on_against)
        if num_players < 11 or num_players > 12:
            a = 5
            b = 4
        return event_input

    def are_goalies_on(self, event_input):
        """
        True if both goalies are on ice, false if , at least, one is off the ice
        """
        players = set(event_input.players_on_for + event_input.players_on_against)
        goalies = self.home_goalie.union(self.away_goalie)
        return goalies.intersection(players)

    def determine_players_on(self, list_of_players, goalies):
        num_of_players_excluding_goalie = 0
        if goalies.intersection(set(list_of_players)):
            # If there's a goalie in the list of players, then at most 5 players on ice
            num_of_players_excluding_goalie = len(list_of_players) - 1
        else:
            num_of_players_excluding_goalie = len(list_of_players)
        return num_of_players_excluding_goalie

    def determine_event_state(self, event_input):
        """
        Determines the state at time of the event
        """
        state = "{}v{}"  # team_of_event 3/4/5/6 vs 3/4/5/6
        goalies_on_for_event = self.are_goalies_on(event_input)  # Returns goalies who are on the ice for the event
        for_ = self.determine_players_on(event_input.players_on_for, goalies_on_for_event)
        against_ = self.determine_players_on(event_input.players_on_against, goalies_on_for_event)
        event_input.state = state.format(for_, against_)
        return event_input

    def retrieve_events_in_game(self):
        """
        Parse self.json_data and retrieve all events reported in the game
        Helper function for each type of event, since each have their own little quirks
        """
        events = self.game_json['liveData']['plays']['allPlays']
        add_events = self.events_in_game.append
        for event in events:
            event_type = event['result']['event']  # Type of event
            if event_type in TRACKED_EVENTS:
                temp_event = Event(event)
                temp_event = self.retrieve_players_on_ice_for_event(temp_event)
                temp_event = self.determine_event_state(temp_event)
                add_events(temp_event)
                # self.separate_events_by_type(temp_event)
            elif event_type not in NOT_TRACKED_EVENTS:
                print(event_type)
        self.get_final_score(temp_event)
        return self

# def write_to_file(self):
#     """
#     Write schema to file
#     Iterate through each event and write to same file
#     """
#     # GameID | Event | Period | Time of event | X | Y | Score At Time Of Event | State At Time of Event |
#     # TeamOfEvent | PlayerWhoDidEvent | PlayerWhoReceivedEvent |  Players On FOR | Players On Against |
#     headers = [
#         "Game ID", "Type of Event", "Period", "Time", "X", "Y", "Score", "Strength"  # 5v5/5v4/5v3 etc
#         , "Team of Event", "Player FOR", "Player AGAINST", "Players ON FOR", "Players ON AGAINST"
#     ]
