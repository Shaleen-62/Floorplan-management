from django.db import models
from django.contrib.auth.models import User
import jsonfield

class User(models.Model):
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    role = models.CharField(max_length=20)
    verified = models.BooleanField(default=False)
    used_spaces = models.TextField(default = "[]")
    
    def __str__(self):
        return f'{self.name} added'
    
    
class Space(models.Model):
    space_name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    floor = models.IntegerField()
    occupied = models.TextField(default = "[]")
    
    def __str__(self):
        return f'{self.space_name} added'
    

class Update(models.Model):
    username = models.CharField(max_length=100)
    role = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
    floor = models.IntegerField()
    edits = jsonfield.JSONField()
    verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f'{self.floor} updated'
    

class Booking(models.Model):
    user = models.CharField(max_length=100)
    role = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
    capacity_required = models.IntegerField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    booked_space = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f'{self.user} booking for {self.booked_space} on {self.date}'

