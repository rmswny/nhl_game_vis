import requests, json
from bs4 import BeautifulSoup
from nhl_classes import Game

def read_json_data(filename_to_read,is_game=True):
    '''
    Read saved JSON data, from a requests.get(GAME_ID) that is unchanged from source
    is_game determines whether or not to read game data or shift data, which are in separate dirs
    where each file is suffixed with the NHL GAME NUM used in the NHL API
    '''
    if is_game:
        filename_to_read = "games/game_{}".format(filename_to_read)
    else:
        filename_to_read = "shifts/shift_{}".format(filename_to_read)
    with open("games/game_{}".format(filename_to_read)) as json_file:
        data = json.load(json_file)
    return data

def save_json_data(json_data, is_game,game_num,game_dir='games/',shift_dir='shifts/'):
    '''
    Function that saves the JSON data to local dir
    Allows to ignore multiple pinging to NHL API
    '''
    if is_game:
        file_name = "{}game_{}.json".format(game_dir,game_num)
    else:
        file_name = "{}shift_{}.json".format(shift_dir,game_num)
    with open(file_name,'w+',encoding='utf-8') as of:
        json.dump(json_data,of,ensure_ascii=False,indent=4)

def get_json_data(URL):
    '''
    Function to retrieve game data from NHL API
    Leverages the requests module to retrieve JSON object from the game
    Nested dictionary object (JSON) is the return of this function
    '''
    req = requests.get(URL)
    return req.json()
    

if __name__ == "__main__":
    NHL_GAME_NUM = 2019020645
    NHL_API_URL = 'http://statsapi.web.nhl.com/api/v1/game/{}/feed/live'.format(NHL_GAME_NUM)
    NHL_SHIFT_URL = 'https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={}'.format(NHL_GAME_NUM)
    # game_data_json = get_json_data(NHL_API_URL)
    # save_json_data(game_data_json,True,NHL_GAME_NUM)
    # shift_data_json = get_json_data(NHL_SHIFT_URL)
    # save_json_data(shift_data_json,False,NHL_GAME_NUM)
    temp = read_json_data(NHL_GAME_NUM)
    


'''
Start by saving game/shift data per game to avoid pinging server
Fetch game events
Fetch shifts
Apply events to shifts
'''