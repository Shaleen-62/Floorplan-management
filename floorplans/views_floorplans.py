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




# API to view the floorplan of the entered floor number
@api_view(['GET'])
#@permission_classes([IsAuthenticated])
def viewfloorplan(request):
    try:
        req_user = request.query_params.get('req_user')
        request_maker = User.objects.get(pk=req_user)
        if request_maker.verified:
            floor = request.query_params.get('floor')
            if floor is None:
                return Response({'error': 'Please provide a floor number'}, status=status.HTTP_400_BAD_REQUEST)
            spaces = Space.objects.filter(floor=floor)
            serializer = SpaceSerializer(spaces, many=True)
            return Response(serializer.data)
        
        else:
            return Response({'error': 'Invalid User credentials. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({'error': 'Invalid User credentials. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)
        

# API to put a request to update floorplan with suggested edits
@api_view(['POST'])
#@permission_classes([IsAuthenticated])
def updatefloorplan(request):
    try:
        req_user = request.query_params.get('req_user')
        request_maker = User.objects.get(pk=req_user)
        if request_maker.role == 'admin' and request_maker.verified:
            floor = request.data.get('floor')
            edits = request.data.get('edits')            
            update = Update.objects.create(
                username=request_maker.name,
                role=request_maker.role,
                floor=floor,
                edits=edits,
                verified=False
            )
            update.save()
            serializer = UpdateSerializer(update)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        else:
            return Response({'error': 'User is not an admin.'}, status=status.HTTP_403_FORBIDDEN)
    except User.DoesNotExist:
        return Response({'error': 'Invalid User credentials. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)


# API to verify the floorplan edits and incorporate the feasible edits, rest displayed for verification
@api_view(['POST'])
#@permission_classes([IsAuthenticated])
#@user_passes_test(lambda u: u.is_superuser)
def verifyfloorplan(request):
    floor = request.query_params.get('floor')
    try:
        req_user = request.query_params.get('req_user')
        request_maker = User.objects.get(pk=req_user)
        if request_maker.role == 'superuser' and request_maker.verified:
            try:
                updates = Update.objects.filter(floor=floor, verified=False)
            except:
                return Response({'No updates pending'})

            to_update, to_verify = custom_verification_logic(request_maker.name, request_maker.role, floor, updates)
            #print('to_update', to_update)
            #print('to_verify', to_verify)
            
            for u in updates:
                u.verified = True
                u.save()
                
            for new in to_update:
                if Space.objects.filter(space_name=new['space_name']).exists():
                    Space.objects.get(space_name=new['space_name']).delete()
                Space.objects.create(
                    space_name= new['space_name'],
                    capacity= new['capacity'],
                    floor= floor,
                    occupied= "[]"
                )
            
            return Response({'manual verification needed immediately': [space for space in to_verify]}, status=status.HTTP_200_OK)

        else:
            return Response({'error': 'User is not an admin.'}, status=status.HTTP_403_FORBIDDEN)
    except User.DoesNotExist:
        return Response({'error': 'Invalid User credentials. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)
