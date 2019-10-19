import requests
import json
from operator import attrgetter, itemgetter


class Shift:

    def __init__(self, player_name, period, start_time, end_time):
        self.player_name = player_name
        self.period = period
        self.start_time = start_time
        self.end_time = end_time
        self.duration = self.calc_duration()

    def __eq__(self, other):
        return self.player_name == other.player_name and self.start_time == other.start_time

    def __hash__(self):
        return hash(self.player_name)

    def calc_duration(self):
        return self.start_time - self.end_time