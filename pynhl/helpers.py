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


def subtract_two_time_objects(smaller, bigger):
    """
    Helper function to return the difference of two time objects in seconds
    """
    smaller = datetime.datetime.combine(datetime.date.today(), smaller)
    bigger = datetime.datetime.combine(datetime.date.today(), bigger)
    difference = bigger - smaller
    return difference.seconds


def seconds_to_minutes(seconds):
    """
    Takes an int input (seconds) and converts to time() object of minutes/seconds
    NHL does not deal with hours so ignoring this functionality
    """
    if isinstance(seconds, int):
        minutes = seconds // 60
        seconds = seconds - (minutes * 60)
        if seconds < 10:
            seconds = f"0{seconds}"
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
        if other.start <= baseline.start <= other.end:
            return True
        elif baseline.start <= other.start <= baseline.end:
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
        # Handles faceoffs, ignores penalties/goals/shots that caused a stoppage
        is_player_on = True
    elif shift_end_time == event_time and event_ in EVENTS_THAT_CAN_CAUSE_A_STOPPAGE:
        # Penalties,goals will cause a stoppage. Player gets credit for being on the ice for that
        # Shots can cause a stoppage, if a player's shift ended when the shot occurred.
        # This conditional assumes a stoppage did occur
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


def swap_states(states_dict):
    """
    Swaps the string held in the keys of states_dict
    Before: {5v4:INT} After: {4v5:INT}
    """
    temp = {f"{k[2]}{k[1]}{k[0]}": v for k, v in states_dict.items()}
    return {f"{k[2]}{k[1]}{k[0]}": v for k, v in states_dict.items()}
    # for key, value in states_dict.items():
    #     # Each key is a 3 char string, []v[]
    #     temp_key = f"{key[2]}{key[1]}{key[0]}"
    #     temp[temp_key] = value
    # return temp
