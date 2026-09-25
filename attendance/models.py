from django.db import models

from employees.models import Employee


class AttendanceDevice(models.Model):
    """
    إعدادات جهاز بصمة ZK. ملحوظة تقنية: السحب المباشر (pyzk) بيحتاج
    السيرفر يكون على نفس شبكة الجهاز، أو agent محلي بيبعت البيانات للسيستم.
    """
    name = models.CharField(max_length=100, verbose_name="اسم الجهاز")
    ip_address = models.GenericIPAddressField(verbose_name="عنوان IP")
    port = models.PositiveIntegerField(default=4370, verbose_name="البورت")
    location = models.CharField(max_length=150, blank=True, verbose_name="الموقع")
    is_active = models.BooleanField(default=True, verbose_name="نشط")

    class Meta:
        verbose_name = "جهاز بصمة"
        verbose_name_plural = "أجهزة البصمة (ZK)"

    def __str__(self):
        return f"{self.name} ({self.ip_address})"


class AttendanceLog(models.Model):
    """سجل البصمة الخام (كل حركة دخول/خروج) - المصدر الأساسي لحساب الحضور والغياب"""

    SOURCE_CHOICES = (
        ("zk", "سحب من جهاز ZK"),
        ("excel", "استيراد إكسيل"),
        ("manual", "إدخال يدوي"),
    )
    PUNCH_CHOICES = (
        ("in", "حضور"),
        ("out", "انصراف"),
        ("unknown", "غير محدد"),
    )

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="attendance_logs",
        null=True, blank=True,
    )
    fingerprint_id = models.CharField(
        max_length=20, db_index=True, verbose_name="رقم البصمة"
    )
    device = models.ForeignKey(
        AttendanceDevice, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="logs",
    )
    timestamp = models.DateTimeField(db_index=True, verbose_name="التوقيت")
    punch_type = models.CharField(
        max_length=10, choices=PUNCH_CHOICES, default="unknown", verbose_name="نوع الحركة"
    )
    source = models.CharField(
        max_length=10, choices=SOURCE_CHOICES, default="zk", verbose_name="المصدر"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "بصمة"
        verbose_name_plural = "سجل البصمات"
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["fingerprint_id", "timestamp"])]

    def __str__(self):
        return f"{self.fingerprint_id} - {self.timestamp}"


class DailyAttendanceSummary(models.Model):
    """
    ملخص محسوب ليوم واحد لكل موظف = المصدر اللي بتتغذى منه صفحة الغياب
    وتفاصيل الحضور في profile الموظف. بيتحسب من AttendanceLog + الإجازات
    والأذونات المعتمدة لنفس اليوم.
    """
    STATUS_CHOICES = (
        ("present", "حاضر"),
        ("absent", "غائب"),
        ("leave", "إجازة"),
        ("permission", "إذن"),
        ("weekend", "إجازة أسبوعية"),
    )

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="daily_summaries"
    )
    date = models.DateField(db_index=True, verbose_name="التاريخ")
    check_in = models.TimeField(blank=True, null=True, verbose_name="وقت الحضور")
    check_out = models.TimeField(blank=True, null=True, verbose_name="وقت الانصراف")
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default="present", verbose_name="الحالة"
    )
    worked_hours = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name="ساعات العمل"
    )

    class Meta:
        verbose_name = "ملخص يوم حضور"
        verbose_name_plural = "ملخص الحضور اليومي"
        unique_together = ("employee", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.get_status_display()})"
