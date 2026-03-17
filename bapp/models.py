from django.db import models
from django.contrib.auth.models import User

class DashboardStats(models.Model):
    total_donors = models.IntegerField(default=13900)
    units_month = models.IntegerField(default=10455)
    emergency_requests = models.IntegerField(default=2)
    hospitals = models.IntegerField(default=190)
    total_units = models.IntegerField(default=2660)

class Activity(models.Model):
    message = models.CharField(max_length=255)
    is_emergency = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Donor(models.Model):
    name = models.CharField(max_length=255)
    blood_group = models.CharField(max_length=5)
    location = models.CharField(max_length=255)
    last_donated = models.DateField(null=True, blank=True)
    contact = models.CharField(max_length=20)
    
    # CHANGE 1: Use 'Eligible' or 'On Cooldown' to match your React CSS logic
    status = models.CharField(max_length=20, default="Eligible") 
    
    # CHANGE 2: Add this for the percentage bar/score in your UI
    # 0.95 represents 95%
    reliability_score = models.FloatField(default=0.95) 

    def __str__(self):
        return f"{self.name} ({self.blood_group})"
    



class BloodInventory(models.Model):
    node_name = models.CharField(max_length=255)
    blood_group = models.CharField(max_length=5)
    component = models.CharField(max_length=50)
    available_units = models.IntegerField(default=0)
    distance_km = models.FloatField()

    def __str__(self):
        return f"{self.node_name} - {self.blood_group}"
    







class HospitalNode(models.Model):
    name = models.CharField(max_length=255)
    node_id = models.CharField(max_length=50, unique=True) # e.g., "Node 012"
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    has_trauma_unit = models.BooleanField(default=False)
    has_burn_center = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.node_id} - {self.name}"

class EmergencyRequest(models.Model):
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Active") # Active, Resolved
    
    def __str__(self):
        return f"SOS by {self.requested_by.username} at {self.timestamp}"
    






class DonationEligibility(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=5)
    last_check_date = models.DateTimeField(auto_now=True)
    is_eligible = models.BooleanField(default=True)
    # Answers stored as JSON or individual booleans
    health_data = models.JSONField(default=dict) 

    def __str__(self):
        return f"{self.user.username} - {self.blood_group}"

class Appointment(models.Model):
    DONATION_TYPES = [
        ('WB', 'Whole Blood'),
        ('PL', 'Platelets'),
        ('PA', 'Plasma'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    node = models.ForeignKey(HospitalNode, on_delete=models.CASCADE)
    donation_type = models.CharField(max_length=2, choices=DONATION_TYPES)
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, default="Scheduled")

    def __str__(self):
        return f"{self.user.username} at {self.node.name}"
    





class BloodRequest(models.Model):
    BLOOD_GROUPS = [
        ('O+', 'O+'), ('O-', 'O-'), ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'),
    ]
    URGENCY_CHOICES = [
        ('SOS', 'SOS'),
        ('High', 'High'),
        ('Normal', 'Normal'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Fulfilled', 'Fulfilled'),
    ]

    # Added: Track who made the request
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blood_requests")
    
    req_id = models.CharField(max_length=20, unique=True, editable=False)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUPS)
    units_needed = models.PositiveIntegerField(default=1)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='Normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    matched_donors_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.req_id:
            import random
            # Generates REQ-XXXX format automatically on first save
            self.req_id = f"REQ-{random.randint(1000, 9999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.req_id} | {self.blood_group} | {self.status}"