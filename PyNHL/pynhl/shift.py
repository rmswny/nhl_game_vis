class Shift:
    # Shift can have events
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = ''
        self.events = []
