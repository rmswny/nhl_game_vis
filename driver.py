from pynhl.game import Game
import requests, json, cProfile, pstats, memory_profiler
from bs4 import BeautifulSoup
from io import StringIO, BytesIO


def start_profiler():
    """
    Starts a profiler object to time the program
    """
    profiler = cProfile.Profile()
    profiler.enable()
    return profiler


def print_profiler(profiler):
    """
    Prints the contents of the profiler at the given time
    """
    prof_stream = StringIO()
    stats_from_profiler = pstats.Stats(profiler, stream=prof_stream).sort_stats("tottime")
    stats_from_profiler.print_stats(20)
    return prof_stream.getvalue()


def read_json_data(filename_to_read, is_game=True):
    '''
    Read saved JSON data, from a requests.get(GAME_ID) that is unchanged from source
    is_game determines whether or not to read game data or shift data, which are in separate dirs
    where each file is suffixed with the NHL GAME NUM used in the NHL API
    '''
    if is_game:
        filename_to_read = "games/game_{}.json".format(filename_to_read)
    else:
        filename_to_read = "shifts/shift_{}.json".format(filename_to_read)
    with open(filename_to_read) as json_file:
        data = json.load(json_file)
    return data


def save_json_data(json_data, is_game, game_num, game_dir='games/', shift_dir='shifts/'):
    '''
    Function that saves the JSON data to local dir
    Allows to ignore multiple pinging to NHL API
    '''

    if is_game:
        file_name = "{}game_{}.json".format(game_dir, game_num)
    else:
        file_name = "{}shift_{}.json".format(shift_dir, game_num)
    with open(file_name, 'w+', encoding='utf-8') as of:
        json.dump(json_data, of, ensure_ascii=False, indent=4)



def get_json_data(url):
    '''
    Function to retrieve game data from NHL API
    Leverages the requests module to retrieve JSON object from the game
    Nested dictionary object (JSON) is the return of this function
    '''
    req = requests.get(url)
    return req.json()


if __name__ == "__main__":
    profiler = start_profiler()
    NHL_GAME_NUM = 2019020645

    # NHL_API_URL = 'http://statsapi.web.nhl.com/api/v1/game/{}/feed/live'.format(NHL_GAME_NUM)
    # NHL_SHIFT_URL = 'https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={}'.format(NHL_GAME_NUM)
    # game_data_json = get_json_data(NHL_API_URL)
    # save_json_data(game_data_json,True,NHL_GAME_NUM)
    # shift_data_json = get_json_data(NHL_SHIFT_URL)
    # save_json_data(shift_data_json,False,NHL_GAME_NUM)

    curr_game_shifts = read_json_data(NHL_GAME_NUM, is_game=False)
    curr_game = read_json_data(NHL_GAME_NUM)
    players = []
    
    '''
    Should a list of players be maintained here
    Where each player has a Shifts separated by GameIDs
    And those shifts have teammate data / event data stored in them
    '''
    parsed_game = Game(curr_game, curr_game_shifts)
    print(print_profiler(profiler))

