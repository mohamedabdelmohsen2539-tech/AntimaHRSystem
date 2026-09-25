from django.conf import settings
from django.db import models

from employees.models import Employee


class LeaveType(models.Model):
    """
    نوع الإجازة - جدول قابل للإضافة من الأدمن نفسه، عشان لو حبيت تضيف
    نوع جديد (بإذن / بدون إذن / أي نوع تاني) متحتاجش تعدل في الكود.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="نوع الإجازة")
    deducts_balance = models.BooleanField(
        default=True, verbose_name="يخصم من رصيد الإجازات"
    )
    requires_approval = models.BooleanField(default=True, verbose_name="يحتاج موافقة")
    max_days_per_year = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="أقصى عدد أيام بالسنة"
    )
    color = models.CharField(
        max_length=7, default="#7C3AED", verbose_name="لون العرض (Hex)"
    )

    class Meta:
        verbose_name = "نوع إجازة"
        verbose_name_plural = "أنواع الإجازات"
        ordering = ["name"]

    def __str__(self):
        return self.name


class BaseRequest(models.Model):
    """حقول مشتركة بين طلب الإجازة وطلب الإذن"""

    STATUS_CHOICES = (
        ("pending", "معلق"),
        ("approved", "موافق عليه"),
        ("rejected", "مرفوض"),
        ("cancelled", "ملغي"),
    )
    SOURCE_CHOICES = (
        ("manual", "إدخال يدوي"),
        ("mobile", "تطبيق الموبايل (Self-Service)"),
    )

    reason = models.TextField(blank=True, verbose_name="السبب")
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending", verbose_name="الحالة"
    )
    source = models.CharField(
        max_length=10, choices=SOURCE_CHOICES, default="manual", verbose_name="مصدر الطلب"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", verbose_name="تمت المراجعة بواسطة",
    )
    reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ المراجعة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ تقديم الطلب")

    class Meta:
        abstract = True


class LeaveRequest(BaseRequest):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="leave_requests"
    )
    leave_type = models.ForeignKey(
        LeaveType, on_delete=models.PROTECT, related_name="leave_requests",
        verbose_name="نوع الإجازة",
    )
    start_date = models.DateField(verbose_name="من تاريخ")
    end_date = models.DateField(verbose_name="إلى تاريخ")
    days_count = models.PositiveIntegerField(default=0, verbose_name="عدد الأيام")

    class Meta:
        verbose_name = "طلب إجازة"
        verbose_name_plural = "طلبات الإجازات"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.start_date and self.end_date and not self.days_count:
            self.days_count = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type} ({self.start_date} → {self.end_date})"


class PermissionRequest(BaseRequest):
    """إذن خروج/تأخير"""
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="permission_requests"
    )
    date = models.DateField(verbose_name="التاريخ")
    from_time = models.TimeField(verbose_name="من الساعة")
    to_time = models.TimeField(verbose_name="إلى الساعة")

    class Meta:
        verbose_name = "إذن"
        verbose_name_plural = "الأذونات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.full_name} - إذن {self.date}"
