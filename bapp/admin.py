from django.contrib import admin
from .models import DashboardStats,Activity,Donor,BloodInventory,HospitalNode,EmergencyRequest,BloodRequest
# Register your models here.
admin.site.register(DashboardStats)
admin.site.register(Activity)
admin.site.register(Donor)
admin.site.register(BloodInventory)
admin.site.register(HospitalNode)
admin.site.register(EmergencyRequest)
admin.site.register(BloodRequest)