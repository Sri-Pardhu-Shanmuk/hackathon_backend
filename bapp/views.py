import json
import random
from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    DashboardStats, Activity, BloodInventory, Appointment, 
    DonationEligibility, Donor, HospitalNode, EmergencyRequest, BloodRequest
)

# --- AUTHENTICATION ---

@csrf_exempt
def register_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        try:
            user = User.objects.create_user(
                username=data.get('username'),
                email=data.get('email'),
                password=data.get('password'),
                first_name=data.get('full_name')
            )
            return JsonResponse({"message": "User created successfully!"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def login_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user = authenticate(username=data.get('username'), password=data.get('password'))
        if user:
            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                "access": str(refresh.access_token),
                "full_name": user.first_name or user.username
            })
        return JsonResponse({"error": "Invalid Credentials"}, status=401)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    return JsonResponse({
        "full_name": request.user.first_name or request.user.username,
        "email": request.user.email,
        "username": request.user.username
    })

@csrf_exempt
def logout_user(request):
    logout(request)
    return JsonResponse({"message": "Logged out successfully"})

# --- DASHBOARD & DONORS ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_data(request):
    stats = DashboardStats.objects.first()
    activities_query = Activity.objects.all().order_by('-created_at')[:5]
    
    activity_list = [
        {"message": item.message, "is_emergency": item.is_emergency} 
        for item in activities_query
    ]

    data = {
        "stats": {
            "total_donors": stats.total_donors if stats else 13900,
            "units_month": stats.units_month if stats else 10455,
            "emergency_requests": stats.emergency_requests if stats else 2,
            "hospitals": stats.hospitals if stats else 190,
            "total_units": stats.total_units if stats else 2660,
        },
        "activities": activity_list
    }
    return JsonResponse(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_donors(request):
    donors_query = Donor.objects.all()
    donors_list = [{
        "name": d.name,
        "bloodGroup": d.blood_group,
        "location": d.location,
        "lastDonation": d.last_donated.strftime("%b %d, %Y") if d.last_donated else "Never",
        "reliabilityScore": float(d.reliability_score),
        "status": d.status 
    } for d in donors_query]
    
    return JsonResponse(donors_list, safe=False)

# --- BLOOD SEARCH & EMERGENCY ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_blood(request):
    group = request.query_params.get('group')
    comp = request.query_params.get('component')

    inventory = BloodInventory.objects.filter(
        blood_group__iexact=group, 
        component__iexact=comp
    ).order_by('distance_km')

    results_list = [{
        "nodeName": item.node_name,
        "distance": f"{item.distance_km} km",
        "availableUnits": f"{item.available_units} Units",
        "component": item.component
    } for item in inventory]

    donors = Donor.objects.filter(
        blood_group__iexact=group, 
        status="Eligible"
    ).order_by('-reliability_score')[:3]

    top_donors = [{
        "name": d.name, 
        "score": f"{(float(d.reliability_score) * 100):.0f}%"
    } for d in donors]

    return JsonResponse({"results": results_list, "top_donors": top_donors})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_emergency_nodes(request):
    query = request.query_params.get('q', '')
    nodes_query = HospitalNode.objects.filter(
        models.Q(name__icontains=query) | models.Q(node_id__icontains=query)
    )

    nodes_list = [{
        "id": node.node_id,
        "name": node.name,
        "lat": float(node.latitude),
        "lng": float(node.longitude),
        "trauma": node.has_trauma_unit,
        "burn": node.has_burn_center,
        "verified": node.is_verified
    } for node in nodes_query]

    top_donors = Donor.objects.filter(status="Eligible").order_by('-reliability_score')[:3]
    return JsonResponse({
        "nodes": nodes_list,
        "ai_donors": [{"name": d.name, "score": float(d.reliability_score)} for d in top_donors],
        "forecast": "Spike detected in Trauma requests. 85% probability of O- shortage soon."
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def broadcast_sos(request):
    EmergencyRequest.objects.create(requested_by=request.user)
    return JsonResponse({"message": "SOS Broadcasted!"}, status=201)

# --- DONATION INSIGHTS & APPOINTMENTS ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_donation_insights(request):
    # Try to find a donor profile for this user
    donor = Donor.objects.filter(name=request.user.first_name).first()
    blood_group = donor.blood_group if donor else "O+"
    
    nearest_node = HospitalNode.objects.first() 

    return JsonResponse({
        "donor_name": request.user.first_name or request.user.username,
        "blood_group": blood_group,
        "reliability_score": 0.98,
        "forecast": f"Your {blood_group} type is currently in critical demand.",
        "nearest_node": {
            "id": nearest_node.node_id if nearest_node else "NODE-001",
            "name": nearest_node.name if nearest_node else "City General Hospital",
            "distance": "1.2 km"
        },
        "available_slots": ["09:00 AM", "11:00 AM", "02:00 PM"]
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_appointment(request):
    data = request.data
    # Determine health eligibility
    answers = data.get('answers', {})
    is_eligible = all(v == 'No' for v in answers.values())

    DonationEligibility.objects.update_or_create(
        user=request.user,
        defaults={
            "blood_group": data.get('bloodGroup', 'O+'),
            "health_data": answers,
            "is_eligible": is_eligible
        }
    )

    # Logic to get a valid HospitalNode instance
    node = HospitalNode.objects.first()
    if not node:
        return Response({"error": "No hospital nodes available"}, status=400)

    Appointment.objects.create(
        user=request.user,
        node=node,
        donation_type=data.get('donationType', 'WB'),
        scheduled_time=datetime.now() 
    )

    return JsonResponse({"message": "Appointment confirmed!"}, status=201)

# --- REQUEST HUB LOGIC ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_blood_requests(request):
    filter_type = request.query_params.get('filter', 'Active')
    
    if filter_type == 'Fulfilled':
        requests_query = BloodRequest.objects.filter(status='Fulfilled')
    else:
        requests_query = BloodRequest.objects.exclude(status='Fulfilled')

    results = [{
        "reqId": r.req_id,
        "bloodGroup": r.blood_group,
        "units": r.units_needed,
        "urgency": r.urgency,
        "status": r.status,
        "matchedDonors": r.matched_donors_count,
        "date": r.created_at.strftime("%b %d, %H:%M %p") 
    } for r in requests_query.order_by('-created_at')]

    return Response(results)

@api_view(['POST'])
#@permission_classes([IsAuthenticated])
def create_blood_request(request):
    data = request.data
    try:
        # request.user comes from the Bearer token!
        new_request = BloodRequest.objects.create(
            user=request.user, 
            blood_group=data.get('bloodGroup'),
            units_needed=data.get('units'),
            urgency=data.get('urgency', 'Normal'),
            status='Pending'
        )
        return Response({"message": "Created", "reqId": new_request.req_id}, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=400)