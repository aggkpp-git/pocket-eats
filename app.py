import streamlit as st
import sqlite3, json, urllib.parse
from pathlib import Path
from datetime import date

DB = Path(__file__).with_name('restaurants.db')

def conn():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    c.execute('''CREATE TABLE IF NOT EXISTS restaurants(
      id INTEGER PRIMARY KEY, name TEXT NOT NULL, address TEXT, website TEXT,
      tags TEXT, menu_source TEXT, checked TEXT, menu_json TEXT,
      favourite INTEGER DEFAULT 1, status TEXT DEFAULT 'Want to go',
      rating INTEGER DEFAULT 0, notes TEXT DEFAULT ''
    )''')
    cols={x[1] for x in c.execute('pragma table_info(restaurants)').fetchall()}
    for col, sql in [('status',"TEXT DEFAULT 'Want to go'"),('rating','INTEGER DEFAULT 0'),('notes',"TEXT DEFAULT ''")]:
        if col not in cols: c.execute(f'ALTER TABLE restaurants ADD COLUMN {col} {sql}')
    c.commit(); return c

def seed():
    c=conn()
    if c.execute('select count(*) from restaurants').fetchone()[0]==0:
        menu=[
          {'cat':'Featured / 精選','en':'Katsu Chicken Curry Don','zh':'炸雞咖哩丼','price':'$26'},
          {'cat':'Featured / 精選','en':'Nabeyaki Udon','zh':'鍋燒烏龍麵','price':'$30'},
          {'cat':'Featured / 精選','en':'Mentaiko Caviar Udon','zh':'明太子魚子醬烏龍麵','price':'$29'},
          {'cat':'Sashimi / 刺身','en':'Salmon Carpaccio','zh':'鮭魚薄切','price':'$26.90'},
          {'cat':'Sashimi / 刺身','en':'Kingfish Carpaccio','zh':'鰤魚薄切','price':'$28.90'},
        ]
        c.execute('''insert into restaurants(name,address,website,tags,menu_source,checked,menu_json,status)
          values(?,?,?,?,?,?,?,?)''',('Akari-ya Izakaya','2/800 Albany Hwy, East Victoria Park WA 6101','https://www.akariya.com.au/','Japanese, Izakaya, $$','Official website / 官方網站','29 Sep 2026',json.dumps(menu),'Want to go'))
        c.commit()
    c.close()
seed()

st.set_page_config(page_title='Pocket Eats Perth', page_icon='🍜', layout='centered', initial_sidebar_state='collapsed')
st.markdown('''<style>
.block-container{max-width:760px;padding-top:1rem;padding-bottom:5rem}.stButton button,.stLinkButton a{min-height:46px}
.hero{padding:12px 2px 4px}.hero h1{font-size:2rem;margin:0}.muted{color:#777;font-size:.84rem}.price{font-size:1.05rem;font-weight:750;text-align:right}
.pill{display:inline-block;padding:4px 9px;border-radius:16px;background:rgba(127,127,127,.12);margin:2px;font-size:.82rem}
.menuitem{padding:8px 0;border-bottom:1px solid rgba(127,127,127,.18)}
[data-testid="stRadio"] > div{gap:.25rem}[data-testid="stRadio"] label{padding:.35rem .5rem}
</style>''', unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🍜 Pocket Eats</h1><div class="muted">Perth · 私人口袋餐廳</div></div>', unsafe_allow_html=True)
page=st.radio('Navigation',['❤️ Pocket','🔎 Search','➕ Add'],horizontal=True,label_visibility='collapsed')

if 'selected' not in st.session_state: st.session_state.selected=None

def get_rows():
    c=conn(); rows=c.execute('select * from restaurants order by favourite desc,id desc').fetchall(); c.close(); return rows

def restaurant_detail(r):
    if st.button('← Back / 返回',use_container_width=False): st.session_state.selected=None; st.rerun()
    st.header(r['name'])
    tags=[t.strip() for t in (r['tags'] or '').split(',') if t.strip()]
    st.markdown(''.join(f'<span class="pill">{t}</span>' for t in tags),unsafe_allow_html=True)
    st.write('📍 '+(r['address'] or 'Address not added'))
    maps='https://www.google.com/maps/search/?api=1&query='+urllib.parse.quote(r['address'] or r['name'])
    a,b=st.columns(2); a.link_button('🧭 Navigate',maps,use_container_width=True)
    if r['website']: b.link_button('🌐 Official',r['website'],use_container_width=True)
    st.divider()
    t1,t2,t3=st.tabs(['📋 Menu','⭐ My notes','ℹ️ Info'])
    with t1:
        lang=st.segmented_control('Language',['中英','中文','English'],default='中英')
        menu=json.loads(r['menu_json'] or '[]')
        st.caption(f"Source: {r['menu_source'] or '—'} · Checked: {r['checked'] or '—'}")
        if not menu: st.warning('尚未擷取 Menu。自動擷取功能會在下一階段接上。')
        cats=[]
        for x in menu:
            if x.get('cat','Menu') not in cats: cats.append(x.get('cat','Menu'))
        for cat in cats:
            st.subheader(cat)
            for x in [z for z in menu if z.get('cat','Menu')==cat]:
                c1,c2=st.columns([4,1])
                en=x.get('en',''); zh=x.get('zh','')
                if lang=='中文': label=zh or en
                elif lang=='English': label=en or zh
                else: label=f"**{en}**  \n{zh}" if zh else f"**{en}**"
                c1.markdown(label); c2.markdown(f"<div class='price'>{x.get('price','—')}</div>",unsafe_allow_html=True)
    with t2:
        statuses=['Want to go','Been there','Favourite']
        idx=statuses.index(r['status']) if r['status'] in statuses else 0
        status=st.selectbox('Status / 狀態',statuses,index=idx)
        rating=st.slider('My rating / 我的評分',0,5,int(r['rating'] or 0))
        notes=st.text_area('Notes / 備註',value=r['notes'] or '',placeholder='例如：下次想試 Omakase、停車方便…')
        if st.button('Save / 儲存',use_container_width=True):
            c=conn(); c.execute('update restaurants set status=?,rating=?,notes=? where id=?',(status,rating,notes,r['id'])); c.commit(); c.close(); st.success('Saved'); st.rerun()
    with t3:
        st.write('**Address**'); st.write(r['address'] or '—')
        st.write('**Tags**'); st.write(r['tags'] or '—')
        st.write('**Menu source**'); st.write(r['menu_source'] or '—')
        st.write('**Last checked**'); st.write(r['checked'] or '—')

rows=get_rows()
if st.session_state.selected:
    r=next((x for x in rows if x['id']==st.session_state.selected),None)
    if r: restaurant_detail(r)
elif page in ['❤️ Pocket','🔎 Search']:
    q=''
    if page=='🔎 Search': q=st.text_input('Search',placeholder='Japanese · Wagyu · Victoria Park · 刺身')
    filt=st.segmented_control('Filter',['All','Want to go','Been there','Favourite'],default='All',label_visibility='collapsed')
    shown=0
    for r in rows:
        menu=json.loads(r['menu_json'] or '[]')
        hay=' '.join([r['name'] or '',r['address'] or '',r['tags'] or '',r['status'] or '']+[z.get('en','')+' '+z.get('zh','') for z in menu]).lower()
        if q and q.lower() not in hay: continue
        if filt!='All' and r['status']!=filt: continue
        shown+=1
        with st.container(border=True):
            st.subheader(r['name'])
            st.caption(f"{r['status']}" + (f" · {'★'*int(r['rating'])}" if r['rating'] else ''))
            st.markdown(''.join(f'<span class="pill">{t.strip()}</span>' for t in (r['tags'] or '').split(',') if t.strip()),unsafe_allow_html=True)
            st.write('📍 '+(r['address'] or 'Address not added'))
            if st.button('Open restaurant / 查看餐廳',key=f"open{r['id']}",use_container_width=True): st.session_state.selected=r['id']; st.rerun()
    if not shown: st.info('沒有符合的口袋餐廳。')
elif page=='➕ Add':
    st.subheader('➕ Add restaurant')
    st.caption('V1.1 先儲存餐廳；下一階段會把這裡改成「只輸入名稱，自動找官方資料與 Menu」。')
    with st.form('add'):
        name=st.text_input('Restaurant name *',placeholder='例如 Nobu Perth')
        address=st.text_input('Address')
        website=st.text_input('Official website')
        tags=st.text_input('Tags',placeholder='Japanese, High-end, Date night')
        status=st.selectbox('Status',['Want to go','Been there','Favourite'])
        ok=st.form_submit_button('＋ Add to Pocket',use_container_width=True)
        if ok:
            if not name.strip(): st.error('請輸入餐廳名稱。')
            else:
                c=conn(); cur=c.execute('''insert into restaurants(name,address,website,tags,menu_source,checked,menu_json,status) values(?,?,?,?,?,?,?,?)''',(name.strip(),address.strip(),website.strip(),tags.strip(),'Not checked yet / 尚未檢查','—','[]',status)); c.commit(); rid=cur.lastrowid; c.close(); st.session_state.selected=rid; st.rerun()
