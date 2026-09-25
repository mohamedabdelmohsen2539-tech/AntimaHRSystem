"""
سحب البصمات من أجهزة ZKTeco.

ملحوظة مهمة: مكتبة pyzk بتتصل بالجهاز عن طريق IP على نفس الشبكة المحلية.
لو السيستم هيتـ host على سيرفر خارجي (VPS)، لازم يشتغل نفس السكريبت ده كـ
"agent" على جهاز داخل نفس شبكة الفرع (Cron job / Windows service) وبعدين
يبعت البيانات للسيرفر عن طريق الـ API بدل ما يتصل بيه مباشرة.

pip install pyzk
"""

from datetime import datetime, timedelta

from django.utils import timezone

from employees.models import Employee
from leaves.models import LeaveRequest, PermissionRequest

from .models import AttendanceDevice, AttendanceLog, DailyAttendanceSummary

# أيام الإجازة الأسبوعية الافتراضية (Python weekday: الإثنين=0 ... الجمعة=4، السبت=5)
# غيّرها لو نظام الشركة مختلف، أو حولها لإعداد في موديل لو كل قسم له جدول مختلف.
WEEKEND_DAYS = {4, 5}  # الجمعة والسبت


def pull_from_device(device: AttendanceDevice, date_from: datetime, date_to: datetime):
    """
    يتصل بجهاز ZK، يسحب كل الحركات (attendance records)، يفلتر بالفترة
    المطلوبة، ويحفظها في AttendanceLog (مع تجاهل أي حركة متسجلة قبل كده).
    يرجع dict فيه عدد الحركات المستوردة والمتجاهلة.

    ملحوظة: استيراد pyzk هنا جوه الدالة (مش فوق الملف) عشان الجزء ده يفضل
    اختياري، ومتحتاجش تثبته لو لسه مش هتجرب سحب بصمة فعلي.
    """
    from zk import ZK  # pip install pyzk

    zk = ZK(device.ip_address, port=device.port, timeout=10)
    conn = zk.connect()
    conn.disable_device()

    imported, skipped = 0, 0
    try:
        records = conn.get_attendance()
        for record in records:
            ts = timezone.make_aware(record.timestamp) if timezone.is_naive(
                record.timestamp
            ) else record.timestamp

            if not (date_from <= ts <= date_to):
                continue

            fingerprint_id = str(record.user_id)
            exists = AttendanceLog.objects.filter(
                fingerprint_id=fingerprint_id, timestamp=ts, device=device
            ).exists()
            if exists:
                skipped += 1
                continue

            employee = Employee.objects.filter(fingerprint_id=fingerprint_id).first()
            punch_type = "in" if getattr(record, "punch", 0) == 0 else "out"

            AttendanceLog.objects.create(
                employee=employee,
                fingerprint_id=fingerprint_id,
                device=device,
                timestamp=ts,
                punch_type=punch_type,
                source="zk",
            )
            imported += 1
    finally:
        conn.enable_device()
        conn.disconnect()

    return {"imported": imported, "skipped": skipped}


# ---------------------------------------------------------------------------
# الحساب التلقائي للحضور/الغياب — بيدمج البصمة الخام مع الإجازات والأذونات
# المعتمدة، وبيكتب النتيجة في DailyAttendanceSummary (اللي بتتغذى منه صفحة
# الغياب وتفاصيل الحضور في profile الموظف).
# ---------------------------------------------------------------------------

def _employee_has_approved_leave(employee, date_):
    return LeaveRequest.objects.filter(
        employee=employee,
        status="approved",
        start_date__lte=date_,
        end_date__gte=date_,
    ).exists()


def _employee_has_approved_permission(employee, date_):
    return PermissionRequest.objects.filter(
        employee=employee, status="approved", date=date_
    ).exists()


def calculate_daily_attendance(employee, date_):
    """
    يحسب حالة يوم واحد لموظف واحد، ويحفظها (أو يحدّثها) في
    DailyAttendanceSummary. بيتنفذ بالترتيب التالي:
    1) إجازة أسبوعية (weekend) → status=weekend وخلاص.
    2) فيه بصمة دخول/خروج فعلية → status=present.
    3) مفيش بصمة، بس فيه إجازة معتمدة تغطي اليوم ده → status=leave.
    4) مفيش بصمة، بس فيه إذن معتمد في نفس اليوم → status=permission.
    5) غير كده → status=absent.
    """
    if date_.weekday() in WEEKEND_DAYS:
        return DailyAttendanceSummary.objects.update_or_create(
            employee=employee, date=date_,
            defaults={"status": "weekend", "check_in": None, "check_out": None, "worked_hours": 0},
        )[0]

    day_logs = AttendanceLog.objects.filter(
        employee=employee, timestamp__date=date_
    ).order_by("timestamp")

    if day_logs.exists():
        first_ts = day_logs.first().timestamp
        last_ts = day_logs.last().timestamp
        worked_hours = round((last_ts - first_ts).total_seconds() / 3600, 2) if last_ts != first_ts else 0
        return DailyAttendanceSummary.objects.update_or_create(
            employee=employee, date=date_,
            defaults={
                "status": "present",
                "check_in": timezone.localtime(first_ts).time(),
                "check_out": timezone.localtime(last_ts).time() if last_ts != first_ts else None,
                "worked_hours": worked_hours,
            },
        )[0]

    if _employee_has_approved_leave(employee, date_):
        status = "leave"
    elif _employee_has_approved_permission(employee, date_):
        status = "permission"
    else:
        status = "absent"

    return DailyAttendanceSummary.objects.update_or_create(
        employee=employee, date=date_,
        defaults={"status": status, "check_in": None, "check_out": None, "worked_hours": 0},
    )[0]


def calculate_attendance_range(date_from, date_to, employees=None):
    """
    يحسب كل الأيام من date_from إلى date_to (شاملة)، لكل الموظفين النشطين
    أو لقائمة موظفين محددة. بترجع عدد السجلات اللي اتحسبت.
    """
    qs = employees if employees is not None else Employee.objects.filter(status="active")
    count = 0
    current = date_from
    while current <= date_to:
        for employee in qs:
            calculate_daily_attendance(employee, current)
            count += 1
        current += timedelta(days=1)
    return count
