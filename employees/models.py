from django.conf import settings
from django.db import models


class Department(models.Model):
    """القسم / الإدارة"""
    name = models.CharField(max_length=150, unique=True, verbose_name="اسم القسم")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "قسم"
        verbose_name_plural = "الأقسام"
        ordering = ["name"]

    def __str__(self):
        return self.name


class JobTitle(models.Model):
    """المسمى الوظيفي"""
    name = models.CharField(max_length=150, unique=True, verbose_name="المسمى الوظيفي")

    class Meta:
        verbose_name = "مسمى وظيفي"
        verbose_name_plural = "المسميات الوظيفية"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Employee(models.Model):
    """
    الموظف - الشاشة الرئيسية اللي كل حاجة تانية (المرتب، المستندات، المؤهلات،
    الجزاءات، الإجازات، الحضور) بترتبط بيها.
    """

    GENDER_CHOICES = (
        ("male", "ذكر"),
        ("female", "أنثى"),
    )
    STATUS_CHOICES = (
        ("active", "على رأس العمل"),
        ("inactive", "غير نشط"),
        ("resigned", "مستقيل"),
        ("terminated", "تم إنهاء الخدمة"),
    )
    MARITAL_CHOICES = (
        ("single", "أعزب"),
        ("married", "متزوج"),
        ("divorced", "مطلق"),
        ("widowed", "أرمل"),
    )

    # --- التعريف الأساسي ---
    fingerprint_id = models.CharField(
        max_length=20, unique=True, db_index=True, verbose_name="رقم البصمة"
    )
    full_name = models.CharField(max_length=200, verbose_name="الاسم بالكامل")
    photo = models.ImageField(
        upload_to="employees/photos/", blank=True, null=True, verbose_name="الصورة"
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default="active", verbose_name="الحالة"
    )

    # --- البيانات الأساسية ---
    national_id = models.CharField(
        max_length=20, unique=True, blank=True, null=True, verbose_name="الرقم القومي"
    )
    birth_date = models.DateField(blank=True, null=True, verbose_name="تاريخ الميلاد")
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, default="male", verbose_name="النوع"
    )
    marital_status = models.CharField(
        max_length=10, choices=MARITAL_CHOICES, blank=True, null=True,
        verbose_name="الحالة الاجتماعية",
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    address = models.TextField(blank=True, verbose_name="العنوان")

    # --- البيانات الوظيفية ---
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="employees", verbose_name="القسم",
    )
    job_title = models.ForeignKey(
        JobTitle, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="employees", verbose_name="الوظيفة",
    )
    hire_date = models.DateField(verbose_name="تاريخ التعيين")

    # --- ربط اختياري بحساب دخول (لازم للأتمتة/تطبيق الموبايل) ---
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="employee_profile", verbose_name="حساب الدخول (للأتمتة)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "موظف"
        verbose_name_plural = "الموظفين"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.fingerprint_id})"


class EmployeeSalary(models.Model):
    """
    بيانات المرتب - محمية: بتتعرض بس لليوزر اللي عنده صلاحية
    employees.view_confidential_salary (شوف admin.py).
    """
    employee = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name="salary"
    )
    basic_salary = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="الراتب الأساسي"
    )
    allowances = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="البدلات"
    )
    deductions = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="الاستقطاعات"
    )
    bank_name = models.CharField(max_length=100, blank=True, verbose_name="اسم البنك")
    bank_account = models.CharField(max_length=50, blank=True, verbose_name="رقم الحساب")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")

    class Meta:
        verbose_name = "بيانات مرتب"
        verbose_name_plural = "بيانات المرتبات"
        permissions = [
            ("view_confidential_salary", "يمكنه رؤية بيانات المرتب"),
        ]

    @property
    def net_salary(self):
        return self.basic_salary + self.allowances - self.deductions

    def __str__(self):
        return f"مرتب {self.employee.full_name}"


class EmployeeDocument(models.Model):
    """المستندات: بطاقة / باسبور / عقد / شهادات ملفات"""
    DOC_TYPES = (
        ("national_id", "بطاقة الرقم القومي"),
        ("passport", "جواز السفر"),
        ("certificate", "شهادة"),
        ("contract", "عقد العمل"),
        ("other", "أخرى"),
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="documents"
    )
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES, verbose_name="نوع المستند")
    file = models.FileField(upload_to="employees/documents/", verbose_name="الملف")
    issue_date = models.DateField(blank=True, null=True, verbose_name="تاريخ الإصدار")
    expiry_date = models.DateField(blank=True, null=True, verbose_name="تاريخ الانتهاء")
    notes = models.CharField(max_length=255, blank=True, verbose_name="ملاحظات")

    class Meta:
        verbose_name = "مستند"
        verbose_name_plural = "المستندات والبطاقة/الباسبور"

    def __str__(self):
        return f"{self.get_doc_type_display()} - {self.employee.full_name}"


class EmployeeQualification(models.Model):
    """المؤهلات والشهادات الدراسية"""
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="qualifications"
    )
    qualification_name = models.CharField(max_length=200, verbose_name="المؤهل/الشهادة")
    institution = models.CharField(max_length=200, blank=True, verbose_name="جهة الحصول")
    graduation_year = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="سنة الحصول"
    )
    grade = models.CharField(max_length=50, blank=True, verbose_name="التقدير")

    class Meta:
        verbose_name = "مؤهل دراسي"
        verbose_name_plural = "المؤهلات والتأهيلات"

    def __str__(self):
        return f"{self.qualification_name} - {self.employee.full_name}"


class Penalty(models.Model):
    """الجزاءات"""
    PENALTY_TYPES = (
        ("warning", "إنذار"),
        ("deduction", "خصم مالي"),
        ("suspension", "إيقاف عن العمل"),
        ("other", "أخرى"),
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="penalties"
    )
    penalty_type = models.CharField(
        max_length=15, choices=PENALTY_TYPES, verbose_name="نوع الجزاء"
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True,
        verbose_name="القيمة / عدد الأيام",
    )
    reason = models.TextField(verbose_name="السبب")
    date = models.DateField(verbose_name="التاريخ")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "جزاء"
        verbose_name_plural = "الجزاءات"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.get_penalty_type_display()} - {self.employee.full_name}"
