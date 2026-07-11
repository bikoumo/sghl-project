from django.contrib import admin
from .models import Appointment, Bed, Building, ExamRequest, ExamResult, Invoice, Medication, Provision, Room, Service

admin.site.register(Building)
admin.site.register(Service)
admin.site.register(Room)
admin.site.register(Bed)
admin.site.register(Appointment)
admin.site.register(Medication)
admin.site.register(Invoice)
admin.site.register(Provision)
admin.site.register(ExamRequest)
admin.site.register(ExamResult)
