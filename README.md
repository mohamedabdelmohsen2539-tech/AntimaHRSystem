# نظام الموارد البشرية (HR) — تشغيل تجريبي محلي

الملف ده دلوقتي مشروع Django كامل شغال لوحده (فيه `manage.py`)، عشان تقدر
تجربه وتشوفه في المتصفح. بعد ما تتأكد إنه شغال زي ما عايز، ندمج الأجزاء دي
(الـ apps التلاتة + إعدادات UNFOLD) جوه مشروع المبيعات/المخازن الأساسي.

## خطوات التشغيل

```bash
# 1) افتح مجلد المشروع
cd hr_system

# 2) اعمل بيئة افتراضية (مرة واحدة بس)
python3 -m venv venv
source venv/bin/activate      # على Windows: venv\Scripts\activate

# 3) ثبّت المكتبات
pip install -r requirements.txt

# 4) جهّز قاعدة البيانات
python manage.py makemigrations employees leaves attendance
python manage.py migrate

# 5) اعمل مستخدم أدمن عشان تدخل بيه
python manage.py createsuperuser

# 6) شغّل السيرفر
python manage.py runserver
```

بعد كده افتح المتصفح على:

- **`http://127.0.0.1:8000/admin/`** → لوحة الأدمن (Unfold) — من هنا تقدر
  تضيف موظف، قسم، مسمى وظيفي، نوع إجازة، وتشوف تاب المرتب/المستندات/المؤهلات/
  الجزاءات/الإجازات/الحضور كلهم جوه صفحة الموظف نفسها.
- **`http://127.0.0.1:8000/hr/employees/import/`** → شاشة استيراد الموظفين
  من إكسيل (الأعمدة المطلوبة: `fingerprint_id, full_name, hire_date`).
- **`http://127.0.0.1:8000/hr/attendance/absence/`** → صفحة الغياب والحساب
  التلقائي (فلترة + زرار إعادة حساب).

## ملحوظة عن مكتبة pyzk

لو مش هتجرب سحب بصمات فعلي دلوقتي، مش لازم تثبّت `pyzk` أو تشغّل أي حاجة
في `attendance/services.py::pull_from_device` — هي مش بتتنادى تلقائي من أي
مكان، وباقي المشروع هيشتغل من غيرها عادي.

## لما تيجي تدمج مع المشروع الأساسي (المبيعات والمخازن)

1. انسخ فولدرات `employees/` و `leaves/` و `attendance/` جوه مشروعك الأساسي.
2. من `config/settings.py` هنا، انقل بس:
   - الأسطر التلاتة بتاعة `employees, attendance, leaves` في `INSTALLED_APPS`
     (لو `unfold` مش مضاف أصلاً هناك، ضيفه برضو زي ما هو فوق).
   - إعدادات `UNFOLD` (أو ادمجها مع أي إعدادات UNFOLD موجودة عندك بالفعل).
3. من `config/urls.py` هنا، انسخ سطرين الـ `include` بتوع
   `employees.urls` و `attendance.urls`.
4. شغّل `makemigrations` و `migrate` تاني على قاعدة بيانات مشروعك الأساسي.

`config_settings_snippet.py` الموجود في نفس المجلد ده نفس المرجع ده بس
مكتوب كملاحظات بس من غير باقي إعدادات المشروع (لو حابب ترجع له تاني).
