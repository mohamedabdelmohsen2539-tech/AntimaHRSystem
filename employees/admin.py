from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from attendance.models import DailyAttendanceSummary
from leaves.models import LeaveRequest, PermissionRequest

from .models import (
    Department,
    Employee,
    EmployeeDocument,
    EmployeeQualification,
    EmployeeSalary,
    JobTitle,
    Penalty,
)


@admin.register(Department)
class DepartmentAdmin(ModelAdmin):
    list_display = ("name", "employees_count")
    search_fields = ("name",)
    list_per_page = 25

    def employees_count(self, obj):
        return obj.employees.count()
    employees_count.short_description = "عدد الموظفين"


@admin.register(JobTitle)
class JobTitleAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    list_per_page = 25


# ---------------------------------------------------------------------------
# Inlines تتعرض كـ tabs جوه صفحة الموظف (tab = True من مميزات Unfold)
# ---------------------------------------------------------------------------

class EmployeeDocumentInline(TabularInline):
    model = EmployeeDocument
    tab = True
    extra = 1
    fields = ("doc_type", "file", "issue_date", "expiry_date", "notes")


class EmployeeQualificationInline(TabularInline):
    model = EmployeeQualification
    tab = True
    extra = 1
    fields = ("qualification_name", "institution", "graduation_year", "grade")


class PenaltyInline(TabularInline):
    model = Penalty
    tab = True
    extra = 0
    fields = ("penalty_type", "amount", "reason", "date")


class EmployeeSalaryInline(TabularInline):
    """
    Tab بيانات المرتب - محمي بصلاحية view_confidential_salary.
    اليوزر اللي معندوش الصلاحية دي مش هيشوف التاب ده خالص، مش مجرد اخفاء شكلي.
    """
    model = EmployeeSalary
    tab = True
    extra = 0
    max_num = 1
    fields = ("basic_salary", "allowances", "deductions", "bank_name", "bank_account", "notes")

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.has_perm(
            "employees.view_confidential_salary"
        )

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)


class LeaveRequestInline(TabularInline):
    """تاب يعرض تاريخ إجازات الموظف جوه الـ profile بتاعه (للعرض فقط)."""
    model = LeaveRequest
    tab = True
    extra = 0
    fields = ("leave_type", "start_date", "end_date", "days_count", "status")
    readonly_fields = fields
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("-start_date")


class PermissionRequestInline(TabularInline):
    """تاب يعرض تاريخ أذونات الموظف جوه الـ profile بتاعه (للعرض فقط)."""
    model = PermissionRequest
    tab = True
    extra = 0
    fields = ("date", "from_time", "to_time", "status")
    readonly_fields = fields
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("-date")


class DailyAttendanceSummaryInline(TabularInline):
    """تاب يعرض آخر أيام الحضور/الغياب المحسوبة للموظف (للعرض فقط)."""
    model = DailyAttendanceSummary
    tab = True
    extra = 0
    fields = ("date", "check_in", "check_out", "status", "worked_hours")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        # آخر 60 يوم بس عشان الصفحة متتقلش، التقرير الكامل والفلترة الحقيقية
        # في صفحة الغياب (/hr/attendance/absence/). فلترة بالتاريخ بدل
        # الـ slice عشان Django admin بيحتاج يعمل order_by على الـ queryset
        # نفسه لاحقًا، والـ slice بيمنع ده.
        from datetime import timedelta

        from django.utils import timezone

        cutoff = timezone.now().date() - timedelta(days=60)
        return super().get_queryset(request).filter(date__gte=cutoff).order_by("-date")


@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    list_display = (
        "photo_thumb",
        "full_name",
        "fingerprint_id",
        "department",
        "job_title",
        "hire_date",
        "status",
    )
    list_filter = ("department", "job_title", "status", "hire_date")
    search_fields = ("full_name", "fingerprint_id", "national_id", "phone")
    ordering = ("full_name",)
    list_per_page = 25  # pagination
    date_hierarchy = "hire_date"

    # الشاشة الرئيسية + tabs للبيانات الأساسية والوظيفية، زي شكل البرنامج القديم
    fieldsets = (
        (None, {"fields": ("photo", "full_name", "fingerprint_id", "status")}),
        (
            "البيانات الأساسية",
            {
                "classes": ["tab"],
                "fields": (
                    "national_id",
                    "birth_date",
                    "gender",
                    "marital_status",
                    "phone",
                    "address",
                ),
            },
        ),
        (
            "البيانات الوظيفية",
            {
                "classes": ["tab"],
                "fields": ("department", "job_title", "hire_date", "user"),
            },
        ),
    )

    # تاب المرتب (محمي) + المستندات + المؤهلات + الجزاءات
    inlines = [
        EmployeeSalaryInline,
        EmployeeDocumentInline,
        EmployeeQualificationInline,
        PenaltyInline,
        LeaveRequestInline,
        PermissionRequestInline,
        DailyAttendanceSummaryInline,
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("department", "job_title")

    def photo_thumb(self, obj):
        return "🖼️" if obj.photo else "—"
    photo_thumb.short_description = "الصورة"
