import json
from datetime import datetime
from heapq import heappush, heappop
from .models import User, Booking, Space, Update


# to merge floorplans:
# merge those without conflict(to_update)
# merge those that aren't yet verified on basis of first come first serve(to_update)
# notify admin about those updates that conflict existing arrangements(to_verify)

def custom_verification_logic(username, role, floor, updates):
    to_update = []
    to_verify = []

    updates = updates.filter(floor=floor, verified=False).order_by('timestamp')
    spaces = Space.objects.filter(floor=floor)
    space_names = set([space.space_name for space in spaces])
    seen_names = set()

    for update in updates:
        for edit in update.edits:
            if edit['space_name'] not in seen_names:
                if edit['space_name'] not in space_names:
                    to_update.append(edit)
                    seen_names.add(edit['space_name'])
                elif edit['capacity'] != Space.objects.get(space_name = edit['space_name']).capacity:
                    to_verify.append([edit])

    return to_update, to_verify



# to suggest suitable spaces given the capacity required, earlier preferences
# suggests at max two names, 1st being the rooms of capacity equal or larger than the required capacity, 2nd being the room based on earlier preference

def suggest(user, date_str, start_time_str, end_time_str, capacity_required):
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
    end_time = datetime.strptime(end_time_str, '%H:%M:%S').time()

    suitable_spaces = []
    last_used_space = None

    spaces = Space.objects.filter(capacity__gte=capacity_required).order_by('capacity')
    space_heap = []

    for space in spaces:
        heappush(space_heap, (space.capacity, space.space_name, space.occupied))

    while space_heap:
        space_capacity, space_name, occupied_intervals_json = heappop(space_heap)
        occupied_intervals = json.loads(occupied_intervals_json or '[]')
        conflict = False

        for interval in occupied_intervals:
            interval_date = datetime.strptime(interval['date'], '%Y-%m-%d').date()
            if interval_date != date:
                continue

            interval_start_time = datetime.strptime(interval['start_time'], '%H:%M:%S').time()
            interval_end_time = datetime.strptime(interval['end_time'], '%H:%M:%S').time()

            if not (end_time <= interval_start_time or start_time >= interval_end_time):
                conflict = True
                break

        if not conflict:
            suitable_spaces.append({'space_name': space_name, 'capacity': space_capacity})
            break

    try:
        user_obj = User.objects.get(name=user)
        used_spaces = json.loads(user_obj.used_spaces or '[]')
        for space_used in used_spaces:
            if space_used['capacity_required'] >= capacity_required:
                last_used_space = space_used['space_name']
                break

    except User.DoesNotExist:
        pass

    if last_used_space and last_used_space not in [space['space_name'] for space in suitable_spaces]:
        suitable_spaces.append({'space_name': last_used_space, 'capacity': capacity_required})

    return suitable_spaces
