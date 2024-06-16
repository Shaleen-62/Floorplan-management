from django.urls import path
from . import views_users
from . import views_floorplans
from . import views_bookings


urlpatterns = [
    path('signup/', views_users.signup, name='signup'),
    path('login/', views_users.login, name='login'),
    path('admin-verification/', views_users.admin_verification, name='admin_verification_list'),
    path('admin-verification/<int:user_id>/', views_users.admin_verification, name='admin_verification_detail'),
    path('viewfloorplan/', views_floorplans.viewfloorplan, name='viewfloorplan'),
    path('updatefloorplan/', views_floorplans.updatefloorplan, name='updatefloorplan'),
    path('verifyfloorplan/', views_floorplans.verifyfloorplan, name='verifyfloorplan'),
    path('suggestspaces/', views_bookings.suggestspaces, name='suggestspaces'),
    path('makebooking/', views_bookings.makebooking, name='makebooking'),
    path('flushbooking/', views_bookings.flushbooking, name='flushbooking'),
]