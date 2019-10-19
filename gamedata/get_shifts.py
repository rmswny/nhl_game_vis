from operator import itemgetter, attrgetter
import requests
from nhl_classes.all_classes import Shift, Player, TEAM_DICT


def get_player(game_players, name, team):
    for player in game_players[name]:
        if name == player.name and team == player.team:
            return player


def shift_data(gameID, game_players):
    '''
    gameID for the shift URL
    game_players for list of players
    '''
    # http://www.nhl.com/stats/rest/shiftcharts?cayenneExp=gameId=2018020005
    game_url = 'http://www.nhl.com/stats/rest/shiftcharts?cayenneExp=gameId={}'.format(
        gameID)
    response = requests.get(game_url)  # 200 for success
    json_data = response.json()  # json dict returned
    shift_dict = {}
    for item in json_data['data']:
        name = item['firstName'] + ' ' + item['lastName']
        temp_player = get_player(game_players, name, TEAM_DICT[item['teamName']])
        temp_shift = Shift(temp_player, item['period'],
                           item['startTime'], item['endTime'])
        if name in shift_dict:
            shift_dict[name].extend([temp_shift])
        else:
            shift_dict[name] = [temp_shift]
    # A dict of player names where their shifts are sorted by periods then start time (ascending order)
    # period 1 00:00 -> period 3 20:00
    return {k: sorted(v, key=attrgetter("period", "start_time")) for k, v in shift_dict.items()}
