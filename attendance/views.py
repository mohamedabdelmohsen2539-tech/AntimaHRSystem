from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from employees.models import Employee

from .models import DailyAttendanceSummary
from .services import calculate_attendance_range


@staff_member_required
def absence_page(request):
    """صفحة الغياب (الفلترة والجدول بيتحملوا بالـ Ajax)."""
    return render(request, "attendance/absence.html")


@staff_member_required
@require_GET
def absence_list_api(request):
    """
    Ajax: فلترة سجلات الحضور/الغياب.
    باراميترز: q (اسم/رقم بصمة), status, date_from, date_to, page
    """
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    page_number = request.GET.get("page", 1)

    qs = DailyAttendanceSummary.objects.select_related("employee").all()

    if q:
        qs = qs.filter(
            Q(employee__full_name__icontains=q) | Q(employee__fingerprint_id__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    qs = qs.order_by("-date", "employee__full_name")
    paginator = Paginator(qs, 25)
    page = paginator.get_page(page_number)

    results = [
        {
            "employee": r.employee.full_name,
            "fingerprint_id": r.employee.fingerprint_id,
            "date": r.date.isoformat(),
            "check_in": r.check_in.strftime("%H:%M") if r.check_in else "-",
            "check_out": r.check_out.strftime("%H:%M") if r.check_out else "-",
            "status": r.get_status_display(),
            "status_code": r.status,
            "worked_hours": str(r.worked_hours),
        }
        for r in page.object_list
    ]

    # ملخص سريع لعدد أيام الغياب في نطاق البحث الحالي (من غير الصفحة الحالية بس)
    absent_total = qs.filter(status="absent").count()

    return JsonResponse(
        {
            "results": results,
            "has_next": page.has_next(),
            "has_previous": page.has_previous(),
            "current_page": page.number,
            "num_pages": paginator.num_pages,
            "total": paginator.count,
            "absent_total": absent_total,
        }
    )


@staff_member_required
@require_POST
def recalculate_api(request):
    """
    Ajax: يعيد حساب الحضور/الغياب لفترة معينة (ولموظف معين لو اتحدد رقم بصمة).
    """
    date_from = request.POST.get("date_from")
    date_to = request.POST.get("date_to")
    fingerprint_id = request.POST.get("fingerprint_id", "").strip()

    if not date_from or not date_to:
        return JsonResponse({"ok": False, "error": "من فضلك حدد الفترة (من - إلى)"}, status=400)

    try:
        d_from = datetime.strptime(date_from, "%Y-%m-%d").date()
        d_to = datetime.strptime(date_to, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"ok": False, "error": "صيغة التاريخ غير صحيحة"}, status=400)

    employees = None
    if fingerprint_id:
        employees = Employee.objects.filter(fingerprint_id=fingerprint_id)
        if not employees.exists():
            return JsonResponse({"ok": False, "error": "رقم البصمة غير موجود"}, status=404)

    count = calculate_attendance_range(d_from, d_to, employees=employees)
    return JsonResponse({"ok": True, "calculated": count})
