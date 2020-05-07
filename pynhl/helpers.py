import datetime

EVENTS_THAT_CAN_CAUSE_A_STOPPAGE = {"Shot", "Goal", "Penalty"}

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
    "Period Official"
}


def subtract_two_time_objects(lhs, rhs):
    """
    Helper function to return the difference of two time objects in seconds
    """
    lhs = datetime.datetime.combine(datetime.date.today(), lhs)
    rhs = datetime.datetime.combine(datetime.date.today(), rhs)
    difference = rhs - lhs
    return difference.seconds


def seconds_to_minutes(seconds):
    """
    Takes an int input (seconds) and converts to time() object of minutes/seconds
    NHL does not deal with hours so ignoring this functionality
    """
    if isinstance(seconds, int):
        minutes = seconds // 60
        seconds = seconds - (minutes * 60)
        return f"{minutes}:{seconds}"
    else:
        raise SystemExit("Incorrect type for function, must be int")


def do_shifts_overlap(baseline, other):
    """
    Determine if two Shift objets were present at the same time
    """
    # Think about the two scenarios, baseline is on after other 1
    # And other is on after baseline 2
    if baseline.period == other.period:
        if baseline.start >= other.start and baseline.start <= other.end:
            return True
        elif other.start >= baseline.start and other.start <= baseline.end:
            return True
    return False


def time_check_event(event_time, shift_start_time, shift_end_time, event_=None):
    """
    Helper function to check whether an event was present during a shift
    """

    is_player_on = False
    if shift_start_time < event_time < shift_end_time:
        is_player_on = True
    elif shift_start_time == event_time and event_ not in EVENTS_THAT_CAN_CAUSE_A_STOPPAGE:
        # TODO: If start is time of event, then player was 100% on -- ?
        # Start of shift is when event occurs
        is_player_on = True
    elif shift_end_time == event_time and event_ in EVENTS_THAT_CAN_CAUSE_A_STOPPAGE:
        # TODO: End of shift, but got credit for shot/something
        is_player_on = True
    return is_player_on


def get_time_shared(curr_shift, other_shift):
    """
    Finds the shared min and shared max, and subtracts the two time objects
    Returns the value in seconds (timedelta doesn't track minutes/hours)
    """

    lower_bound = max(curr_shift.start, other_shift.start)
    upper_bound = min(curr_shift.end, other_shift.end)
    temp = datetime.datetime.combine(datetime.date.today(), upper_bound) - datetime.datetime.combine(
        datetime.date.today(), lower_bound)
    return temp.seconds, lower_bound, upper_bound
