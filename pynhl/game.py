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
        # Events of each type
        self.penalties_in_game = []
        self.face_offs_in_game = []
        self.hits_in_game = []
        self.shots_in_game = []
        self.goals_in_game = []
        self.takeaways_in_game = []
        self.giveaways_in_game = []
        self.events_in_game = []
        self.retrieve_events_in_game()
        # Functionality to complete the game
        self.combine_shifts_events()
        # Based off number of players on the ice, determine if it's PP/PK/4v4/5v5/6v5 etc
        # If len != 12, if != 6, if goalie isnt on ice, etc
        b = [x for x in self.shots_in_game if len(x.players_on_against) < 6]
        '''
        TODO:
        Determine score & state for each shift & event
            Events are easy to track, count the players and see if both goalies are on the ice
            For shifts, when do shifts have these things change?
                FIRST: Sort all shifts by period then start time
                Assume all shifts are 5v5 UNTIL (PEN,GOAL,?)
                    Then, for all shifts that start > the (P,G,?) but < end_time
                    correct the 
        '''

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

    def parse_event(self, temp, event):
        """
        Parses event from NHL API
        Functions handle edge cases for different events
        """
        temp.game_id = self.game_id
        temp = temp.get_players(event)
        temp = temp.get_team(event)
        temp = temp.get_period(event)
        temp = temp.get_time(event)
        temp = temp.get_score(event)
        temp = temp.get_x(event)
        temp = temp.get_y(event)
        temp = temp.transform_score()
        return temp

    def add_event(self, temp):
        """
        Adds event to it's proper set based off of it's type
        """
        self.events_in_game.append(temp)
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

    def retrieve_players_on_ice_for_event(self, event_input):
        """
        Retrieve the players who are on the ice for a given event
        """
        if not isinstance(event_input, Event):
            return
        shifts = self.shifts_in_game[event_input.period]
        for player_name in shifts:
            """
            Find players first shift before the event
            Check if start_of_shift < event_input.time
            if so, add, based on team
            """
            start_index = bisect.bisect(shifts[player_name], event_input.time)
            temp = shifts[player_name][start_index]
            """
            BISECT goes to index after??
            """
            while shifts[player_name][start_index].start <= event_input.time:
                if temp.team == event_input.team_of_player:
                    event_input.players_on_for.append(player_name)
                else:
                    event_input.players_on_against.append(player_name)
                start_index += 1
        return self

    def retrieve_events_in_game(self):
        """
        Parse self.json_data and retrieve all events reported in the game
        Helper function for each type of event, since each have their own little quirks
        """
        events = self.game_json['liveData']['plays']['allPlays']
        for event in events:
            event_type = event['result']['event']  # Type of event
            if event_type in TRACKED_EVENTS:
                """
                Create event object
                Parse it base on type
                FIND OUT WHO IS ON THE ICE -- DETERMINE PLAYING STATE
                EACH EVENT CARRIES THE SCORE, RETRIEVE THAT 
                """
                new_event = Event(type_of_event=event_type)
                new_event = self.parse_event(new_event, event)
                self.retrieve_players_on_ice_for_event(new_event)
                self.add_event(new_event)
            elif event_type not in NOT_TRACKED_EVENTS:
                print(event_type)
        self.get_final_score(new_event)
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
