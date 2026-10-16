"""Bilingual UI strings (English / Arabic) with a tiny translator.

Usage:
    from poultryguard import i18n
    t = i18n.translator(lang)      # lang in {"en", "ar"}
    st.subheader(t("live_title"))

Missing keys fall back to English, then to the key itself.
"""
from __future__ import annotations

LANGS = {"en": "English", "ar": "العربية"}
RTL = {"ar"}

TR = {
    "en": {
        # app / header
        "app_title": "PoultryGuard AI",
        "app_sub": "Smart poultry health monitoring · mortality detection · veterinary response",
        # controls
        "control_panel": "control panel",
        "language": "Language", "theme": "Theme", "dark": "Dark", "light": "Light",
        "logout": "Log out", "signed_in_as": "Signed in as",
        "farm_flock": "Farm / flock", "farm_id": "Farm ID", "house_id": "House ID",
        "flock_age": "Flock age (days)",
        "detection": "Detection", "confidence": "Confidence", "inf_size": "Inference size",
        "tiled": "Tiled inference (very dense houses)",
        "mortality_thresholds": "Mortality thresholds",
        "immobile_abnormal": "Immobile → abnormal (s)",
        "immobile_suspected": "Immobile+lying → suspected (s)",
        "zone_rows": "Zone rows", "zone_cols": "Zone cols",
        "camera_source": "Camera source",
        "demo_video": "Demo video (sample loop)", "upload_video": "Upload video",
        "upload_images": "Upload image(s)", "webcam": "Webcam (local)",
        "ip_camera": "IP camera (RTSP/HTTP)", "stream_url": "Stream URL",
        "cam_note": "Webcam & RTSP need a local/edge deployment; on the cloud use Demo or Upload.",
        "start": "Start", "stop": "Stop", "inject_demo": "Inject demo mortality",
        "inject_help": "Force one bird to suspected mortality to demo the full vet workflow",
        # nav
        "nav_live": "Live Monitor", "nav_cases": "Mortality Cases", "nav_vet": "Vet Console",
        "nav_env": "Environment", "nav_dash": "Dashboard", "nav_dataset": "Dataset",
        "nav_req": "Requirements",
        # live
        "live_title": "Live Monitor",
        "live_caption": "Detection · counting · individual tracking · immobility & posture · automatic mortality case registration.",
        "live_count": "Live count", "suspected": "suspected", "flock_stable": "flock stable",
        "abnormal_resting": "Abnormal / resting", "pipeline_fps": "Pipeline FPS",
        "press_start": "Press **Start** in the control panel to begin monitoring.",
        "counted": "counted", "chickens": "chickens",
        "no_frame": "No frame from source. For RTSP, check the URL / credentials; for the demo video, generate it (see Requirements tab).",
        "case_opened": "Mortality case opened",
        # cases
        "cases_title": "Mortality Cases",
        "no_cases": "No cases yet. Use **Inject demo mortality**, or let the immobility logic flag a motionless bird on a live feed.",
        "open_case": "Open case", "evidence": "Evidence", "bird": "bird", "zone": "Zone",
        "suspected_at": "Suspected mortality", "notify_vet": "Notify veterinarian",
        "visit_slot": "Visit slot", "book_visit": "Book farm visit",
        # vet console
        "vet_title": "Veterinary Console", "no_open_cases": "No open cases.",
        "case": "Case", "veterinarian": "Veterinarian", "diagnosis": "Diagnosis",
        "treatment": "Treatment / medication", "vaccination": "Vaccination",
        "log_diagnosis": "Log diagnosis", "log_treatment": "Log treatment",
        "log_vaccination": "Log vaccination", "close_case": "Close case",
        "action_history": "Action history", "status": "status", "age": "age",
        "review_case": "Review case", "record_examination": "Record on-site exam",
        "exam_findings": "Examination findings", "follow_up": "Follow-up monitoring",
        "follow_up_when": "Follow-up date / time", "follow_up_notes": "Follow-up notes",
        "schedule_follow_up": "Schedule follow-up", "evidence_clip": "Captured video clip",
        # environment
        "env_title": "Environmental Early-Warning",
        "env_caption": "Fuse environment with behaviour to warn before mortality. Sensors simulated here; swap for a Modbus/MQTT feed in production.",
        "temp": "Temperature °C", "humidity": "Humidity %", "co2": "CO₂ ppm", "nh3": "NH₃ ppm",
        "target": "target", "limit": "limit",
        "spike_nh3": "Spike NH₃", "spike_co2": "Spike CO₂", "heat": "Heat stress",
        "cold": "Cold stress", "clear": "Clear",
        "env_ok": "All environmental parameters within target bands.",
        # dashboard
        "dash_title": "Flock Dashboard", "current_count": "Current count",
        "open_cases": "Open cases", "total_cases": "Total mortality cases",
        "flock_age_short": "Flock age", "count_suspected": "Live count & suspected mortality",
        "by_zone": "Mortality cases by house zone — hotspots for inspection",
        # dataset
        "dataset_title": "Mortality Posture Dataset",
        "dataset_caption": "Every opened case stores a cropped snapshot + posture label. Export them as a training-ready set to build the labelled dataset the brief proposes (day 0–45).",
        "captured": "Captured mortality snapshots", "export": "Export dataset",
        # requirements
        "req_title": "Requirement coverage & model status",
        "pipeline": "End-to-end pipeline", "requirement": "Requirement",
        "implemented_in": "Implemented in", "see_tab": "See tab", "detector": "Detector",
        "model_active": "Fine-tuned chicken model active",
        "model_fallback": "Generic fallback (train for production accuracy)",
        "map50": "Test mAP@50", "precision": "Precision", "recall": "Recall",
        "count_err": "Count error (dense)",
        "validated": "Validated on the held-out test split (GEL broiler dataset, Roboflow, CC BY 4.0).",
        # login
        "login_welcome": "Sign in to PoultryGuard",
        "login_sub": "AI poultry health monitoring & veterinary response",
        "username": "Username", "password": "Password", "role": "Role",
        "sign_in": "Sign in", "invalid_login": "Invalid username or password.",
        "demo_accounts": "Demo accounts",
        "role_admin": "Administrator", "role_vet": "Veterinarian", "role_operator": "Farm Operator",
    },
    "ar": {
        "app_title": "بولتري جارد",
        "app_sub": "مراقبة ذكية لصحة الدواجن · كشف النفوق · الاستجابة البيطرية",
        "control_panel": "لوحة التحكم",
        "language": "اللغة", "theme": "المظهر", "dark": "داكن", "light": "فاتح",
        "logout": "تسجيل الخروج", "signed_in_as": "مسجّل الدخول باسم",
        "farm_flock": "المزرعة / القطيع", "farm_id": "معرّف المزرعة", "house_id": "معرّف الحظيرة",
        "flock_age": "عمر القطيع (أيام)",
        "detection": "الكشف", "confidence": "الثقة", "inf_size": "دقة الاستدلال",
        "tiled": "استدلال مُجزّأ (حظائر عالية الكثافة)",
        "mortality_thresholds": "عتبات النفوق",
        "immobile_abnormal": "ثابت ← غير طبيعي (ث)",
        "immobile_suspected": "ثابت + مستلقٍ ← مُشتبه (ث)",
        "zone_rows": "صفوف المناطق", "zone_cols": "أعمدة المناطق",
        "camera_source": "مصدر الكاميرا",
        "demo_video": "فيديو توضيحي (تكرار)", "upload_video": "رفع فيديو",
        "upload_images": "رفع صورة/صور", "webcam": "كاميرا محلية",
        "ip_camera": "كاميرا IP (RTSP/HTTP)", "stream_url": "رابط البث",
        "cam_note": "تتطلب الكاميرا و RTSP تشغيلاً محلياً/طرفياً؛ على السحابة استخدم الفيديو التوضيحي أو الرفع.",
        "start": "بدء", "stop": "إيقاف", "inject_demo": "محاكاة حالة نفوق",
        "inject_help": "فرض اشتباه نفوق على طائر لعرض سير العمل البيطري كاملاً",
        "nav_live": "المراقبة المباشرة", "nav_cases": "حالات النفوق", "nav_vet": "الوحدة البيطرية",
        "nav_env": "البيئة", "nav_dash": "لوحة المعلومات", "nav_dataset": "البيانات",
        "nav_req": "المتطلبات",
        "live_title": "المراقبة المباشرة",
        "live_caption": "الكشف · العدّ · التتبع الفردي · السكون والوضعية · تسجيل حالات النفوق تلقائياً.",
        "live_count": "العدد الحالي", "suspected": "مشتبه", "flock_stable": "القطيع مستقر",
        "abnormal_resting": "غير طبيعي / ساكن", "pipeline_fps": "إطارات/ث",
        "press_start": "اضغط **بدء** في لوحة التحكم لبدء المراقبة.",
        "counted": "تم عدّ", "chickens": "دجاجة",
        "no_frame": "لا يوجد إطار من المصدر. لـ RTSP تحقق من الرابط/البيانات؛ للفيديو التوضيحي أنشئه (انظر تبويب المتطلبات).",
        "case_opened": "تم فتح حالة نفوق",
        "cases_title": "حالات النفوق",
        "no_cases": "لا توجد حالات بعد. استخدم **محاكاة حالة نفوق**، أو دع منطق السكون يرصد طائراً بلا حركة.",
        "open_case": "فتح الحالة", "evidence": "الدليل", "bird": "طائر", "zone": "المنطقة",
        "suspected_at": "اشتباه نفوق", "notify_vet": "إبلاغ الطبيب البيطري",
        "visit_slot": "موعد الزيارة", "book_visit": "حجز زيارة ميدانية",
        "vet_title": "الوحدة البيطرية", "no_open_cases": "لا توجد حالات مفتوحة.",
        "case": "الحالة", "veterinarian": "الطبيب البيطري", "diagnosis": "التشخيص",
        "treatment": "العلاج / الدواء", "vaccination": "التطعيم",
        "log_diagnosis": "تسجيل التشخيص", "log_treatment": "تسجيل العلاج",
        "log_vaccination": "تسجيل التطعيم", "close_case": "إغلاق الحالة",
        "action_history": "سجل الإجراءات", "status": "الحالة", "age": "العمر",
        "review_case": "مراجعة الحالة", "record_examination": "تسجيل الفحص الميداني",
        "exam_findings": "نتائج الفحص", "follow_up": "متابعة المراقبة",
        "follow_up_when": "تاريخ/وقت المتابعة", "follow_up_notes": "ملاحظات المتابعة",
        "schedule_follow_up": "جدولة المتابعة", "evidence_clip": "مقطع الفيديو الملتقط",
        "env_title": "الإنذار البيئي المبكر",
        "env_caption": "دمج البيئة مع السلوك للتحذير قبل النفوق. الحساسات محاكاة هنا؛ تُستبدل ببث Modbus/MQTT في الإنتاج.",
        "temp": "الحرارة °م", "humidity": "الرطوبة %", "co2": "CO₂ جزء/مليون", "nh3": "NH₃ جزء/مليون",
        "target": "المستهدف", "limit": "الحد",
        "spike_nh3": "رفع NH₃", "spike_co2": "رفع CO₂", "heat": "إجهاد حراري",
        "cold": "إجهاد بارد", "clear": "مسح",
        "env_ok": "جميع القيم البيئية ضمن النطاقات المستهدفة.",
        "dash_title": "لوحة معلومات القطيع", "current_count": "العدد الحالي",
        "open_cases": "حالات مفتوحة", "total_cases": "إجمالي حالات النفوق",
        "flock_age_short": "عمر القطيع", "count_suspected": "العدد المباشر والنفوق المشتبه",
        "by_zone": "حالات النفوق حسب منطقة الحظيرة — بؤر التفتيش",
        "dataset_title": "مجموعة بيانات وضعيات النفوق",
        "dataset_caption": "كل حالة مفتوحة تحفظ صورة مقصوصة + تصنيف الوضعية. صدّرها كمجموعة جاهزة للتدريب (من اليوم 0 إلى 45).",
        "captured": "لقطات النفوق المُلتقطة", "export": "تصدير البيانات",
        "req_title": "تغطية المتطلبات وحالة النموذج",
        "pipeline": "خط المعالجة الكامل", "requirement": "المتطلب",
        "implemented_in": "مُنفّذ في", "see_tab": "التبويب", "detector": "الكاشف",
        "model_active": "نموذج الدجاج المُدرَّب فعّال",
        "model_fallback": "النموذج الاحتياطي العام (درّب لدقة الإنتاج)",
        "map50": "mAP@50 (اختبار)", "precision": "الدقة", "recall": "الاستدعاء",
        "count_err": "خطأ العدّ (كثيف)",
        "validated": "تم التحقق على مجموعة الاختبار المعزولة (بيانات GEL للدواجن، Roboflow، CC BY 4.0).",
        "login_welcome": "تسجيل الدخول إلى بولتري جارد",
        "login_sub": "مراقبة صحة الدواجن بالذكاء الاصطناعي والاستجابة البيطرية",
        "username": "اسم المستخدم", "password": "كلمة المرور", "role": "الدور",
        "sign_in": "تسجيل الدخول", "invalid_login": "اسم المستخدم أو كلمة المرور غير صحيحة.",
        "demo_accounts": "حسابات تجريبية",
        "role_admin": "مدير النظام", "role_vet": "طبيب بيطري", "role_operator": "مشغّل المزرعة",
    },
}


def translator(lang: str):
    lang = lang if lang in TR else "en"

    def t(key: str) -> str:
        return TR[lang].get(key) or TR["en"].get(key, key)
    return t


def is_rtl(lang: str) -> bool:
    return lang in RTL
