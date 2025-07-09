from django.contrib import admin
from .models import Child, Trainer, GroupKidGarden, Attendance, User


admin.site.register(User)
admin.site.register(Trainer)
admin.site.register(Child)
admin.site.register(GroupKidGarden)
admin.site.register(Attendance)