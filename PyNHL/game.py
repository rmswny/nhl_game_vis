from pynhl.event import Event
from pynhl.player import Player
from pynhl.shift import Shift

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


class Game(Event):
    # Game will have Players who will have shifts and each shift can/will have event(s)
    '''
    This class will take in a JSON DICT of game data
    And parse out the necessary data (players, events)
    Which will then be used to generate Player/Event classes
    '''

    def __init__(self, game_json, shift_json):
        self.game_json = game_json
        self.shift_json = shift_json
        self.game_id = game_json['gameData']['game']['pk']
        self.game_season = game_json['gameData']['game']['season']
        self.home_team = ''
        self.away_team = ''
        self.final_score = ''
        # Functions & Variables to parse Game Data
        self.players_in_game = {}
        self.shifts_in_game = {}
        self.penalties_in_game = []
        self.face_offs_in_game = []
        self.hits_in_game = []
        self.shots_in_game = []
        self.goals_in_game = []
        self.takeaways_in_game = []
        self.giveaways_in_game = []
        # Functions & Variables to parse Shift data
        self.retrieve_shifts_from_game()
        self.retrieve_events_in_game()
        self.fetch_teams_from_game_data()
        self.retrieve_players_in_game()
        self.combine_shifts_events()
        a = 5

    def __str__(self):
        return f"Game ID: {self.game_id} , Season: {self.game_season} : {self.home_team} " \
               f"vs. {self.away_team} Final Score: {self.final_score}"

    def fetch_teams_from_game_data(self):
        """
        Parse self.json_data for HOME/AWAY teams in game
        and final score
        """
        try:
            self.away_team = self.game_json['gameData']['teams']['away']['triCode']
            self.home_team = self.game_json['gameData']['teams']['home']['triCode']
            return self
        except KeyError as k:
            print(k)

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
        self.add_event(temp)

    def add_event(self, temp):
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

    def retrieve_events_in_game(self):
        """
        Parse self.json_data and retrieve all events reported in the game
        Helper function for each type of event, since each have their own little quirks
        """
        events = self.game_json['liveData']['plays']['allPlays']
        for event in events:
            event_type = event['result']['event']  # Type of event
            if event_type in TRACKED_EVENTS:
                new_event = Event(type_of_event=event_type)
                self.parse_event(new_event, event)
                a = 5
            elif event_type not in NOT_TRACKED_EVENTS:
                print(event_type)
        # Update final score based off last event
        self.final_score = "{}-{}".format(new_event.score[1], new_event.score[0])
        return self

    def normalize_score(self, team, score):
        if team == self.home_team:
            score = score[0] - score[1]
        else:
            score = score[1] - score[0]
        return score

    def retrieve_shifts_from_game(self):
        """
        Assign shifts in game to it's corresponding player
        """
        # Creating shift class

        for shifts in self.shift_json['data']:
            team = shifts['teamAbbrev']
            name = "{} {}".format(shifts['firstName'], shifts['lastName'])
            period = int(shifts['period'])
            shift_start = shifts['startTime']
            shift_end = shifts['endTime']
            shift_dur = shifts["duration"]
            score = self.normalize_score(team, (shifts['homeScore'], shifts['visitingScore']))
            temp = Shift(game_id=self.game_id, team=team, name=name, period=period, start=shift_start, end=shift_end,
                         duration=shift_dur,
                         score=score)
            # Shifts separated by player in game
            if temp.period not in self.shifts_in_game:
                self.shifts_in_game[temp.period] = {}
            if temp.name not in self.shifts_in_game[temp.period]:
                self.shifts_in_game[temp.period][temp.name] = []
            self.shifts_in_game[temp.period][temp.name].append(temp)
        return self

    def was_player_on_ice(self, event, on_list, against_list, player, shifts):
        """
        Helper function to determine whether or not the player was on the ice
        for an event

        Appends on/against list if so, returns lists with no change if not
        """
        for shift in shifts:
            if shift.start > event.time:
                break

            if shift.start < event.time <= shift.end:
                if player in self.players_in_game[event.team_of_player]:
                    on_list.append(player)
                    break
                else:
                    against_list.append(player)
                    break
        return on_list, against_list

    def combine_shifts_events(self):
        """
        Create/Find player objects
        For each event, find the players on the ice for the event

        self.players contains the players in this game -TODO: will have to see how to pass in/merge data after this
        """
        for event in self.penalties_in_game:
            temp_on_for = []
            temp_on_against = []
            for player, shifts in self.shifts_in_game[event.period].items():
                temp_on_for, temp_on_against = self.was_player_on_ice(event, temp_on_for, temp_on_against, player,
                                                                      shifts)
            # Has now added all the players to the event
            # Need to the event to the Players event themself
        return self
