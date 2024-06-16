from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from django.db.models import Q
from django.utils.dateparse import parse_date, parse_time

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Booking, Space, Update
from .serializers import SpaceSerializer, UpdateSerializer, UserSerializer, BookingSerializer
from .created import suggest, custom_verification_logic

import json
from datetime import datetime
from heapq import heappush, heappop




# API to suggest space to any user regardless of them being verified
@api_view(['POST'])
def suggestspaces(request):
    capacity_required = request.data.get('capacity_required')
    date_str = request.data.get('date')
    start_time_str = request.data.get('start_time')
    end_time_str = request.data.get('end_time')

    date = parse_date(date_str)
    start_time = parse_time(start_time_str)
    end_time = parse_time(end_time_str)
    
    if not (capacity_required and date and start_time and end_time):
        return Response({'error': 'Please provide all required fields'}, status=status.HTTP_400_BAD_REQUEST)

    req_user = request.data.get("req_user")
    request_maker = User.objects.get(pk=req_user)
    role = request_maker.role


    available_spaces = suggest(request_maker.name, date_str, start_time_str, end_time_str, capacity_required)

    booking = Booking.objects.create(
        user=req_user.name,
        role=role,
        capacity_required=capacity_required,
        date=date,
        start_time=start_time,
        end_time=end_time,
        booked_space=None
    )
    
    serializer = BookingSerializer(booking)
    return Response({'available_spaces': [space for space in available_spaces], 'booking': serializer.data}, status=status.HTTP_200_OK)


# API to let a verified user make booking
@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def makebooking(request):
    req_user = request.query_params.get('req_user')
    username = User.objects.get(pk=req_user).name
    space_name = request.data.get('booked_space')
    date_str = request.data.get('date')
    start_time_str = request.data.get('start_time')
    end_time_str = request.data.get('end_time')
    capacity_required = request.data.get('capacity_required')
    
    date = parse_date(date_str)
    start_time = parse_time(start_time_str)
    end_time = parse_time(end_time_str)

    try:
        user = User.objects.get(name=username)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        space = Space.objects.get(space_name=space_name)
    except Space.DoesNotExist:
        return Response({'error': 'Space not found'}, status=status.HTTP_404_NOT_FOUND)

    occupied = space.occupied
    if isinstance(occupied, str):
        occupied = json.loads(occupied)

    # checking whether interval overlap with previous bookings
    for interval in occupied:
        interval_start_time = datetime.strptime(interval['start_time'], '%H:%M:%S').time()
        interval_end_time = datetime.strptime(interval['end_time'], '%H:%M:%S').time()
        if (start_time < interval_end_time and end_time > interval_start_time):
            return Response({'error': 'The space is already occupied during the requested time interval.'}, status=status.HTTP_400_BAD_REQUEST)

    # if suggestspace was called for the same query, make modifications in the same entry
    try:
        existing_booking = Booking.objects.get(
            user=username,
            date=date_str,
            start_time=start_time_str,
            end_time=end_time_str
        )
        
        # if a user booked another room for the same interval, throw an error
        if existing_booking.booked_space is not None:
            return Response({'error': 'Another space has already been booked for this time slot.'}, status=status.HTTP_400_BAD_REQUEST)
        # modifying booked_space and timestamp in the entry
        else:
            existing_booking.booked_space = space_name
            existing_booking.timestamp = datetime.now()
            existing_booking.save()
            
    # suggestspace was not called for this query, making a new entry
    except Booking.DoesNotExist:
        new_booking = Booking.objects.create(
            user=username,
            role=user.role,
            timestamp=datetime.now(),
            capacity_required=space.capacity,
            date=date_str,
            start_time=start_time_str,
            end_time=end_time_str,
            booked_space=space_name
        )

    # booked interval also reflected for the space booked
    occupied.append({'date': date_str, 'start_time': start_time_str, 'end_time': end_time_str})
    space.occupied = json.dumps(occupied)
    space.save()
    space_used = user.used_spaces
    if isinstance(space_used, str):
        space_used = json.loads(space_used)
    space_used.append({'space_name': space_name, 'capacity_required': capacity_required})
    user.used_spaces = json.dumps(space_used)
    user.save()

    return Response({'message': 'Booking successful'}, status=status.HTTP_200_OK)


# API to flush bookings that happened before a certain date
@api_view(['POST'])
#@permission_classes([IsAuthenticated])
#@user_passes_test(lambda u: u.is_superuser)
def flushbooking(request):
    
    try:
        req_user = request.query_params.get('req_user')
        user = User.objects.get(pk=req_user)
        if user.role != 'superuser':
            return Response({'error': 'User is not an admin.'}, status=status.HTTP_403_FORBIDDEN)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    date_str = request.data.get('date')
    if not date_str:
        return Response({'error': 'Date is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        given_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
    
    spaces = Space.objects.all()
    for space in spaces:
        occupied = json.loads(space.occupied)
        updated_occupied = [entry for entry in occupied if datetime.strptime(entry['date'], '%Y-%m-%d').date() > given_date]
        space.occupied = json.dumps(updated_occupied)
        space.save()
    
    return Response({'message': 'Booking entries flushed successfully.'}, status=status.HTTP_200_OK)
