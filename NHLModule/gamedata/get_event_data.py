import requests, gamedata.get_shifts
import nhl_classes.all_classes as nhlc
from operator import attrgetter


def update_score(current_score, is_home):
    temp = current_score.split(':')
    if is_home:
        score = str(int(temp[1]) + 1)
        temp[1] = score
        current_score = ':'.join(temp)
    else:
        score = str(int(temp[0]) + 1)
        temp[1] = score
        current_score = ':'.join(temp)
    return current_score


def update_shots(shot_event, players_on_ice):
    for player in players_on_ice:
        if player.team == shot_event.team:
            player.shots['for'] += 1
            if shot_event.event_by == player.name:
                player.personal_shots[shot_event.type_of_event] += 1
        else:
            player.shots['against'] -= 1


def generate_on_ice_players(game_shifts, event):
    current_players_on_ice = []
    for player, shifts in game_shifts.items():
        for shift in shifts:
            if shift.start_time > event.time:
                # Player was not on for event, moving on..
                break
            elif shift.start_time < event.time < shift.end_time and shift.period == event.period:
                # Checking if player was on ice
                current_players_on_ice.append(shift.player)
    return current_players_on_ice


def merge_events_shifts(game_events, game_shifts):
    current_score = "0:0"  # away:home
    is_powerplay = False
    for event in game_events:
        # Finds players who are currently on the ice
        current_players_on_ice = generate_on_ice_players(game_shifts, event)
        if len(current_players_on_ice) < 10:
            a = 5
        elif len(current_players_on_ice) < 11:
            a = 5
        elif len(current_players_on_ice) < 12:
            a = 5
        # Determine the team who caused the event
        # Current players now made, now +/- for each player
        if 'Shot' in event.type_of_event or 'Goal' in event.type_of_event:
            update_shots(event, current_players_on_ice)
        # elif 'Penalty' in event.type_of_event:
        #     player.penalties['for'] -= 1
        # elif 'Hit' in event.type_of_event:
        #     pass
        # elif 'away' in event.type_of_event:
        #     # Give/Takeaway
        #     pass
    a = 5


def generate_event(input_event):
    player_name = input_event['players'][0]['player']['fullName']
    event_type = input_event['result']['event']
    event_period = input_event['about']['period']
    event_time = input_event['about']['periodTime']
    event_x_loc = input_event['coordinates']['x']
    event_y_loc = input_event['coordinates']['y']
    event_by_team = nhlc.TEAM_DICT[input_event['team']['name']]
    temp = nhlc.Event(
        type_of_event=event_type,
        event_by=player_name,
        team=event_by_team,
        period=event_period,
        time=event_time,
        x_loc=event_x_loc,
        y_loc=event_y_loc
    )
    if 'Penalty' in event_type:
        try:
            temp.penalty_length = int(input_event['result']['penaltyMinutes']) * 60
            if len(input_event['players']) > 1:
                temp.drew_by = input_event['players'][1]['player']['fullName']
        except:
            print('penalty minutes is not a num?')

    return temp


def get_events(all_events):
    event_list = []
    for event in all_events:
        type_of_event = event['result']['event']
        if 'Shot' in type_of_event:
            event_list.append(generate_event(event))
            # print(shot_list[:-1].type_of_shot) # Shot check
        elif 'Goal' in type_of_event:
            # Goals are shots!
            event_list.append(generate_event(event))
        elif 'Penalty' in type_of_event:
            # Penalties for score effects tracking
            event_list.append(generate_event(event))
        # Do faceoffs, takeaways,giveaways
        # A check to confirm all events are within the EVENT_SET
        # else:
        # print("Events I don't care about? -> {}".format(event['result']['event']))
    # [print("p: {} t: {}".format(x.period,x.time)) for x in a]
    return sorted(event_list, key=attrgetter("period", "time"), reverse=False)


def retrieve_players(all_players):
    team_player_set = {}
    for pid in all_players.keys():
        # name = all_players[pid]['fullName']
        # team = all_players[pid]['currentTeam']['name']
        # p_num = all_players[pid]['primaryNumber']
        temp_player = nhlc.Player(all_players[pid]['fullName'], all_players[pid]['currentTeam']['name'],
                                  all_players[pid]['primaryNumber'])
        if temp_player.team not in team_player_set:
            # Dict by teams
            team_player_set[temp_player.name] = [temp_player]
        else:
            for player in team_player_set[temp_player.name]:
                if player == temp_player:
                    break
            # All players are different, duplicate name but different team
            temp_player[temp_player.name].append(temp_player)
    return team_player_set


def worthy_game():
    NHL_GAME_NUM = '2019020007'
    NHL_API_URL = 'http://statsapi.web.nhl.com/api/v1/game/{}/feed/live'.format(
        NHL_GAME_NUM)
    req = requests.get(NHL_API_URL)
    while req.status_code == 200:
        game_json = req.json()
        away_team = game_json['gameData']['teams']['away']['name']
        home_team = game_json['gameData']['teams']['home']['name']
        if 'Buf' in away_team or 'Buf' in home_team:
            return game_json, NHL_GAME_NUM
        else:
            NHL_GAME_NUM = int(NHL_GAME_NUM) + 1


def game_data():
    game_json, game_num = worthy_game()
    # Retrieve dict of players from each game
    game_players = retrieve_players(game_json['gameData']['players'])
    # Retrieve all events from each game
    game_events = get_events(game_json['liveData']['plays']['allPlays'])
    # Retrieve shift(s) for every player
    game_shifts = gamedata.get_shifts.shift_data(game_num, game_players)
    # Combine shift and event information for tabular output
    merge_events_shifts(game_events, game_shifts)
    # Visualize results
    a = 5


if __name__ == "__main__":
    # http://statsapi.web.nhl.com/api/v1/game/2019020007/feed/live
    game_data()
