from django.urls import path
from bapp.views import (
    register_user, 
    login_user,
    get_user_profile, 
    logout_user,
    get_dashboard_data,
    search_blood,
    get_donors,
    get_emergency_nodes,
    broadcast_sos,
    get_donation_insights,
    book_appointment , # Make sure this is imported!
    get_blood_requests,
    create_blood_request,
)

urlpatterns = [
    path('api/register/', register_user),
    path('api/login/', login_user),
    path('api/user/', get_user_profile),
    path('api/logout/', logout_user),
    path('api/dashboard-stats/', get_dashboard_data),
    path('api/search-blood/', search_blood),
    path('api/donors/', get_donors),
    path('api/emergency-nodes/', get_emergency_nodes),
    path('api/broadcast-sos/', broadcast_sos),
    
    # FIXED: Added 'api/' prefix to match React's fetch URL
    path('api/donation-insights/', get_donation_insights, name='donation_insights'),
    
    # ADDED: This is required for the "Confirm Appointment" button to work
    path('api/book-appointment/', book_appointment, name='book_appointment'),

    path('api/blood-requests/', get_blood_requests, name='blood_requests'),

    path('api/create-request/', create_blood_request, name='create_request'),

    

]