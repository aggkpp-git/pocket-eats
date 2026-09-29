import streamlit as st
import json
import urllib.parse
from datetime import date
from supabase import create_client

# =========================================================
# Supabase
# =========================================================

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase = get_supabase()


# =========================================================
# Database helpers
# =========================================================

def get_rows():
    result = (
        supabase
        .table("restaurants")
        .select("*")
        .order("favourite", desc=True)
        .order("id", desc=True)
        .execute()
    )
    return result.data or []


def seed():
    result = (
        supabase
        .table("restaurants")
        .select("id")
        .limit(1)
        .execute()
    )

    if result.data:
        return

    menu = [
        {
            "cat": "Featured / 精選",
            "en": "Katsu Chicken Curry Don",
            "zh": "炸雞咖哩丼",
            "price": "$26"
        },
        {
            "cat": "Featured / 精選",
            "en": "Nabeyaki Udon",
            "zh": "鍋燒烏龍麵",
            "price": "$30"
        },
        {
            "cat": "Featured / 精選",
            "en": "Mentaiko Caviar Udon",
            "zh": "明太子魚子醬烏龍麵",
            "price": "$29"
        },
        {
            "cat": "Sashimi / 刺身",
            "en": "Salmon Carpaccio",
            "zh": "鮭魚薄切",
            "price": "$26.90"
        },
        {
            "cat": "Sashimi / 刺身",
            "en": "Kingfish Carpaccio",
            "zh": "鰤魚薄切",
            "price": "$28.90"
        },
    ]

    supabase.table("restaurants").insert({
        "name": "Akari-ya Izakaya",
        "address": "2/800 Albany Hwy, East Victoria Park WA 6101",
        "website": "https://www.akariya.com.au/",
        "tags": "Japanese, Izakaya, $$",
        "price_level": "$$",
        "menu_source": "Official website / 官方網站",
        "menu_url": "https://www.akariya.com.au/",
        "menu_json": menu,
        "menu_checked": "2026-09-29",
        "status": "Want to go",
        "favourite": False,
        "rating": 0,
        "notes": ""
    }).execute()


seed()


# =========================================================
# Page
# =========================================================

st.set_page_config(
    page_title="Pocket Eats Perth",
    page_icon="🍜",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
    .block-container{
        max-width:760px;
        padding-top:1rem;
        padding-bottom:5rem;
    }

    .stButton button,
    .stLinkButton a{
        min-height:46px;
    }

    .hero{
        padding:12px 2px 4px;
    }

    .hero h1{
        font-size:2rem;
        margin:0;
    }

    .muted{
        color:#777;
        font-size:.84rem;
    }

    .price{
        font-size:1.05rem;
        font-weight:750;
        text-align:right;
    }

    .pill{
        display:inline-block;
        padding:4px 9px;
        border-radius:16px;
        background:rgba(127,127,127,.12);
        margin:2px;
        font-size:.82rem;
    }

    .menuitem{
        padding:8px 0;
        border-bottom:1px solid rgba(127,127,127,.18);
    }

    [data-testid="stRadio"] > div{
        gap:.25rem;
    }

    [data-testid="stRadio"] label{
        padding:.35rem .5rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="hero">
        <h1>🍜 Pocket Eats</h1>
        <div class="muted">Perth · 私人口袋餐廳</div>
    </div>
    """,
    unsafe_allow_html=True
)

page = st.radio(
    "Navigation",
    ["❤️ Pocket", "🔎 Search", "➕ Add"],
    horizontal=True,
    label_visibility="collapsed"
)

if "selected" not in st.session_state:
    st.session_state.selected = None


# =========================================================
# Restaurant detail
# =========================================================

def restaurant_detail(r):

    if st.button("← Back / 返回", use_container_width=False):
        st.session_state.selected = None
        st.rerun()

    st.header(r["name"])

    tags = [
        t.strip()
        for t in (r.get("tags") or "").split(",")
        if t.strip()
    ]

    st.markdown(
        "".join(
            f'<span class="pill">{t}</span>'
            for t in tags
        ),
        unsafe_allow_html=True
    )

    st.write(
        "📍 " + (r.get("address") or "Address not added")
    )

    maps = (
        "https://www.google.com/maps/search/?api=1&query="
        + urllib.parse.quote(
            r.get("address") or r["name"]
        )
    )

    a, b = st.columns(2)

    a.link_button(
        "🧭 Navigate",
        maps,
        use_container_width=True
    )

    if r.get("website"):
        b.link_button(
            "🌐 Official",
            r["website"],
            use_container_width=True
        )

    st.divider()

    t1, t2, t3 = st.tabs(
        ["📋 Menu", "⭐ My notes", "ℹ️ Info"]
    )

    # -----------------------------------------------------
    # MENU
    # -----------------------------------------------------

    with t1:

        lang = st.segmented_control(
            "Language",
            ["中英", "中文", "English"],
            default="中英"
        )

        menu = r.get("menu_json") or []

        # Compatibility in case JSON comes back as text
        if isinstance(menu, str):
            try:
                menu = json.loads(menu)
            except Exception:
                menu = []

        checked = r.get("menu_checked") or "—"

        st.caption(
            f"Source: {r.get('menu_source') or '—'}"
            f" · Checked: {checked}"
        )

        if not menu:
            st.warning(
                "尚未擷取 Menu。自動擷取功能會在下一階段接上。"
            )

        cats = []

        for x in menu:
            cat = x.get("cat", "Menu")

            if cat not in cats:
                cats.append(cat)

        for cat in cats:

            st.subheader(cat)

            items = [
                z for z in menu
                if z.get("cat", "Menu") == cat
            ]

            for x in items:

                c1, c2 = st.columns([4, 1])

                en = x.get("en", "")
                zh = x.get("zh", "")

                if lang == "中文":
                    label = zh or en

                elif lang == "English":
                    label = en or zh

                else:
                    if zh:
                        label = f"**{en}**  \n{zh}"
                    else:
                        label = f"**{en}**"

                c1.markdown(label)

                c2.markdown(
                    f"""
                    <div class='price'>
                    {x.get('price', '—')}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # -----------------------------------------------------
    # NOTES
    # -----------------------------------------------------

    with t2:

        statuses = [
            "Want to go",
            "Been there",
            "Favourite"
        ]

        current_status = r.get("status") or "Want to go"

        idx = (
            statuses.index(current_status)
            if current_status in statuses
            else 0
        )

        status = st.selectbox(
            "Status / 狀態",
            statuses,
            index=idx
        )

        rating = st.slider(
            "My rating / 我的評分",
            0,
            5,
            int(r.get("rating") or 0)
        )

        notes = st.text_area(
            "Notes / 備註",
            value=r.get("notes") or "",
            placeholder="例如：下次想試 Omakase、停車方便…"
        )

        if st.button(
            "Save / 儲存",
            use_container_width=True
        ):

            supabase.table("restaurants").update({
                "status": status,
                "rating": rating,
                "notes": notes,
                "favourite": status == "Favourite",
                "updated_at": "now()"
            }).eq(
                "id",
                r["id"]
            ).execute()

            st.success("Saved")
            st.rerun()

    # -----------------------------------------------------
    # INFO
    # -----------------------------------------------------

    with t3:

        st.write("**Address**")
        st.write(r.get("address") or "—")

        st.write("**Tags**")
        st.write(r.get("tags") or "—")

        st.write("**Menu source**")
        st.write(r.get("menu_source") or "—")

        st.write("**Last checked**")
        st.write(r.get("menu_checked") or "—")


# =========================================================
# Load restaurants
# =========================================================

try:
    rows = get_rows()

except Exception as e:

    st.error(
        "Pocket Eats 無法連接 Supabase 資料庫。"
    )

    st.code(str(e))

    st.stop()


# =========================================================
# Selected restaurant
# =========================================================

if st.session_state.selected:

    r = next(
        (
            x for x in rows
            if x["id"] == st.session_state.selected
        ),
        None
    )

    if r:
        restaurant_detail(r)


# =========================================================
# Pocket / Search
# =========================================================

elif page in ["❤️ Pocket", "🔎 Search"]:

    q = ""

    if page == "🔎 Search":

        q = st.text_input(
            "Search",
            placeholder=(
                "Japanese · Wagyu · "
                "Victoria Park · 刺身"
            )
        )

    filt = st.segmented_control(
        "Filter",
        [
            "All",
            "Want to go",
            "Been there",
            "Favourite"
        ],
        default="All",
        label_visibility="collapsed"
    )

    shown = 0

    for r in rows:

        menu = r.get("menu_json") or []

        if isinstance(menu, str):
            try:
                menu = json.loads(menu)
            except Exception:
                menu = []

        hay = " ".join(
            [
                r.get("name") or "",
                r.get("address") or "",
                r.get("tags") or "",
                r.get("status") or ""
            ]
            +
            [
                (
                    z.get("en", "")
                    + " "
                    + z.get("zh", "")
                )
                for z in menu
            ]
        ).lower()

        if q and q.lower() not in hay:
            continue

        if (
            filt != "All"
            and r.get("status") != filt
        ):
            continue

        shown += 1

        with st.container(border=True):

            st.subheader(r["name"])

            caption = r.get("status") or "Want to go"

            if r.get("rating"):
                caption += (
                    " · "
                    + "★" * int(r["rating"])
                )

            st.caption(caption)

            tags = [
                t.strip()
                for t in (r.get("tags") or "").split(",")
                if t.strip()
            ]

            st.markdown(
                "".join(
                    f'<span class="pill">{t}</span>'
                    for t in tags
                ),
                unsafe_allow_html=True
            )

            st.write(
                "📍 "
                + (
                    r.get("address")
                    or "Address not added"
                )
            )

            if st.button(
                "Open restaurant / 查看餐廳",
                key=f"open{r['id']}",
                use_container_width=True
            ):

                st.session_state.selected = r["id"]
                st.rerun()

    if not shown:
        st.info("沒有符合的口袋餐廳。")


# =========================================================
# Add restaurant
# =========================================================

elif page == "➕ Add":

    st.subheader("➕ Add restaurant")

    st.caption(
        "V1.2 已使用永久雲端資料庫。"
        "下一階段會把這裡改成「只輸入名稱，"
        "自動找官方資料與 Menu」。"
    )

    with st.form("add"):

        name = st.text_input(
            "Restaurant name *",
            placeholder="例如 Nobu Perth"
        )

        address = st.text_input(
            "Address"
        )

        website = st.text_input(
            "Official website"
        )

        tags = st.text_input(
            "Tags",
            placeholder=(
                "Japanese, High-end, Date night"
            )
        )

        status = st.selectbox(
            "Status",
            [
                "Want to go",
                "Been there",
                "Favourite"
            ]
        )

        ok = st.form_submit_button(
            "＋ Add to Pocket",
            use_container_width=True
        )

        if ok:

            if not name.strip():

                st.error(
                    "請輸入餐廳名稱。"
                )

            else:

                result = (
                    supabase
                    .table("restaurants")
                    .insert({
                        "name": name.strip(),
                        "address": address.strip(),
                        "website": website.strip(),
                        "tags": tags.strip(),
                        "menu_source":
                            "Not checked yet / 尚未檢查",
                        "menu_json": [],
                        "status": status,
                        "favourite":
                            status == "Favourite",
                        "rating": 0,
                        "notes": ""
                    })
                    .execute()
                )

                if result.data:

                    st.session_state.selected = (
                        result.data[0]["id"]
                    )

                    st.rerun()

                else:

                    st.error(
                        "餐廳沒有成功加入，請再試一次。"
                    )
