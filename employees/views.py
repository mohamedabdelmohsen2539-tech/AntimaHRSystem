import openpyxl
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import Department, Employee, JobTitle

# ---------------------------------------------------------------------------
# شاشة استيراد الموظفين من إكسيل (Ajax) — بتعمل بريفيو للبيانات الأول
# ثم تحفظ بعد تأكيد المستخدم.
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = ["fingerprint_id", "full_name", "hire_date"]


def _read_excel_rows(uploaded_file):
    """يرجع لستة dict لكل صف، والعمود الأول لازم يكون العناوين بالإنجليزي
    (fingerprint_id, full_name, national_id, phone, hire_date, department, job_title)."""
    wb = openpyxl.load_workbook(uploaded_file, data_only=True)
    sheet = wb.active
    headers = [str(c.value).strip() if c.value else "" for c in sheet[1]]
    rows = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        data = dict(zip(headers, row))
        if any(v not in (None, "") for v in data.values()):
            rows.append(data)
    return headers, rows


@staff_member_required
def import_employees_page(request):
    """الصفحة نفسها (GET) — الرفع والبريفيو والحفظ بيتم بـ Ajax على endpoints تحت."""
    return render(request, "employees/import_employees.html")


@staff_member_required
@require_POST
def import_employees_preview(request):
    """Ajax: يرفع الملف، يتحقق من الأعمدة المطلوبة ويرجع بريفيو + أخطاء محتملة."""
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"ok": False, "error": "لم يتم اختيار ملف"}, status=400)

    try:
        headers, rows = _read_excel_rows(uploaded_file)
    except Exception as exc:  # ملف تالف أو صيغة غير مدعومة
        return JsonResponse({"ok": False, "error": f"تعذر قراءة الملف: {exc}"}, status=400)

    missing = [c for c in REQUIRED_COLUMNS if c not in headers]
    if missing:
        return JsonResponse(
            {"ok": False, "error": f"الأعمدة الناقصة في الملف: {', '.join(missing)}"},
            status=400,
        )

    existing_ids = set(Employee.objects.values_list("fingerprint_id", flat=True))
    preview, errors = [], []
    for i, row in enumerate(rows, start=2):
        fp = str(row.get("fingerprint_id") or "").strip()
        name = str(row.get("full_name") or "").strip()
        row_errors = []
        if not fp:
            row_errors.append("رقم البصمة فارغ")
        elif fp in existing_ids:
            row_errors.append("رقم البصمة مكرر (موجود بالفعل)")
        if not name:
            row_errors.append("اسم الموظف فارغ")
        preview.append({"row": i, "data": row, "errors": row_errors})
        if row_errors:
            errors.append(i)

    return JsonResponse(
        {"ok": True, "preview": preview, "rows_with_errors": errors, "total": len(rows)}
    )


@staff_member_required
@require_POST
def import_employees_commit(request):
    """Ajax: بعد موافقة اليوزر على البريفيو، يحفظ الملف فعليًا (بيتجاهل الصفوف اللي فيها أخطاء)."""
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"ok": False, "error": "لم يتم اختيار ملف"}, status=400)

    _, rows = _read_excel_rows(uploaded_file)
    created, skipped = 0, 0

    for row in rows:
        fp = str(row.get("fingerprint_id") or "").strip()
        name = str(row.get("full_name") or "").strip()
        if not fp or not name or Employee.objects.filter(fingerprint_id=fp).exists():
            skipped += 1
            continue

        department = None
        if row.get("department"):
            department, _ = Department.objects.get_or_create(name=str(row["department"]).strip())
        job_title = None
        if row.get("job_title"):
            job_title, _ = JobTitle.objects.get_or_create(name=str(row["job_title"]).strip())

        Employee.objects.create(
            fingerprint_id=fp,
            full_name=name,
            national_id=row.get("national_id") or None,
            phone=row.get("phone") or "",
            hire_date=row.get("hire_date"),
            department=department,
            job_title=job_title,
        )
        created += 1

    return JsonResponse({"ok": True, "created": created, "skipped": skipped})


# ---------------------------------------------------------------------------
# Live search لصفحة الموظفين — بالاسم أو رقم البصمة + فلتر تاريخ التعيين
# ---------------------------------------------------------------------------

@staff_member_required
@require_GET
def employees_live_search(request):
    query = request.GET.get("q", "").strip()
    hire_from = request.GET.get("hire_from")
    hire_to = request.GET.get("hire_to")
    page_number = request.GET.get("page", 1)

    qs = Employee.objects.select_related("department", "job_title").all()
    if query:
        from django.db.models import Q

        qs = qs.filter(Q(full_name__icontains=query) | Q(fingerprint_id__icontains=query))
    if hire_from:
        qs = qs.filter(hire_date__gte=hire_from)
    if hire_to:
        qs = qs.filter(hire_date__lte=hire_to)

    paginator = Paginator(qs.order_by("full_name"), 25)
    page = paginator.get_page(page_number)

    results = [
        {
            "id": e.id,
            "full_name": e.full_name,
            "fingerprint_id": e.fingerprint_id,
            "department": e.department.name if e.department else "",
            "job_title": e.job_title.name if e.job_title else "",
            "hire_date": e.hire_date.isoformat() if e.hire_date else "",
            "status": e.get_status_display(),
        }
        for e in page.object_list
    ]

    return JsonResponse(
        {
            "results": results,
            "has_next": page.has_next(),
            "has_previous": page.has_previous(),
            "current_page": page.number,
            "num_pages": paginator.num_pages,
            "total": paginator.count,
        }
    )
