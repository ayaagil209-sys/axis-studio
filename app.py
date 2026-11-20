import json
import os
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
CONTENT_FILE = DATA_DIR / "content.json"
MESSAGES_FILE = DATA_DIR / "messages.json"
ALLOWED_EXT = {"jpg", "jpeg", "png", "webp"}

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me")

DEFAULT_CONTENT = {
    "site_name": "Axis Studio",
    "hero_title": "من النجمة والمضلع نبني مساحات تحمل هويتها",
    "hero_text": "Axis Studio استوديو يستلهم من الهندسة الإسلامية وتراثها الزخرفي، ليقدم عمارة وتصميماً داخلياً معاصراً يحافظ على الروح والهوية.",
    "about_text": "نؤمن بأن الهندسة الإسلامية منظومة من النسب والتكرار والضوء والظل، تصلح لتشكيل مساحات حديثة. نعمل على العمارة والتصميم الداخلي والزخارف المعمارية.",
    "about_quote": "الجمال في الهندسة الإسلامية يولد من التكرار المنتظم، وفي تصاميمنا نجعل هذا التكرار يحكي قصة كل مكان.",
    "stats": "+120|مشروع\n+15|سنة خبرة\n+60|عميل",
    "categories": "عمارة|مباني سكنية وتجارية وثقافية بروح تراثية معاصرة\nتصميم داخلي|فراغات دافئة بزخارف جبسية وخشبية وإضاءة مدروسة\nالريندر|مشاهد ثلاثية الأبعاد تُظهر المشروع قبل بنائه\nالزخارف المعمارية|تصميم الأنماط الهندسية والمشربيات والواجهات",
    "services": "التصميم المعماري|واجهات وكتل ومخططات تتكامل مع الموقع وتعكس الهوية الإسلامية المعاصرة.\nالتصميم الداخلي|تنسيق الفراغات والأثاث والإضاءة والخامات بطابع دافئ وهادئ.\nالزخارف المعمارية|تصميم أنماط هندسية مخصصة للجدران والأسقف والواجهات والمشربيات.\nالريندر ثلاثي الأبعاد|مشاهد واقعية تساعد على اتخاذ القرار وتسويق المشروع بوضوح.",
    "process": "الاستكشاف|نستمع إلى رؤيتك ونزور الموقع ونحدد الأهداف والميزانية.\nالفكرة|مفاهيم تصميمية أولية تعكس الهندسة والزخرفة المناسبة.\nالتطوير|تفاصيل الزخارف والخامات والإضاءة مع مشاهد الريندر.\nالتنفيذ|إشراف دقيق على الموقع وتسليم المستندات الكاملة.",
    "testimonials": "فهموا الهوية التي أردتها، وخرجت الزخارف أجمل مما تخيلت.|أحمد الحربي · صاحب فيلا\nالتفاصيل الجبسية والإضاءة غيّرت شكل المجلس تماماً.|نورة السالم · مالكة مساحة تجارية\nالتزام واضح بالجدول الزمني وجودة عالية في التنفيذ.|خالد العتيبي · مطوّر عقاري",
    "showcase_url": "https://example.com",
    "phone": "+966 00 000 0000",
    "email": "hello@axis-studio.com",
    "address": "الرياض، حي العليا",
    "instagram": "https://www.instagram.com/axis.studio_02/",
    "facebook": "#",
    "gallery": [],
}

TEXT_FIELDS = [
    "site_name", "hero_title", "hero_text", "about_text", "about_quote",
    "stats", "categories", "services", "process", "testimonials",
    "showcase_url", "phone", "email", "address", "instagram", "facebook",
]


def load_json(path, default):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_content():
    content = dict(DEFAULT_CONTENT)
    content.update(load_json(CONTENT_FILE, {}))
    return content


def parse_pairs(text):
    """يحوّل كل سطر 'عنوان|نص' إلى زوج (عنوان، نص)."""
    items = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 1)
        items.append((parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""))
    return items


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin"))
        return view(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    c = load_content()
    return render_template(
        "index.html",
        c=c,
        stats=parse_pairs(c["stats"]),
        categories=parse_pairs(c["categories"]),
        services=parse_pairs(c["services"]),
        process=parse_pairs(c["process"]),
        testimonials=parse_pairs(c["testimonials"]),
        sent=request.args.get("sent"),
    )


@app.post("/contact")
def contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    if not name or not email:
        return redirect(url_for("index") + "#contact")

    messages = load_json(MESSAGES_FILE, [])
    messages.append({
        "name": name,
        "email": email,
        "service": request.form.get("service", ""),
        "message": request.form.get("msg", "").strip(),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    save_json(MESSAGES_FILE, messages)
    return redirect(url_for("index", sent=1) + "#contact")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST" and "password" in request.form:
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("كلمة المرور غير صحيحة")
        return redirect(url_for("admin"))

    if not session.get("admin"):
        return render_template("admin.html", logged_in=False)

    return render_template(
        "admin.html",
        logged_in=True,
        c=load_content(),
        messages=list(reversed(load_json(MESSAGES_FILE, []))),
    )


@app.post("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))


@app.post("/admin/save")
@login_required
def admin_save():
    content = load_content()
    for field in TEXT_FIELDS:
        if field in request.form:
            content[field] = request.form[field].strip()
    save_json(CONTENT_FILE, content)
    flash("تم حفظ التعديلات")
    return redirect(url_for("admin"))


@app.post("/admin/gallery/upload")
@login_required
def gallery_upload():
    file = request.files.get("image")
    caption = request.form.get("caption", "").strip() or "عمل من أعمالنا"
    if not file or "." not in file.filename:
        flash("اختر صورة أولاً")
        return redirect(url_for("admin"))

    ext = file.filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXT:
        flash("الصيغ المسموحة: jpg, png, webp")
        return redirect(url_for("admin"))

    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(UPLOAD_DIR / secure_filename(filename))

    content = load_content()
    content["gallery"].append({"file": filename, "caption": caption})
    save_json(CONTENT_FILE, content)
    flash("تمت إضافة الصورة")
    return redirect(url_for("admin"))


@app.post("/admin/gallery/delete/<int:index>")
@login_required
def gallery_delete(index):
    content = load_content()
    if 0 <= index < len(content["gallery"]):
        item = content["gallery"].pop(index)
        (UPLOAD_DIR / item["file"]).unlink(missing_ok=True)
        save_json(CONTENT_FILE, content)
        flash("تم حذف الصورة")
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)