# ChangeFlow

سامانهٔ مدیریت درخواست تغییر (Change Request) — نسخهٔ اول، به‌صورت HTTP API.
این پروژه با روش Spec-Driven Development و ابزار Spec Kit به‌همراه یک Coding Agent ساخته شده است.

**دانشجو:** Vahid Nazari Tavakoli
**Repository:** https://github.com/vahidnazaritavakolii/changeFlow

---

## ۱. وضعیت واقعی پروژه

| مورد | وضعیت |
|---|---|
| Taskها | ۴۶ Task؛ ۴۴ Task اولیه + T045 و T046 که Converge اضافه کرد |
| Build و Test | `pytest -q` ← **231 passed, 1 warning** در ۴٫۹۳ ثانیه (اجرا توسط دانشجو، 2026-11-17) |
| Analyze | انجام شد؛ ۱۲ Finding + ۳ یافتهٔ بازبینی انسانی، همه با تصمیم مکتوب |
| Converge | <!-- TODO(Vahid): تعداد دورها و نتیجهٔ دور آخر را بنویس، مثلاً «۳ دور؛ دور سوم بدون شکاف» یا «دور سوم یک شکاف باز: T047» --> |
| پذیرش انسانی | **ارزیابی نشده است.** هیچ معیار پذیرشی توسط فردی غیر از دانشجو بررسی نشده |

طبق Constitution پروژه، Feature در وضعیت «پیاده‌سازی‌شده» است، نه «کامل و پذیرفته‌شده».

## ۲. Stack

- Python 3.12
- FastAPI و uvicorn
- SQLite از طریق ماژول استاندارد `sqlite3` (بدون ORM)
- pytest و httpx برای آزمون

دلیل هر انتخاب در [`research.md`](specs/001-change-request-workflow/research.md) آمده است.

## ۳. پیش‌نیازها و روش اجرا

<!-- TODO(Vahid): این فرمان‌ها را با specs/001-change-request-workflow/quickstart.md تطبیق بده و اگر تفاوتی هست اصلاح کن. -->

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# ساخت کاربران آزمایشی و دریافت Token
python -m changeflow.infrastructure.seed --db changeflow.db alice=requester bob=reviewer

# اجرای سرور
CHANGEFLOW_DB=changeflow.db uvicorn changeflow.api.app:create_app --factory

# اجرای آزمون‌ها
pytest -q
```

راهنمای کامل به‌همراه سناریوهای نمونه: [`quickstart.md`](specs/001-change-request-workflow/quickstart.md)

## ۴. API

همهٔ Endpointها به هدر `Authorization: Bearer <token>` نیاز دارند.

| Method | Path | کاربرد |
|---|---|---|
| POST | `/change-requests` | ایجاد درخواست در وضعیت Draft |
| GET | `/change-requests` | فهرست درخواست‌های قابل مشاهده |
| GET | `/change-requests/{id}` | مشاهدهٔ یک درخواست |
| PUT | `/change-requests/{id}` | ویرایش (فقط Draft و ChangesRequested) |
| POST | `/change-requests/{id}/submit` | ارسال برای بررسی |
| POST | `/change-requests/{id}/approve` | تأیید |
| POST | `/change-requests/{id}/request-changes` | برگشت برای اصلاح |

هر عملیات تغییردهنده باید `version` فعلی درخواست را در بدنه ارسال کند.

| نتیجه | HTTP | `code` |
|---|---|---|
| احراز هویت نشده | 401 | `unauthenticated` |
| پیدا نشد یا قابل مشاهده نیست | 404 | `not_found` |
| غیرمجاز | 403 | `forbidden` |
| ورودی نامعتبر | 400 | `invalid_input` |
| Version قدیمی | 409 | `conflict` |
| وضعیت نامعتبر | 422 | `invalid_status` |

قرارداد کامل: [`contracts/http-api.md`](specs/001-change-request-workflow/contracts/http-api.md)

## ۵. تصمیم‌های اصلی معماری

1. **جداسازی مسئولیت‌ها.** قواعد کسب‌وکار (گردش وضعیت، منع Self-Review، دید، اعتبارسنجی، ترتیب بررسی‌ها) در Package `domain` با Python خالص قرار دارند. `application` فقط هماهنگ می‌کند (احراز هویت ← بارگذاری ← Domain ← ذخیره) و Handlerهای `api` فقط درخواست را می‌خوانند، یک Use Case را صدا می‌زنند و نتیجه را به HTTP نگاشت می‌کنند.
2. **اعمال خودکار قاعدهٔ معماری.** `tests/architecture/test_architecture.py` با ماژول `ast` بررسی می‌کند که Domain به HTTP یا Persistence وابسته نباشد و Handlerها هیچ شرطی نداشته باشند. این Test یک Self-test هم دارد تا به‌صورت توخالی سبز نشود.
3. **Concurrency با Optimistic Locking.** ستون `version` و یک `UPDATE ... WHERE id = ? AND version = ?`. اگر Version قدیمی باشد، هیچ ردیفی تغییر نمی‌کند و پاسخ `409` است.
4. **احراز هویت با Bearer Token ساده.** فقط Hash توکن ذخیره می‌شود و نقش‌ها در هر عملیات از دیتابیس خوانده می‌شوند تا «مجوز فعلی» بررسی شود. JWT رد شد چون نقشِ داخل Token تا زمان انقضا کهنه می‌ماند.
5. **تغییرناپذیری درخواست Approved** از طریق گردش وضعیت در Domain به‌همراه بررسی Version. Content Hash و Snapshot بررسی و برای این نسخه رد شدند.
6. **اعتبارسنجی ورودی در Domain، نه با Pydantic در Handler**، تا ترتیب بررسی‌ها حفظ شود (هویت و مجوز قبل از اعتبار ورودی). هزینه: Schema ورودی به‌صورت خودکار تولید نمی‌شود.
7. **سادگی.** ORM، DI Container، Unit of Work و لایهٔ DTO صریحاً رد شده‌اند (Research، بخش R8).

## ۶. تصمیم‌های محصولی (Clarify)

- مالک همیشه درخواست خودش را می‌بیند؛ کسی که حق دیدن ندارد پاسخ `404` می‌گیرد.
- Self-Review به‌طور کامل ممنوع است: نه تأیید و نه برگشت برای اصلاحِ درخواستِ خود.
- حذف، رد نهایی و لغو در این نسخه وجود ندارد.
- ویرایش در وضعیت PendingReview ممنوع است.
- معیار کارایی (۵۰ کاربر هم‌زمان) که Agent پیشنهاد داده بود حذف شد، چون خارج از Scope و بدون امکان اثبات بود.

جزئیات و فرض‌های باز (A6، A7 و PA-1 تا PA-7) در `spec.md` و `plan.md` ثبت شده‌اند.

## ۷. محدودیت‌های شناخته‌شده

- **آزمون هم‌زمانی شبیه‌سازی‌شده است.** سناریوی «دو Reviewer هم‌زمان» با دو درخواست پشت سر هم روی یک Version آزموده می‌شود، نه با اجرای واقعاً موازی.
- **Tokenها** انقضا، چرخش و ابطال ندارند و با یک فرمان Seed ساخته می‌شوند. مدیریت کاربر و نقش خارج از Scope است.
- **پنجرهٔ زمانی لغو نقش:** اگر نقش کاربر در فاصلهٔ چند میلی‌ثانیه‌ای بین خواندن نقش و نوشتن حذف شود، عملیات انجام می‌شود.
- **SQLite** در هر لحظه یک نویسنده دارد و برای چند نمونهٔ هم‌زمان از برنامه مناسب نیست. مسیر مهاجرت به PostgreSQL در Research (R1) آمده است.
- **Deprecation Warning:** Starlette اعلام می‌کند استفاده از `httpx` در `TestClient` منسوخ شده است. روی نتیجهٔ آزمون‌ها اثری ندارد و جایگزین آن بررسی نشده است.
- **صفحات مستندات خودکار FastAPI غیرفعال‌اند** (نتیجهٔ T045)، بنابراین مرجع API فایل Contract است.
- حد طول فیلدها (A6) و سازوکار هویت (A7) هنوز فرض قابل بازبینی‌اند، نه تصمیم تأییدشده.
- تاریخچهٔ تغییرات (Audit) وجود ندارد؛ فقط آخرین دلیل برگشت نگه داشته می‌شود.
- خروجی Converge قضاوت یک مدل است، نه اثبات؛ نبودِ شکاف در یک دور به معنی نبودِ قطعی شکاف نیست.

## ۸. نقش Coding Agent و بازبینی انسانی

Coding Agent مورد استفاده: <!-- TODO(Vahid): نام و نسخهٔ Agent را بنویس -->

Agent همهٔ Artifactها و کد را از طریق فرمان‌های Spec Kit تولید کرد. متن ورودی هر فرمان و تصمیم‌های محصولی و معماری توسط دانشجو تعیین و خروجی هر مرحله پیش از Commit بازبینی شد. در این بازبینی از یک دستیار هوش مصنوعی نیز به‌عنوان بازبین کمک گرفته شد.

مواردی که بازبینی انسانی خروجی Agent را تغییر داد:

| مرحله | کاری که Agent کرد | اصلاح |
|---|---|---|
| Constitution | چهار لایه و مفهوم Port را به‌عنوان الزام دائمی اضافه کرد | حذف شد؛ ساختار مشخص به Plan منتقل شد |
| Constitution | «کامل» را برابر با Build و Test موفق تعریف کرد | به «پیاده‌سازی‌شده» در برابر «کامل» (با Converge و پذیرش انسانی) تفکیک شد |
| Specify | یک معیار کارایی بدون منبع اضافه کرد | در Clarify حذف شد |
| Plan | ارجاع دوپهلو به `SC-006` و ادعای نادرست دربارهٔ Principle I | Analyze این دو را پیدا نکرد؛ به‌عنوان یافتهٔ انسانی H1 و H2 ثبت و اصلاح شد |

مواردی که ابزار پیدا کرد و آزمون‌ها نگرفته بودند:

| منبع | یافته | نتیجه |
|---|---|---|
| Analyze | دو تناقض HIGH در Spec دربارهٔ دید و نوع خطا، با وجود پوشش ۱۰۰٪ | اصلاح پیش از Implement |
| Converge دور ۱ | صفحات مستندات FastAPI بدون احراز هویت در دسترس بودند، در حالی که ۲۱۷ آزمون سبز بود | T045؛ اصلاح شد (۲۲۵ آزمون) |
| Converge دور ۲ | رفتار نادرست برای شناسهٔ بسیار بزرگ | T046؛ اصلاح شد (۲۳۱ آزمون) |

## ۹. فهرست Artifactها

| Artifact | مسیر |
|---|---|
| Constitution | `.specify/memory/constitution.md` |
| Specification و Clarifications | `specs/001-change-request-workflow/spec.md` |
| Plan | `specs/001-change-request-workflow/plan.md` |
| Research | `specs/001-change-request-workflow/research.md` |
| Data Model | `specs/001-change-request-workflow/data-model.md` |
| API Contract | `specs/001-change-request-workflow/contracts/http-api.md` |
| Tasks | `specs/001-change-request-workflow/tasks.md` |
| گزارش Analyze و تصمیم‌ها | `specs/001-change-request-workflow/analysis.md` |
| گزارش واقعی Test | `specs/001-change-request-workflow/test-results.md` |
| نتیجهٔ اجرای Quickstart | `specs/001-change-request-workflow/quickstart-results.md` |
| جدول ردیابی | `specs/001-change-request-workflow/traceability.md` |
| گزارش Converge | `specs/001-change-request-workflow/converge-report.md` |
| پاسخ سؤالات مفهومی | `docs/answers/session-01.md` |
