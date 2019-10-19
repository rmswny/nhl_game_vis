def time_to_seconds(time):
    # given a string MM:SS
    # convert to seconds
    sep = time.find(':')
    minutes = int(time[:sep])
    seconds = int(time[sep+1:])
    return (minutes*60)+(seconds)


class Event:
    SET_OF_EVENTS = {
        'Takeaway',
        'Blocked Shot',
        'Giveaway',
        'Penalty',
        'Hit',
        'Missed Shot',
        'Goal',
        'Faceoff',
        'Shot'
    }
    # define if the scoring state of the shot
    # list of who is on the ice for each shot

    def __init__(self, type_of_event, event_by, period, time, x_loc, y_loc):
        self.type_of_event = type_of_event
        self.event_by = event_by
        self.period = period
        self.time = time_to_seconds(time)
        self.x_loc = x_loc
        self.y_loc = y_loc
