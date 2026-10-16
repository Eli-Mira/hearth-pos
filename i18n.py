"""Arabic/English translations for Hearth POS UI strings."""
from __future__ import annotations

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # App name
        "app_name": "Restaurant POS",
        # Login
        "enter_pin": "Enter your PIN to begin",
        "staff_pin_required": "Staff PIN required",
        "invalid_pin": "Invalid PIN",
        "welcome": "Welcome, {name}",
        "confirm": "Confirm",
        "cancel": "Cancel",
        # Manager dashboard
        "manager_dashboard": "MANAGER DASHBOARD",
        "logged_in_as": "Logged in as: {name} ({role})",
        "logout": "Logout",
        "menu_tab": "📋 Menu",
        "staff_tab": "👥 Staff",
        "reports_tab": "📊 Reports",
        "inventory_tab": "📦 Inventory",
        "shifts_tab": "💰 Shifts",
        "settings_tab": "⚙️ Settings",
        "add_category": "➕ Add Category",
        "add_item": "➕ Add Item",
        "add_staff": "➕ Add Staff",
        "refresh": "🔄 Refresh",
        "new_category": "New Category",
        "category_name": "Category name:",
        "edit_category": "Edit Category",
        "delete_category": "Delete Category",
        "delete_confirm": "Delete '{name}'? This will soft-delete the category.",
        "add_menu_item": "Add Menu Item",
        "item_name": "Name:",
        "category": "Category:",
        "price": "Price:",
        "track_stock": "Track Stock:",
        "yes": "Yes",
        "no": "No",
        "initial_stock": "Initial Stock:",
        "low_stock_alert": "Low Stock Alert:",
        "save": "Save",
        "reset_pin": "Reset PIN",
        "deactivate": "Deactivate",
        "deactivate_confirm": "Deactivate {name}?",
        # Reports
        "daily_sales_report": "Daily Sales Report",
        "generate_report": "🔄 Generate Report",
        "report_placeholder": "Click Generate Report to view today's summary",
        # Inventory
        "inventory_tracked": "Inventory (Tracked Items)",
        "stock_label": "Stock: {qty}",
        "low_alert": "⚠️ LOW",
        # Shifts
        "current_shift": "Current Shift",
        "opened_by": "Opened by: {name}",
        "opened": "Opened: {time}",
        "float": "Float: ${amount:.2f}",
        "end_shift": "💰 End Shift",
        "no_active_shift": "No Active Shift",
        "start_shift": "💰 Start Shift",
        "recent_shifts": "Recent Shifts",
        # Settings
        "settings": "Settings",
        "theme": "Theme",
        "dark": "🌙 Dark",
        "light": "☀️ Light",
        "language": "Language",
        # Floor plan
        "floor_plan": "Floor Plan",
        "takeaway": "Takeaway",
        "delivery": "Delivery",
        "manager": "Manager",
        "shift": "Shift",
        "logout_btn": "Logout",
        "no_active_shift_btn": "Start Shift",
        "active_shift_btn": "End Shift",
        # Checkout
        "payment_complete": "Payment Complete",
        "payment_method": "Payment Method",
        "cash": "Cash",
        "card": "Card",
        "tendered": "Tendered",
        "change": "Change",
        "total": "Total",
        "subtotal": "Subtotal",
        "tax": "Tax",
        # Kitchen
        "kitchen": "KITCHEN",
        "done": "Done",
        # Order
        "back": "← Back",
        "send_to_kitchen": "Send to Kitchen",
        # Generic
        "error": "Error",
        "success": "Success",
        "delete": "Delete",
        "edit": "Edit",
        "create": "Create",
        "required": "{field} is required",
        "invalid_input": "Invalid input",
        "yes_btn": "Yes",
        "no_btn": "No",
        # Lockout
        "locked_title": "Account Locked",
        "locked_message": "Too many failed attempts. Try again in {minutes} minutes.",
        "locked_message_secs": "Too many failed attempts. Try again in {seconds} seconds.",
        # Receipt
        "receipt": "Receipt",
        "order_id": "Order #{id}",
        "item": "Item",
        "qty": "Qty",
        "price_col": "Price",
        "total_col": "Total",
        "payment_summary": "Payment Summary",
        "change_due": "Change Due",
        "thank_you": "Thank you!",
    },
    "ar": {
        # App name
        "app_name": "نظام نقاط البيع",
        # Login
        "enter_pin": "أدخل رمز PIN للمتابعة",
        "staff_pin_required": "مطلوب رمز PIN للموظفين",
        "invalid_pin": "رمز PIN غير صحيح",
        "welcome": "مرحباً، {name}",
        "confirm": "تأكيد",
        "cancel": "إلغاء",
        # Manager dashboard
        "manager_dashboard": "لوحة المدير",
        "logged_in_as": "مسجل كـ: {name} ({role})",
        "logout": "تسجيل خروج",
        "menu_tab": "📋 القائمة",
        "staff_tab": "👥 الموظفين",
        "reports_tab": "📊 التقارير",
        "inventory_tab": "📦 المخزون",
        "shifts_tab": "💰 الورديات",
        "settings_tab": "⚙️ الإعدادات",
        "add_category": "➕ إضافة فئة",
        "add_item": "➕ إضافة صنف",
        "add_staff": "➕ إضافة موظف",
        "refresh": "🔄 تحديث",
        "new_category": "فئة جديدة",
        "category_name": "اسم الفئة:",
        "edit_category": "تعديل الفئة",
        "delete_category": "حذف الفئة",
        "delete_confirm": "حذف '{name}'؟ سيتم حذف الفئة بشكل ناعم.",
        "add_menu_item": "إضافة صنف للقائمة",
        "item_name": "الاسم:",
        "category": "الفئة:",
        "price": "السعر:",
        "track_stock": "تتبع المخزون:",
        "yes": "نعم",
        "no": "لا",
        "initial_stock": "المخزون الأولي:",
        "low_stock_alert": "تنبيه انخفاض المخزون:",
        "save": "حفظ",
        "reset_pin": "إعادة تعيين PIN",
        "deactivate": "إلغاء تفعيل",
        "deactivate_confirm": "إلغاء تفعيل {name}؟",
        # Reports
        "daily_sales_report": "تقرير المبيعات اليومي",
        "generate_report": "🔄 إنشاء التقرير",
        "report_placeholder": "اضغط إنشاء التقرير لعرض ملخص اليوم",
        # Inventory
        "inventory_tracked": "المخزون (الأصناف المتتبعة)",
        "stock_label": "المخزون: {qty}",
        "low_alert": "⚠️ منخفض",
        # Shifts
        "current_shift": "الوردية الحالية",
        "opened_by": "فتحت بواسطة: {name}",
        "opened": "فتحت: {time}",
        "float": "رصيد افتتاحي: ${amount:.2f}",
        "end_shift": "💰 إنهاء الوردية",
        "no_active_shift": "لا توجد وردية نشطة",
        "start_shift": "💰 بدء الوردية",
        "recent_shifts": "الورديات الأخيرة",
        # Settings
        "settings": "الإعدادات",
        "theme": "المظهر",
        "dark": "🌙 داكن",
        "light": "☀️ فاتح",
        "language": "اللغة",
        # Floor plan
        "floor_plan": "مخطط الطابق",
        "takeaway": "للخارج",
        "delivery": "توصيل",
        "manager": "المدير",
        "shift": "الوردية",
        "logout_btn": "تسجيل خروج",
        "no_active_shift_btn": "بدء الوردية",
        "active_shift_btn": "إنهاء الوردية",
        # Checkout
        "payment_complete": "اكتمل الدفع",
        "payment_method": "طريقة الدفع",
        "cash": "نقدي",
        "card": "بطاقة",
        "tendered": "المبلغ المستلم",
        "change": "الباقي",
        "total": "الإجمالي",
        "subtotal": "المجموع الفرعي",
        "tax": "الضريبة",
        # Kitchen
        "kitchen": "المطبخ",
        "done": "تم",
        # Order
        "back": "→ رجوع",
        "send_to_kitchen": "إرسال للمطبخ",
        # Generic
        "error": "خطأ",
        "success": "نجح",
        "delete": "حذف",
        "edit": "تعديل",
        "create": "إنشاء",
        "required": "{field} مطلوب",
        "invalid_input": "مدخل غير صالح",
        "yes_btn": "نعم",
        "no_btn": "لا",
        # Lockout
        "locked_title": "الحساب مقفل",
        "locked_message": "محاولات فاشلة كثيرة. حاول مرة أخرى بعد {minutes} دقيقة.",
        "locked_message_secs": "محاولات فاشلة كثيرة. حاول مرة أخرى بعد {seconds} ثانية.",
        # Receipt
        "receipt": "إيصال",
        "order_id": "طلب #{id}",
        "item": "الصنف",
        "qty": "الكمية",
        "price_col": "السعر",
        "total_col": "الإجمالي",
        "payment_summary": "ملخص الدفع",
        "change_due": "الباقي",
        "thank_you": "شكراً لك!",
    },
}

_current_lang = "en"


def set_language(lang: str) -> None:
    global _current_lang
    _current_lang = lang if lang in TRANSLATIONS else "en"


def get_language() -> str:
    return _current_lang


def t(key: str, **kwargs: object) -> str:
    """Translate a string key into the current language."""
    translations = TRANSLATIONS.get(_current_lang, TRANSLATIONS["en"])
    text = translations.get(key, TRANSLATIONS["en"].get(key, key))
    try:
        return text.format(**kwargs)
    except (KeyError, ValueError):
        return text
