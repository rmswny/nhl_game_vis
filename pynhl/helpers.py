import datetime

EVENTS_THAT_CAN_CAUSE_A_STOPPAGE = {"Shot", "Goal", "Penalty"}


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

# def find_overlapping_shifts(player_shift, other_shifts):
#     """
#     Function will determine if ANY shift occurs doing another shift
#     And will find the total time, over (possibly) more than one shift that is shared
#     between two players
#
#     Helper function that iterates through a list of shifts (other_shifts) to compare to player_shift
#     Inputs are already separated by period & team to ensure minimal comparisons are needed
#
#     returns the indices where shifts are overlapping
#     """
#     indices = set()
#     for index, other_shift in enumerate(other_shifts):
#         # How to handle both shifts and time objects? Probably cannot -- separate functions!
#         if time_check_shift(player_shift, other_shift):
#             # on the ice together!
#             indices.add(index)
#     return indices
