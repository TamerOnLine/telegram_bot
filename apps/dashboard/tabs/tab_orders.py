from __future__ import annotations

import streamlit as st
from pathlib import Path
import sys

# === ضمان الوصول لموديول shop_bot/db.py ===
ROOT = Path(__file__).resolve().parents[3]
SHOP_BOT_DIR = ROOT / "apps" / "shop_bot"
if str(SHOP_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(SHOP_BOT_DIR))

try:
    from db import list_orders
except Exception:
    list_orders = None


def render_tab() -> None:
    st.subheader("📦 طلبات المتجر (Shop Orders)")

    if list_orders is None:
        st.error("تعذّر استيراد shop_bot.db — تأكد من وجود الملف.")
        return

    with st.spinner("جاري جلب الطلبات من قاعدة البيانات..."):
        try:
            rows = list_orders()
        except Exception as exc:
            st.error(f"حدث خطأ أثناء استعلام قاعدة البيانات:\n\n{exc}")
            return

    if not rows:
        st.info("لا يوجد أي طلبات مسجّلة حتى الآن.")
        return

    # تنسيق بسيط للعرض
    for row in rows:
        with st.container():
            st.markdown(
                f"""
### 🧾 Order #{row['id']}
**User:** {row['full_name']} (@{row['username']})  
**User ID:** `{row['user_id']}`  
**Total:** **{row['total']:.2f}€**  
**Date:** {row['created_at']}

**Details:**  
```text
{row['details']}
            """,
        )
        st.divider()


