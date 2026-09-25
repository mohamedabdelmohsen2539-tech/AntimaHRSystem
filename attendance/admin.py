from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import AttendanceDevice, AttendanceLog, DailyAttendanceSummary


@admin.register(AttendanceDevice)
class AttendanceDeviceAdmin(ModelAdmin):
    list_display = ("name", "ip_address", "port", "location", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "ip_address", "location")
    list_per_page = 25


@admin.register(AttendanceLog)
class AttendanceLogAdmin(ModelAdmin):
    list_display = ("fingerprint_id", "employee", "timestamp", "punch_type", "source", "device")
    list_filter = ("source", "punch_type", "device")
    search_fields = ("fingerprint_id", "employee__full_name")
    date_hierarchy = "timestamp"
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("employee", "device")


@admin.register(DailyAttendanceSummary)
class DailyAttendanceSummaryAdmin(ModelAdmin):
    list_display = ("employee", "date", "check_in", "check_out", "status", "worked_hours")
    list_filter = ("status",)
    search_fields = ("employee__full_name", "employee__fingerprint_id")
    date_hierarchy = "date"
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("employee")
