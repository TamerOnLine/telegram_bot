from __future__ import annotations


def index_html() -> str:
    return """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>ربط حساب Gmail</title>
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f172a;
      color: #e5e7eb;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }
    .card {
      background: #020617;
      border-radius: 1rem;
      padding: 2rem 2.5rem;
      box-shadow: 0 20px 40px rgba(15, 23, 42, 0.7);
      max-width: 480px;
      width: 100%;
      text-align: center;
    }
    h1 {
      margin-top: 0;
      margin-bottom: 1rem;
      font-size: 1.4rem;
    }
    p {
      margin-bottom: 1.4rem;
      line-height: 1.7;
      color: #cbd5f5;
    }
    .note {
      font-size: 0.9rem;
      color: #94a3b8;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>خادم ربط Gmail</h1>
    <p>هذا الخادم مخصص لربط حسابات Gmail مع بوت التليجرام فقط.</p>
    <p class="note">يُفضّل أن تصل إلى هذا الرابط من خلال البوت وليس مباشرة.</p>
  </div>
</body>
</html>
    """


def success_html() -> str:
    return """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>تم الربط بنجاح</title>
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f172a;
      color: #e5e7eb;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }
    .card {
      background: #020617;
      border-radius: 1rem;
      padding: 2rem 2.5rem;
      box-shadow: 0 20px 40px rgba(15, 23, 42, 0.7);
      max-width: 480px;
      width: 100%;
      text-align: center;
    }
    h1 {
      margin-top: 0;
      margin-bottom: 1rem;
      font-size: 1.4rem;
    }
    p {
      margin-bottom: 1.4rem;
      line-height: 1.7;
      color: #cbd5f5;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>تم ربط حساب Gmail بنجاح ✅</h1>
    <p>يمكنك الآن إغلاق هذه الصفحة والعودة إلى بوت التليجرام.</p>
  </div>
</body>
</html>
    """


def error_html(message: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>خطأ في الربط</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f172a;
      color: #e5e7eb;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }}
    .card {{
      background: #020617;
      border-radius: 1rem;
      padding: 2rem 2.5rem;
      box-shadow: 0 20px 40px rgba(15, 23, 42, 0.7);
      max-width: 480px;
      width: 100%;
      text-align: center;
    }}
    h1 {{
      margin-top: 0;
      margin-bottom: 1rem;
      font-size: 1.4rem;
      color: #fecaca;
    }}
    p {{
      margin-bottom: 1.4rem;
      line-height: 1.7;
      color: #fecaca;
    }}
  </style>
</head>
<body>
  <div class="card">
    <h1>حدث خطأ أثناء الربط ❌</h1>
    <p>{message}</p>
  </div>
</body>
</html>
    """
