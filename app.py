import streamlit as st
import json
import urllib.parse
import urllib.request
import urllib.error
from supabase import create_client

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="Pocket Eats Perth",
    page_icon="🍜",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =========================================================
# SUPABASE
# =========================================================

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase = get_supabase()


# =========================================================
# DATABASE
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


def menu_items(r):
    menu = r.get("menu_json") or []

    if isinstance(menu, str):
        try:
            menu = json.loads(menu)
        except Exception:
            return []

    return menu if isinstance(menu, list) else []


# =========================================================
# GEOAPIFY
# =========================================================

def search_perth_restaurants(name):
    """
    Search for a named venue/restaurant in the Perth metro area
    using Geoapify Forward Geocoding.
    """

    api_key = st.secrets["GEOAPIFY_KEY"]

    # Free-form search works better for known restaurant/place names.
    search_text = f"{name.strip()}, Perth, Western Australia, Australia"

    params = {
        "text": search_text,

        # Look primarily for named amenities / venues
        "type": "amenity",

        # Perth metro area
        "filter": "rect:115.60,-32.55,116.20,-31.55",

        # Prefer central Perth when several matches exist
        "bias": "proximity:115.8613,-31.9523",

        "limit": "10",
        "lang": "en",
        "format": "json",
        "apiKey": api_key,
    }

    url = (
        "https://api.geoapify.com/v1/geocode/search?"
        + urllib.parse.urlencode(params)
    )

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Pocket-Eats/1.3.1"
        }
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=15
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"Geoapify HTTP error: {e.code}"
        )

    except Exception as e:
        raise RuntimeError(
            f"Restaurant search failed: {e}"
        )

    results = []

    # format=json returns results[] rather than features[]
    for p in data.get("results", []):

        restaurant_name = (
            p.get("name")
            or p.get("address_line1")
            or name.strip()
        )

        address = (
            p.get("formatted")
            or ""
        )

        suburb = (
            p.get("suburb")
            or p.get("district")
            or p.get("city")
            or ""
        )

        postcode = (
            p.get("postcode")
            or ""
        )

        place_id = (
            p.get("place_id")
            or ""
        )

        # Some Geoapify results may contain contact information.
        website = (
            p.get("website")
            or ""
        )

        results.append({
            "name": restaurant_name,
            "address": address,
            "website": website,
            "suburb": suburb,
            "postcode": postcode,
            "place_id": place_id,
        })

    return results




# =========================================================
# STYLE
# =========================================================

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


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <h1>🍜 Pocket Eats</h1>
        <div class="muted">
            Perth · 私人口袋餐廳 · V1.3.1
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

page = st.radio(
    "Navigation",
    [
        "❤️ Pocket",
        "🔎 Search",
        "➕ Add"
    ],
    horizontal=True,
    label_visibility="collapsed"
)


# =========================================================
# SESSION STATE
# =========================================================

if "selected" not in st.session_state:
    st.session_state.selected = None

if "restaurant_results" not in st.session_state:
    st.session_state.restaurant_results = []

if "restaurant_query" not in st.session_state:
    st.session_state.restaurant_query = ""


# =========================================================
# RESTAURANT DETAIL
# =========================================================

def restaurant_detail(r):

    if st.button("← Back / 返回"):
        st.session_state.selected = None
        st.rerun()

    st.header(r["name"])

    tags = [
        t.strip()
        for t in (r.get("tags") or "").split(",")
        if t.strip()
    ]

    if tags:
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

    t1, t2, t3, t4 = st.tabs(
        [
            "📋 Menu",
            "⭐ My notes",
            "✏️ Edit",
            "ℹ️ Info"
        ]
    )

    # MENU
    with t1:

        lang = st.segmented_control(
            "Language",
            ["中英", "中文", "English"],
            default="中英"
        )

        menu = menu_items(r)

        checked = (
            r.get("menu_checked")
            or "—"
        )

        st.caption(
            f"Source: "
            f"{r.get('menu_source') or '—'}"
            f" · Checked: {checked}"
        )

        if not menu:
            st.warning(
                "尚未擷取 Menu。"
                "自動尋找官方 Menu 將在下一階段加入。"
            )

        cats = []

        for x in menu:
            cat = x.get("cat", "Menu")

            if cat not in cats:
                cats.append(cat)

        for cat in cats:

            st.subheader(cat)

            for x in [
                z for z in menu
                if z.get("cat", "Menu") == cat
            ]:

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
                    f"<div class='price'>"
                    f"{x.get('price', '—')}"
                    f"</div>",
                    unsafe_allow_html=True
                )

    # NOTES
    with t2:

        statuses = [
            "Want to go",
            "Been there",
            "Favourite"
        ]

        current_status = (
            r.get("status")
            or "Want to go"
        )

        idx = (
            statuses.index(current_status)
            if current_status in statuses
            else 0
        )

        status = st.selectbox(
            "Status / 狀態",
            statuses,
            index=idx,
            key=f"status_{r['id']}"
        )

        rating = st.slider(
            "My rating / 我的評分",
            0,
            5,
            int(r.get("rating") or 0),
            key=f"rating_{r['id']}"
        )

        notes = st.text_area(
            "Notes / 備註",
            value=r.get("notes") or "",
            key=f"notes_{r['id']}"
        )

        if st.button(
            "Save / 儲存",
            use_container_width=True,
            key=f"save_notes_{r['id']}"
        ):

            supabase.table(
                "restaurants"
            ).update({
                "status": status,
                "rating": rating,
                "notes": notes,
                "favourite":
                    status == "Favourite"
            }).eq(
                "id",
                r["id"]
            ).execute()

            st.success("Saved")
            st.rerun()

    # EDIT
    with t3:

        st.subheader("Edit restaurant")

        edit_name = st.text_input(
            "Restaurant name",
            value=r.get("name") or "",
            key=f"edit_name_{r['id']}"
        )

        edit_address = st.text_input(
            "Address",
            value=r.get("address") or "",
            key=f"edit_address_{r['id']}"
        )

        edit_website = st.text_input(
            "Official website",
            value=r.get("website") or "",
            key=f"edit_website_{r['id']}"
        )

        edit_tags = st.text_input(
            "Tags",
            value=r.get("tags") or "",
            key=f"edit_tags_{r['id']}"
        )

        if st.button(
            "💾 Save changes",
            use_container_width=True,
            key=f"edit_save_{r['id']}"
        ):

            if not edit_name.strip():

                st.error(
                    "Restaurant name cannot be empty."
                )

            else:

                supabase.table(
                    "restaurants"
                ).update({
                    "name": edit_name.strip(),
                    "address": edit_address.strip(),
                    "website": edit_website.strip(),
                    "tags": edit_tags.strip()
                }).eq(
                    "id",
                    r["id"]
                ).execute()

                st.success("Restaurant updated.")
                st.rerun()

        st.divider()

        st.caption(
            "Danger zone / 刪除後無法復原"
        )

        confirm_delete = st.checkbox(
            "I understand. / 我確定要刪除",
            key=f"delete_confirm_{r['id']}"
        )

        if st.button(
            "🗑 Delete restaurant",
            type="secondary",
            use_container_width=True,
            disabled=not confirm_delete,
            key=f"delete_{r['id']}"
        ):

            supabase.table(
                "restaurants"
            ).delete().eq(
                "id",
                r["id"]
            ).execute()

            st.session_state.selected = None

            st.success("Restaurant deleted.")
            st.rerun()

    # INFO
    with t4:

        st.write("**Address**")
        st.write(
            r.get("address") or "—"
        )

        st.write("**Tags**")
        st.write(
            r.get("tags") or "—"
        )

        st.write("**Menu source**")
        st.write(
            r.get("menu_source") or "—"
        )

        st.write("**Last checked**")
        st.write(
            r.get("menu_checked") or "—"
        )


# =========================================================
# LOAD DATA
# =========================================================

try:
    rows = get_rows()

except Exception as e:

    st.error(
        "Pocket Eats 無法連接 Supabase。"
    )

    st.code(str(e))
    st.stop()


# =========================================================
# SELECTED RESTAURANT
# =========================================================

if st.session_state.selected:

    r = next(
        (
            x for x in rows
            if x["id"]
            == st.session_state.selected
        ),
        None
    )

    if r:
        restaurant_detail(r)


# =========================================================
# POCKET / SEARCH
# =========================================================

elif page in [
    "❤️ Pocket",
    "🔎 Search"
]:

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

        menu = menu_items(r)

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

            caption = (
                r.get("status")
                or "Want to go"
            )

            if r.get("rating"):
                caption += (
                    " · "
                    + "★"
                    * int(r["rating"])
                )

            st.caption(caption)

            tags = [
                t.strip()
                for t in (
                    r.get("tags") or ""
                ).split(",")
                if t.strip()
            ]

            if tags:
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
                key=f"open_{r['id']}",
                use_container_width=True
            ):

                st.session_state.selected = r["id"]
                st.rerun()

    if not shown:
        st.info(
            "沒有符合的口袋餐廳。"
        )


# =========================================================
# ADD / SEARCH PERTH
# =========================================================

elif page == "➕ Add":

    st.subheader(
        "➕ Find a restaurant"
    )

    st.caption(
        "輸入餐廳名稱，Pocket Eats "
        "會搜尋 Perth 的真實餐廳。"
    )

    search_name = st.text_input(
        "Restaurant name",
        placeholder="例如 Nobu"
    )

    if st.button(
        "🔎 Search Perth",
        use_container_width=True
    ):

        if not search_name.strip():

            st.warning(
                "請先輸入餐廳名稱。"
            )

        else:

            with st.spinner(
                "Searching Perth restaurants..."
            ):

                try:

                    results = (
                        search_perth_restaurants(
                            search_name
                        )
                    )

                    st.session_state.restaurant_results = (
                        results
                    )

                    st.session_state.restaurant_query = (
                        search_name
                    )

                except Exception as e:

                    st.session_state.restaurant_results = []

                    st.error(
                        "Geoapify 搜尋失敗。"
                    )

                    st.code(str(e))

    results = (
        st.session_state.restaurant_results
    )

    if results:

        st.success(
            f"找到 {len(results)} 個結果"
        )

        for i, item in enumerate(results):

            with st.container(border=True):

                st.subheader(
                    item["name"]
                )

                if item["address"]:
                    st.write(
                        "📍 " + item["address"]
                    )

                if item["suburb"]:
                    st.caption(
                        item["suburb"]
                    )

                if item["website"]:
                    st.write(
                        "🌐 Official website found"
                    )

                if st.button(
                    "＋ Add this restaurant",
                    key=f"add_result_{i}",
                    use_container_width=True
                ):

                    # Prevent simple duplicate
                    duplicate = next(
                        (
                            x for x in rows
                            if (
                                x.get("name", "")
                                .strip()
                                .lower()
                                ==
                                item["name"]
                                .strip()
                                .lower()
                            )
                            and (
                                x.get("address", "")
                                .strip()
                                .lower()
                                ==
                                item["address"]
                                .strip()
                                .lower()
                            )
                        ),
                        None
                    )

                    if duplicate:

                        st.warning(
                            "這間餐廳已經在 Pocket 裡。"
                        )

                    else:

                        result = (
                            supabase
                            .table("restaurants")
                            .insert({
                                "name":
                                    item["name"],

                                "address":
                                    item["address"],

                                "website":
                                    item["website"],

                                "tags":
                                    "Restaurant",

                                "menu_source":
                                    "Not checked yet / 尚未檢查",

                                "menu_json":
                                    [],

                                "status":
                                    "Want to go",

                                "favourite":
                                    False,

                                "rating":
                                    0,

                                "notes":
                                    ""
                            })
                            .execute()
                        )

                        if result.data:

                            st.session_state.selected = (
                                result.data[0]["id"]
                            )

                            st.session_state.restaurant_results = []

                            st.rerun()

    elif st.session_state.restaurant_query:

        st.info(
            "沒有找到符合的 Perth 餐廳。"
        )

    st.divider()

    with st.expander(
        "Can't find it? / 找不到餐廳？手動新增"
    ):

        with st.form(
            "manual_add"
        ):

            manual_name = st.text_input(
                "Restaurant name *"
            )

            manual_address = st.text_input(
                "Address"
            )

            manual_website = st.text_input(
                "Official website"
            )

            manual_tags = st.text_input(
                "Tags"
            )

            manual_status = st.selectbox(
                "Status",
                [
                    "Want to go",
                    "Been there",
                    "Favourite"
                ]
            )

            manual_ok = (
                st.form_submit_button(
                    "＋ Add manually",
                    use_container_width=True
                )
            )

            if manual_ok:

                if not manual_name.strip():

                    st.error(
                        "請輸入餐廳名稱。"
                    )

                else:

                    result = (
                        supabase
                        .table("restaurants")
                        .insert({
                            "name":
                                manual_name.strip(),

                            "address":
                                manual_address.strip(),

                            "website":
                                manual_website.strip(),

                            "tags":
                                manual_tags.strip(),

                            "menu_source":
                                "Not checked yet / 尚未檢查",

                            "menu_json":
                                [],

                            "status":
                                manual_status,

                            "favourite":
                                manual_status
                                == "Favourite",

                            "rating":
                                0,

                            "notes":
                                ""
                        })
                        .execute()
                    )

                    if result.data:

                        st.session_state.selected = (
                            result.data[0]["id"]
                        )

                        st.rerun()
