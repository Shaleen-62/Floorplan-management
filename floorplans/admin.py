from django.contrib import admin
from .models import User, Update, Space, Booking

admin.site.register(User)
admin.site.register(Update)
admin.site.register(Space)
admin.site.register(Booking)