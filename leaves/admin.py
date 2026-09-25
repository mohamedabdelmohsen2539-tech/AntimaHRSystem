from django.contrib import admin
from django.utils import timezone
from unfold.admin import ModelAdmin

from .models import LeaveRequest, LeaveType, PermissionRequest


@admin.register(LeaveType)
class LeaveTypeAdmin(ModelAdmin):
    list_display = ("name", "deducts_balance", "requires_approval", "max_days_per_year")
    list_per_page = 25


@admin.register(LeaveRequest)
class LeaveRequestAdmin(ModelAdmin):
    list_display = (
        "employee",
        "leave_type",
        "start_date",
        "end_date",
        "days_count",
        "status",
        "source",
    )
    list_filter = ("status", "leave_type", "source")
    search_fields = ("employee__full_name", "employee__fingerprint_id")
    list_per_page = 25
    date_hierarchy = "start_date"
    actions = ["approve_requests", "reject_requests"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("employee", "leave_type")

    @admin.action(description="اعتماد الطلبات المحددة")
    def approve_requests(self, request, queryset):
        queryset.update(
            status="approved", reviewed_by=request.user, reviewed_at=timezone.now()
        )

    @admin.action(description="رفض الطلبات المحددة")
    def reject_requests(self, request, queryset):
        queryset.update(
            status="rejected", reviewed_by=request.user, reviewed_at=timezone.now()
        )


@admin.register(PermissionRequest)
class PermissionRequestAdmin(ModelAdmin):
    list_display = ("employee", "date", "from_time", "to_time", "status", "source")
    list_filter = ("status", "source")
    search_fields = ("employee__full_name", "employee__fingerprint_id")
    list_per_page = 25
    date_hierarchy = "date"
    actions = ["approve_requests", "reject_requests"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("employee")

    @admin.action(description="اعتماد الطلبات المحددة")
    def approve_requests(self, request, queryset):
        queryset.update(
            status="approved", reviewed_by=request.user, reviewed_at=timezone.now()
        )

    @admin.action(description="رفض الطلبات المحددة")
    def reject_requests(self, request, queryset):
        queryset.update(
            status="rejected", reviewed_by=request.user, reviewed_at=timezone.now()
        )
