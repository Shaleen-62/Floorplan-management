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




# API for login
@api_view(['POST'])
def signup(request):
    username = request.data.get('username')
    password = request.data.get('password')
    password_reenter = request.data.get('password_reenter')
    role = request.data.get('role')

    if User.objects.filter(name=username).exists():
        return Response({'error': 'Username already taken. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)

    if password != password_reenter:
        return Response({'error': 'Passwords do not match. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)

    if role == 'admin':
        verified = False 
    elif role == 'consumer':
        verified = True
    elif role == 'superuser':
        verified = True

    user_data = {'name': username, 'password': password, 'role': role, 'verified': verified}
    serializer = UserSerializer(data=user_data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# API for signup
@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    try:
        user = User.objects.get(name=username, password=password)
        if user.verified:
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'User successfully logged in',
                'username': user.name,
                'role': user.role,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response({'error': 'Invalid User credentials. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({'error': 'Invalid User credentials. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)
    

# API to verify admins
@api_view(['GET', 'PUT'])
#@permission_classes([IsAuthenticated])
#@user_passes_test(lambda u: u.is_superuser)
def admin_verification(request, user_id=None):
    req_user = request.query_params.get('req_user')
    request_maker = User.objects.get(pk=req_user)
    if request_maker.role == 'superuser':
        if request.method == 'GET':
            # show all pending verifications
            if user_id is None:
                users = User.objects.filter(role='admin', verified=False)
                serializer = UserSerializer(users, many=True)
                return Response(serializer.data)
            # shows whether the user with the entered id is admin or not
            else:
                try:
                    user = User.objects.get(pk=user_id)
                    if user.role == 'admin':
                        serializer = UserSerializer(user)
                        return Response(serializer.data)
                    else:
                        return Response({'error': 'User is not an admin'}, status=status.HTTP_400_BAD_REQUEST)
                except User.DoesNotExist:
                    return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Toggle verified status
        elif request.method == 'PUT':
            if user_id is None:
                return Response({'error': 'Please provide a valid user_id for PUT operation'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(pk=user_id)
                if user.role == 'admin':
                    user.verified = not user.verified  
                    user.save()
                    serializer = UserSerializer(user)
                    return Response(serializer.data)
                else:
                    return Response({'error': 'User is not an admin'}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'error': 'Operation not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    else:
        return Response({'error': 'User is not a superuser'}, status=status.HTTP_400_BAD_REQUEST)
