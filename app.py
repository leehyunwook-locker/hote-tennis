import streamlit as st, sqlite3, pandas as pd, random, json
from datetime import datetime

# ==========================================
# 모바일 UI 최적화 및 홈화면 아이콘 세팅
# ==========================================
st.set_page_config(page_title="핫테 대진표", page_icon="🎾", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<script>
    const iconUrl = "https://raw.githubusercontent.com/leehyunwook-locker/hote-tennis/main/logo.jpg";
    let appleIcon = window.parent.document.querySelector('link[rel="apple-touch-icon"]');
    if (!appleIcon) {
        appleIcon = window.parent.document.createElement('link');
        appleIcon.rel = 'apple-touch-icon';
        window.parent.document.head.appendChild(appleIcon);
    }
    appleIcon.href = iconUrl;
</script>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 1.5rem; padding-left: 0.5rem; padding-right: 0.5rem; max-width: 100%; overflow-x: hidden; }
    [data-testid="collapsedControl"] { display: none; }
    h1, h2, h3, h4, h5 { margin-bottom: 0.4rem !important; margin-top: 0.4rem !important; }
    div[role="radiogroup"] { justify-content: space-around; background-color: #f0f2f6; padding: 5px; border-radius: 8px; margin-bottom: 8px;}
    .stRadio label { font-size: 14px !important; font-weight: bold; cursor: pointer; padding: 5px; }
    div[data-baseweb="select"] { margin-top: -5px; font-size: 13px !important; }
    
    .table-wrapper { overflow-x: auto; width: 100%; max-height: 65vh; margin-bottom: 1rem; border: 1px solid #ddd; }
    table.rank-table { border-collapse: separate; border-spacing: 0; width: 100%; text-align: center; font-size: 13px; font-family: sans-serif; white-space: nowrap; }
    table.rank-table td, table.rank-table th { padding: 8px 5px; border-bottom: 1px solid #ddd; border-right: 1px solid #ddd; text-align: center; }
    table.rank-table th { position: sticky; top: 0; background-color: #f0f2f6; z-index: 4; }
    table.rank-table th:nth-child(1), table.rank-table td:nth-child(1) { position: sticky; left: 0px; background-color: #f9f9f9; z-index: 3; min-width: 35px; }
    table.rank-table th:nth-child(2), table.rank-table td:nth-child(2) { position: sticky; left: 35px; background-color: #f9f9f9; z-index: 3; min-width: 50px; }
    table.rank-table th:nth-child(1), table.rank-table th:nth-child(2) { z-index: 5 !important; background-color: #eceff1; }
    
    .podium-box { border-radius: 10px; padding: 12px 5px; text-align: center; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .gold { background: linear-gradient(135deg, #FFD700 0%, #FDB931 100%); color: #4A3A00; }
    .silver { background: linear-gradient(135deg, #e2ebf0 0%, #cfd9df 100%); color: #333; }
    .bronze { background: linear-gradient(135deg, #d4af37 0%, #aa6c39 100%); color: #FFF; }
    .p-title { font-size: 14px; font-weight: bold; margin: 0; opacity: 0.9;}
    .p-name { font-size: 17px; font-weight: 900; margin: 5px 0; word-break: keep-all; }
    
    .team-box-a { background-color: #fffde7; border: 1px solid #ffd54f; border-radius: 8px; padding: 12px 2px; text-align: center; height: auto !important; min-height: 90px; display: flex; flex-direction: column; justify-content: center; overflow: visible; }
    .team-box-b { background-color: #e8f5e9; border: 1px solid #81c784; border-radius: 8px; padding: 12px 2px; text-align: center; height: auto !important; min-height: 90px; display: flex; flex-direction: column; justify-content: center; overflow: visible; }
    .nowrap-text { white-space: nowrap !important; word-break: keep-all !important; }
    .wrap-text { white-space: normal !important; word-break: keep-all !important; line-height: 1.4; }

    input[type="number"] { text-align: center; font-weight: bold; font-size: 18px !important; background-color: #f8f9fa; border: 1px solid #cfd8dc; border-radius: 5px; height: 42px !important; white-space: nowrap !important; padding: 0 !important;}
    div[data-testid="stButton"] button { height: 42px !important; padding: 0px 5px; font-size: 14px; margin-top: 0px; white-space: nowrap !important;}
    
    @media (max-width: 640px) {
        [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; overflow: hidden !important; }
        [data-testid="stHorizontalBlock"] > div { min-width: 0 !important; padding: 0 3px !important; }
        div[data-testid="stExpander"] details summary p { font-size: 15px !important; font-weight: bold !important; white-space: nowrap !important; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1단계: 강력한 DB 연결 모듈
# ==========================================
def get_db_conn():
    conn = sqlite3.connect('hote_tennis.db', timeout=60, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_db_conn()
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_password', '1234')")
        c.execute('''CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, gender TEXT, base_rating REAL, is_active INTEGER)''')
        
        c.execute("SELECT COUNT(*) FROM members")
        if c.fetchone()[0] == 0:
            default_members = [("상국", "남", 5.0, 0), ("홍만", "남", 5.0, 0), ("체야", "여", 5.0, 0), ("재윤", "여", 5.0, 0), ("인숙", "여", 5.0, 0), ("상철", "남", 5.0, 0), ("효경", "여", 5.0, 0), ("재민", "남", 5.0, 0), ("재경", "남", 5.0, 0), ("정호", "남", 5.0, 0), ("대홍", "남", 5.0, 0), ("영익", "남", 5.0, 0), ("영도", "남", 5.0, 0), ("진철", "남", 5.0, 0)]
            c.executemany("INSERT INTO members (name, gender, base_rating, is_active, is_guest) VALUES (?, ?, ?, 1, 0)", default_members)
        
        c.execute('''CREATE TABLE IF NOT EXISTS points_log (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, input_date TEXT, points INTEGER, games INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS match_history (id TEXT PRIMARY KEY, game_date TEXT, team_a TEXT, team_b TEXT, winner TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, event_date TEXT, event_name TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS event_matches (id TEXT PRIMARY KEY, event_id INTEGER, team_a TEXT, team_b TEXT, winner TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS event_points_log (id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER, name TEXT, points INTEGER, games INTEGER, match_id TEXT, result TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS point_rules (category TEXT PRIMARY KEY, win INTEGER, lose INTEGER, draw INTEGER)''')
        
        c.execute("SELECT COUNT(*) FROM point_rules")
        if c.fetchone()[0] == 0:
            default_rules = [("남남 대 남남", 3, 0, 1), ("여여 대 여여", 3, 0, 1), ("남녀 대 남녀", 3, 0, 1), ("남남 (혼복과 대결)", 3, 1, 1), ("남녀 (남남과 대결)", 5, 0, 2), ("단식", 3, 0, 1), ("대기자", 2, 0, 0), ("최소 게임수 (이벤트용)", 2, 0, 0)]
            c.executemany("INSERT INTO point_rules VALUES (?, ?, ?, ?)", default_rules)

        def add_column_safe(table, column, definition):
            try: c.execute(f"SELECT {column} FROM {table} LIMIT 1")
            except sqlite3.OperationalError:
                try: c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                except Exception: pass

        for t, c_name, defs in [
            ("members", "is_guest", "INTEGER DEFAULT 0"),
            ("points_log", "source_id", "TEXT"),
            ("points_log", "score_won", "INTEGER DEFAULT 0"),
            ("points_log", "score_lost", "INTEGER DEFAULT 0"),
            ("match_history", "team_a_pos", "TEXT DEFAULT '미지정'"),
            ("match_history", "team_b_pos", "TEXT DEFAULT '미지정'"),
            ("match_history", "score_a", "INTEGER DEFAULT 0"),
            ("match_history", "score_b", "INTEGER DEFAULT 0"),
            ("events", "event_type", "TEXT"),
            ("events", "team_1_name", "TEXT"),
            ("events", "team_2_name", "TEXT"),
            ("events", "team_1_members", "TEXT"),
            ("events", "team_2_members", "TEXT"),
            ("events", "participants", "TEXT"),
            ("events", "bracket_json", "TEXT"),
            ("events", "gen_params_json", "TEXT"),
            ("event_matches", "round", "INTEGER DEFAULT 0"),
            ("event_matches", "court", "INTEGER DEFAULT 0"),
            ("event_matches", "score_a", "INTEGER DEFAULT 0"),
            ("event_matches", "score_b", "INTEGER DEFAULT 0"),
            ("event_matches", "team_a_pos", "TEXT DEFAULT '미지정'"),
            ("event_matches", "team_b_pos", "TEXT DEFAULT '미지정'"),
            ("event_points_log", "score_won", "INTEGER DEFAULT 0"),
            ("event_points_log", "score_lost", "INTEGER DEFAULT 0")]:
            add_column_safe(t, c_name, defs)
        conn.commit()
    finally: conn.close()

if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

if 'pair_count' not in st.session_state: st.session_state['pair_count'] = 1
if 'team_count' not in st.session_state: st.session_state['team_count'] = 1
if 'e_pair_count' not in st.session_state: st.session_state['e_pair_count'] = 1
if 'e_team_count' not in st.session_state: st.session_state['e_team_count'] = 1
if 'admin_logged_in' not in st.session_state: st.session_state['admin_logged_in'] = False
if 'sync_done' not in st.session_state:
    conn = get_db_conn()
    try:
        c = conn.cursor()
        d_row = c.execute("SELECT value FROM settings WHERE key='active_match_date'").fetchone()
        j_row = c.execute("SELECT value FROM settings WHERE key='active_tournament_json'").fetchone()
        g_row = c.execute("SELECT value FROM settings WHERE key='active_gen_params_json'").fetchone()
        
        st.session_state['match_date'] = d_row[0] if d_row else datetime.now().strftime("%Y-%m-%d")
        st.session_state['tournament_data'] = {str(k): v for k, v in json.loads(j_row[0]).items()} if j_row and j_row[0] else {}
        st.session_state['gen_params'] = json.loads(g_row[0]) if g_row and g_row[0] else None
        st.session_state['sync_done'] = True
    finally: conn.close()

def get_admin_pwd():
    conn = get_db_conn()
    try: return conn.cursor().execute("SELECT value FROM settings WHERE key='admin_password'").fetchone()[0]
    finally: conn.close()

def get_members(exclude_guest=False):
    conn = get_db_conn()
    try:
        query = "SELECT * FROM members WHERE is_active=1"
        if exclude_guest: query += " AND is_guest=0"
        query += " ORDER BY name ASC"
        df = pd.read_sql_query(query, conn)
        pts_df = pd.read_sql_query("SELECT name, SUM(points) as p, SUM(games) as g FROM points_log GROUP BY name", conn)
        eff_dict = {row['name']: round(row['p'] / row['g'], 1) for _, row in pts_df.iterrows() if pd.notna(row['g']) and row['g'] > 0}
        df['eff_rating'] = df.apply(lambda x: float(eff_dict.get(x['name'], x['base_rating'])), axis=1)
        return df
    finally: conn.close()

def get_point_rules():
    conn = get_db_conn()
    try: return pd.read_sql_query("SELECT * FROM point_rules", conn).set_index('category').to_dict('index')
    finally: conn.close()

def strip_gender(s): return s.replace('(여)','').replace('(남)','').replace('(G)','').strip() if isinstance(s, str) else s

# ==========================================
# 실시간 순위, 미입력 안내, 대기자 표시 로직 
# ==========================================
def render_realtime_podium(pts_df, matches_df, min_games=1, title="🏆 실시간 순위"):
    if pts_df.empty:
        st.info("🎯 스코어가 저장된 경기가 없어 순위를 산정할 수 없습니다.")
        return pd.DataFrame()

    agg = pts_df.groupby('name').agg(승점=('points', 'sum'), 경기수=('games', 'sum')).reset_index()
    
    wl_dict = {n: {'승':0, '무':0, '패':0, '득점':0, '실점':0} for n in agg['name']}
    
    if not matches_df.empty:
        for _, m in matches_df.iterrows():
            ta = [x.strip() for x in str(m['team_a']).replace('&', ',').split(',') if x.strip()]
            tb = [x.strip() for x in str(m['team_b']).replace('&', ',').split(',') if x.strip()]
            w = m['winner']
            
            try: sa = int(m['score_a'])
            except: sa = 0
            try: sb = int(m['score_b'])
            except: sb = 0

            for u in ta:
                if u not in wl_dict: wl_dict[u] = {'승':0, '무':0, '패':0, '득점':0, '실점':0}
                wl_dict[u]['득점'] += sa
                wl_dict[u]['실점'] += sb
                if w == "A팀 승리": wl_dict[u]['승'] += 1
                elif w == "무승부": wl_dict[u]['무'] += 1
                elif w == "B팀 승리": wl_dict[u]['패'] += 1
                
            for u in tb:
                if u not in wl_dict: wl_dict[u] = {'승':0, '무':0, '패':0, '득점':0, '실점':0}
                wl_dict[u]['득점'] += sb
                wl_dict[u]['실점'] += sa
                if w == "B팀 승리": wl_dict[u]['승'] += 1
                elif w == "무승부": wl_dict[u]['무'] += 1
                elif w == "A팀 승리": wl_dict[u]['패'] += 1
                
    agg['승'] = agg['name'].map(lambda x: wl_dict.get(x, {}).get('승', 0)).fillna(0).astype(int)
    agg['무'] = agg['name'].map(lambda x: wl_dict.get(x, {}).get('무', 0)).fillna(0).astype(int)
    agg['패'] = agg['name'].map(lambda x: wl_dict.get(x, {}).get('패', 0)).fillna(0).astype(int)
    agg['득점'] = agg['name'].map(lambda x: wl_dict.get(x, {}).get('득점', 0)).fillna(0).astype(int)
    agg['실점'] = agg['name'].map(lambda x: wl_dict.get(x, {}).get('실점', 0)).fillna(0).astype(int)

    agg['득실차'] = agg['득점'] - agg['실점']
    agg['자격미달'] = agg['경기수'] < min_games

    agg = agg.sort_values(by=['자격미달', '승점', '득실차', '승', '패'], ascending=[True, False, False, False, True]).reset_index(drop=True)
    
    ranks, curr_rank = [], 1
    for i in range(len(agg)):
        if i == 0: ranks.append(curr_rank)
        else:
            prev, curr = agg.iloc[i-1], agg.iloc[i]
            if (prev['자격미달'] == curr['자격미달'] and prev['승점'] == curr['승점'] and prev['득실차'] == curr['득실차'] and prev['승'] == curr['승'] and prev['패'] == curr['패']):
                ranks.append(curr_rank)
            else:
                curr_rank += 1; ranks.append(curr_rank)
    agg['순위'] = ranks
    
    agg['평균승점_val'] = agg.apply(lambda x: x['승점'] / x['경기수'] if x['경기수'] > 0 else 0, axis=1)
    agg['평균득실차_val'] = agg.apply(lambda x: x['득실차'] / x['경기수'] if x['경기수'] > 0 else 0, axis=1)
    agg['평균승점'] = agg['평균승점_val'].apply(lambda x: f"{x:.2f}")
    agg['평균득실차'] = agg['평균득실차_val'].apply(lambda x: f"{x:.2f}")
    agg['승률'] = agg.apply(lambda x: f"{int(round((x['승']/x['경기수'])*100, 0))}%" if x['경기수'] > 0 else "0%", axis=1)
    
    def get_podium_html(rank_num, color_class, icon):
        df = agg[(agg['순위'] == rank_num) & (agg['자격미달'] == False)]
        if df.empty: return ""
        is_tie = len(df) > 1
        title_str = f"{icon} 공동 {rank_num}위" if is_tie else f"{icon} {rank_num}위"
        names = "<br>".join(df['name'].tolist())
        w, l, d, d_diff, tot_pts = int(df.iloc[0]['승']), int(df.iloc[0]['패']), int(df.iloc[0]['무']), int(df.iloc[0]['득실차']), int(df.iloc[0]['승점'])
        stat_str = f"<div style='font-size:13px; font-weight:normal; margin-top:6px; color:#444; line-height:1.4;'><b style='color:#000; font-size:15px;'>총 {tot_pts}점</b><br>{w}승 {d}무 {l}패<br>득실 {d_diff:+d}</div>"
        return f"<div class='podium-box {color_class}'><div class='p-title'>{title_str}</div><div class='p-name nowrap-text'>{names}</div>{stat_str}</div>"

    st.markdown(f"<h3 style='color:#1976D2; text-align:center; font-weight:900; margin-bottom:15px;'>{title}</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: 
        h = get_podium_html(1, 'gold', '🥇')
        if h: st.markdown(h, unsafe_allow_html=True)
    with c2: 
        h = get_podium_html(2, 'silver', '🥈')
        if h: st.markdown(h, unsafe_allow_html=True)
    with c3: 
        h = get_podium_html(3, 'bronze', '🥉')
        if h: st.markdown(h, unsafe_allow_html=True)
    st.divider()
    return agg

def display_missing_scores(t_data, is_event, event_id, target_date, uniq_id, all_ex_m, court_names, filter_name="전체 보기"):
    if not t_data: return
    try: r_keys = sorted(list(t_data.keys()), key=lambda x: int(x))
    except: return
    if not r_keys: return
    
    max_r = str(r_keys[-1])
    max_r_val = t_data.get(max_r) or t_data.get(int(max_r))
    
    if max_r_val and any(m['winner'] not in ['입력 대기', '취소'] for m in max_r_val['matches']):
        missing_matches = []
        for r in r_keys:
            r_str = str(r)
            r_val = t_data.get(r_str) or t_data.get(int(r))
            if not r_val: continue
            for c_idx, m in enumerate(r_val['matches']):
                if m['winner'] == '입력 대기': 
                    if filter_name != "전체 보기":
                        a_names = [p['name'] for p in m['team_a']]
                        b_names = [p['name'] for p in m['team_b']]
                        if filter_name not in a_names and filter_name not in b_names:
                            continue
                    missing_matches.append((r_str, c_idx, m))
        
        if missing_matches:
            st.markdown("<div style='padding:10px 5px; background-color:#fff3e0; border-radius:8px; border:2px solid #ffb74d; margin-bottom:15px;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color:#e65100; margin-top:0; margin-bottom:10px; font-weight:900; text-align:center;'>⚠️ 미입력 대진 (점수를 입력하세요)</h4>", unsafe_allow_html=True)
            for r_num, c_idx, m in missing_matches:
                c_name = court_names[c_idx] if c_idx < len(court_names) else str(c_idx+1)
                render_match_card(r_num, c_idx, m, False, filter_name, is_event, event_id, target_date, c_name, f"{uniq_id}_m", all_ex_m, auto_expand=True)
            st.markdown("</div>", unsafe_allow_html=True)

def display_wait_counts_db(target_date=None, event_id=None):
    conn = get_db_conn()
    try:
        if event_id is not None:
            df = pd.read_sql_query("SELECT name, COUNT(*) as cnt FROM event_points_log WHERE event_id=? AND games=0 GROUP BY name", conn, params=(event_id,))
        else:
            df = pd.read_sql_query("SELECT name, COUNT(*) as cnt FROM points_log WHERE input_date=? AND games=0 AND source_id NOT LIKE 'MANUAL_%' GROUP BY name", conn, params=(target_date,))
    finally: conn.close()
    
    if not df.empty and df['cnt'].sum() > 0:
        counts = {row['name']: row['cnt'] for _, row in df.iterrows() if row['cnt'] > 0}
        if not counts: return
        st.markdown("<div style='font-size:15px; font-weight:bold; color:#e65100; margin-top:15px; margin-bottom:5px;'>💤 개인별 대기 횟수표</div>", unsafe_allow_html=True)
        sorted_counts = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        
        html = "<table style='width:100%; border-collapse: collapse; text-align:center; font-size:14px; margin-bottom:10px;'>"
        for i in range(0, len(sorted_counts), 2):
            html += "<tr>"
            p1 = sorted_counts[i]
            html += f"<td style='padding:8px; border-bottom:1px solid #ddd;'><b style='color:#333;'>{p1[0]}</b> <span style='color:#d32f2f; font-weight:bold;'>{p1[1]}회</span></td>"
            if i + 1 < len(sorted_counts):
                p2 = sorted_counts[i+1]
                html += f"<td style='padding:8px; border-bottom:1px solid #ddd; border-left:1px dashed #ccc;'><b style='color:#333;'>{p2[0]}</b> <span style='color:#d32f2f; font-weight:bold;'>{p2[1]}회</span></td>"
            else: html += "<td style='padding:8px; border-bottom:1px solid #ddd; border-left:1px dashed #ccc;'></td>"
            html += "</tr>"
        html += "</table>"
        st.markdown(f"<div style='background-color:#fff; border-radius:8px; border:1px solid #ccc; padding:5px;'>{html}</div>", unsafe_allow_html=True)

# ==========================================
# 2단계: 승점 계산 및 매칭 로직
# ==========================================
def get_match_rule_category(team_a, team_b):
    if len(team_a) == 1 or len(team_b) == 1: return "단식"
    ga, gb = [p.get('gender','남') for p in team_a], [p.get('gender','남') for p in team_b]
    type_a = 'MM' if ga.count('남') == 2 else 'FF' if ga.count('여') == 2 else 'MF'
    type_b = 'MM' if gb.count('남') == 2 else 'FF' if gb.count('여') == 2 else 'MF'
    if type_a == 'MM' and type_b == 'MM': return '남남 대 남남'
    elif type_a == 'FF' and type_b == 'FF': return '여여 대 여여'
    elif type_a == 'MF' and type_b == 'MF': return '남녀 대 남녀'
    return '남남 (혼복과 대결)' 

def assign_points_db(match_id, target_date, team_a, team_b, result, is_event=False, event_id=None, score_a=0, score_b=0):
    conn = get_db_conn()
    try:
        c = conn.cursor()
        rules = get_point_rules()
        score_a, score_b = int(score_a), int(score_b)
        
        if is_event: c.execute("DELETE FROM event_points_log WHERE match_id=?", (match_id,))
        else: c.execute("DELETE FROM points_log WHERE source_id=?", (match_id,))

        if result not in ["입력 대기", "취소"]:
            cat_a = get_match_rule_category(team_a, team_b)
            pts_a, pts_b = 0, 0
            if len(team_a) == 1:
                r = rules.get("단식", {'win':3, 'lose':0, 'draw':1})
                if result == 'A팀 승리': pts_a, pts_b = r['win'], r['lose']
                elif result == 'B팀 승리': pts_a, pts_b = r['lose'], r['win']
                else: pts_a, pts_b = r['draw'], r['draw']
            else:
                ga, gb = [p.get('gender','남') for p in team_a], [p.get('gender','남') for p in team_b]
                type_a = 'MM' if ga.count('남') == 2 else 'FF' if ga.count('여') == 2 else 'MF'
                type_b = 'MM' if gb.count('남') == 2 else 'FF' if gb.count('여') == 2 else 'MF'
                if type_a == 'MF' and type_b == 'MM':
                    if result == 'A팀 승리': pts_a, pts_b = rules['남녀 (남남과 대결)']['win'], rules['남남 (혼복과 대결)']['lose']
                    elif result == 'B팀 승리': pts_a, pts_b = rules['남녀 (남남과 대결)']['lose'], rules['남남 (혼복과 대결)']['win']
                    else: pts_a, pts_b = rules['남녀 (남남과 대결)']['draw'], rules['남남 (혼복과 대결)']['draw']
                elif type_a == 'MM' and type_b == 'MF':
                    if result == 'A팀 승리': pts_a, pts_b = rules['남남 (혼복과 대결)']['win'], rules['남녀 (남남과 대결)']['lose']
                    elif result == 'B팀 승리': pts_a, pts_b = rules['남남 (혼복과 대결)']['lose'], rules['남녀 (남남과 대결)']['win']
                    else: pts_a, pts_b = rules['남남 (혼복과 대결)']['draw'], rules['남녀 (남남과 대결)']['draw']
                else:
                    r = rules.get(cat_a, rules.get('남남 대 남남', {'win':3, 'lose':0, 'draw':1}))
                    if result == 'A팀 승리': pts_a, pts_b = r['win'], r['lose']
                    elif result == 'B팀 승리': pts_a, pts_b = r['lose'], r['win']
                    else: pts_a, pts_b = r['draw'], r['draw']

            for p in team_a:
                if is_event: c.execute("INSERT INTO event_points_log (event_id, name, points, games, match_id, result, score_won, score_lost) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                       (event_id, str(p['name']), pts_a, 1, match_id, '승' if result=='A팀 승리' else '무' if result=='무승부' else '패', score_a, score_b))
                elif not p.get('is_guest', False): c.execute("INSERT INTO points_log (source_id, name, input_date, points, games, score_won, score_lost) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                                             (match_id, str(p['name']), target_date, pts_a, 1, score_a, score_b))
            for p in team_b:
                if is_event: c.execute("INSERT INTO event_points_log (event_id, name, points, games, match_id, result, score_won, score_lost) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                       (event_id, str(p['name']), pts_b, 1, match_id, '승' if result=='B팀 승리' else '무' if result=='무승부' else '패', score_b, score_a))
                elif not p.get('is_guest', False): c.execute("INSERT INTO points_log (source_id, name, input_date, points, games, score_won, score_lost) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                                             (match_id, str(p['name']), target_date, pts_b, 1, score_b, score_a))
        conn.commit()
    finally: conn.close()

def generate_single_round(players_df, court_count, play_mode, match_option, special_data_list, sub_option, current_r_num, all_rounds_data, team_rosters=None):
    player_dicts = players_df.to_dict('records')
    random.shuffle(player_dicts) 
    needed_players = court_count * (2 if play_mode == "단식" else 4)
    needed_waitlist = max(0, len(player_dicts) - needed_players)
    
    reserved_names = set()
    if play_mode == "복식":
        if match_option == "특정 페어 우선" and special_data_list:
            for pair in special_data_list: reserved_names.update(pair)
        elif match_option == "특정팀 대결 우선" and special_data_list:
            for matchup in special_data_list: reserved_names.update(matchup[0]); reserved_names.update(matchup[1])
            
    play_counts, past_partners, past_opponents = {p['name']: 0 for p in player_dicts}, {p['name']: set() for p in player_dicts}, {p['name']: set() for p in player_dicts}
    
    for r_num, r_data in all_rounds_data.items():
        if int(r_num) >= current_r_num: continue
        for match in r_data['matches']:
            if match['winner'] == '취소': continue
            ta, tb = [p['name'] for p in match['team_a']], [p['name'] for p in match['team_b']]
            for n in ta + tb:
                if n in play_counts: play_counts[n] += 1
            if len(ta) == 2: past_partners[ta[0]].add(ta[1]); past_partners[ta[1]].add(ta[0])
            if len(tb) == 2: past_partners[tb[0]].add(tb[1]); past_partners[tb[1]].add(tb[0])
            for pa in ta:
                for pb in tb: past_opponents[pa].add(pb); past_opponents[pb].add(pa)
    
    waitlist = []
    if needed_waitlist > 0:
        avail_for_wait = [p for p in player_dicts if p['name'] not in reserved_names]
        sorted_by_plays = sorted(avail_for_wait, key=lambda x: play_counts[x['name']], reverse=True)
        waitlist = sorted_by_plays[:needed_waitlist]
        if len(waitlist) < needed_waitlist:
            rem = needed_waitlist - len(waitlist)
            avail_reserved = [p for p in player_dicts if p['name'] in reserved_names and p not in waitlist]
            waitlist.extend(sorted(avail_reserved, key=lambda x: play_counts[x['name']], reverse=True)[:rem])
            
    playing_now = [p for p in player_dicts if p not in waitlist]
    matches = []
    
    if play_mode == "단식":
        while len(playing_now) >= 2 and len(matches) < court_count:
            p1 = playing_now.pop(0)
            best_p2, best_p2_idx, best_cost = None, -1, float('inf')
            for i, p2 in enumerate(playing_now):
                cost = abs(p1['eff_rating'] - p2['eff_rating']) + (10000 if p2['name'] in past_opponents[p1['name']] else 0)
                if cost < best_cost: best_cost, best_p2, best_p2_idx = cost, p2, i
            if best_p2:
                matches.append({"team_a": [p1], "team_b": [best_p2], "winner": "입력 대기"})
                playing_now.pop(best_p2_idx)
        waitlist.extend(playing_now)
        return {"matches": matches, "waitlist": waitlist, "option": "단식"}

    if match_option == "팀 상관없이 혼복우선":
        team_rosters = None
        match_option = "기본 (평점 우선)"
        sub_option = "혼복 우선"

    if team_rosters:
        pool_A = [p for p in playing_now if p['name'] in team_rosters['A']]
        pool_B = [p for p in playing_now if p['name'] in team_rosters['B']]
        teams_A = []
        while len(pool_A) >= 2:
            p1 = pool_A.pop(0)
            best_p2, best_cost, best_idx = None, float('inf'), -1
            for i, p2 in enumerate(pool_A):
                cost = abs(p1['eff_rating'] - p2['eff_rating']) + (10000 if p2['name'] in past_partners[p1['name']] else 0)
                if cost < best_cost: best_cost, best_p2, best_idx = cost, p2, i
            if best_p2: teams_A.append([p1, best_p2]); pool_A.pop(best_idx)
        teams_B = []
        while len(pool_B) >= 2:
            p1 = pool_B.pop(0)
            best_p2, best_cost, best_idx = None, float('inf'), -1
            for i, p2 in enumerate(pool_B):
                cost = abs(p1['eff_rating'] - p2['eff_rating']) + (10000 if p2['name'] in past_partners[p1['name']] else 0)
                if cost < best_cost: best_cost, best_p2, best_idx = cost, p2, i
            if best_p2: teams_B.append([p1, best_p2]); pool_B.pop(best_idx)
        while teams_A and teams_B and len(matches) < court_count:
            matches.append({"team_a": teams_A.pop(0), "team_b": teams_B.pop(0), "winner": "입력 대기"})
        waitlist.extend(pool_A + pool_B)
        for t in teams_A + teams_B: waitlist.extend(t)
        return {"matches": matches, "waitlist": waitlist, "option": "팀 대항전"}

    formed_teams = []
    if match_option == "특정팀 대결 우선" and special_data_list:
        for matchup in special_data_list:
            if len(matches) >= court_count: break
            ta = [p for p in playing_now if p['name'] in matchup[0]]
            tb = [p for p in playing_now if p['name'] in matchup[1]]
            if len(ta) == 2 and len(tb) == 2:
                matches.append({"team_a": ta, "team_b": tb, "winner": "입력 대기"})
                for pp in ta + tb: playing_now.remove(pp)

    if match_option == "특정 페어 우선" and special_data_list:
        for pair in special_data_list:
            team = [p for p in playing_now if p['name'] in pair]
            if len(team) == 2:
                formed_teams.append(team)
                for pp in team: playing_now.remove(pp)

    rest_opt = sub_option if match_option in ["특정팀 대결 우선", "특정 페어 우선"] else match_option
    needed_teams = (court_count - len(matches)) * 2
    target_team_rating = (sum(p['eff_rating'] for p in playing_now) / (len(playing_now) / 2)) if len(playing_now) > 0 else 10.0

    if rest_opt == "여복 우선":
        females = [p for p in playing_now if p['gender'] == '여']
        while len(females) >= 2 and len(formed_teams) < needed_teams:
            p1 = females.pop(0)
            best_p2, best_p2_idx, best_cost = None, -1, float('inf')
            for i, p2 in enumerate(females):
                cost = (10000 if p2['name'] in past_partners[p1['name']] else 0) + abs((p1['eff_rating'] + p2['eff_rating']) - target_team_rating)
                if cost < best_cost: best_cost, best_p2, best_p2_idx = cost, p2, i
            if best_p2:
                formed_teams.append([p1, best_p2]); females.pop(best_p2_idx)
                playing_now.remove(p1); playing_now.remove(best_p2)

    if rest_opt == "혼복 우선":
        males, females = [p for p in playing_now if p['gender'] == '남'], [p for p in playing_now if p['gender'] == '여']
        while len(males) >= 1 and len(females) >= 1 and len(formed_teams) < needed_teams:
            p1 = males.pop(0)
            best_p2, best_p2_idx, best_cost = None, -1, float('inf')
            for i, p2 in enumerate(females):
                cost = (10000 if p2['name'] in past_partners[p1['name']] else 0) + abs((p1['eff_rating'] + p2['eff_rating']) - target_team_rating)
                if cost < best_cost: best_cost, best_p2, best_p2_idx = cost, p2, i
            if best_p2:
                formed_teams.append([p1, best_p2]); females.pop(best_p2_idx)
                playing_now.remove(p1); playing_now.remove(best_p2)

    while len(playing_now) >= 2 and len(formed_teams) < needed_teams:
        p1 = playing_now.pop(0)
        best_p2, best_p2_idx, best_cost = None, -1, float('inf')
        for i, p2 in enumerate(playing_now):
            cost = (10000 if p2['name'] in past_partners[p1['name']] else 0) + abs((p1['eff_rating'] + p2['eff_rating']) - target_team_rating)
            if cost < best_cost: best_cost, best_p2, best_p2_idx = cost, p2, i
        if best_p2:
            formed_teams.append([p1, best_p2]); playing_now.pop(best_p2_idx)

    def get_t_type(t):
        g = [p['gender'] for p in t]
        return 'FF' if g.count('여') == 2 else 'MM' if g.count('남') == 2 else 'MF'

    while len(formed_teams) >= 2 and len(matches) < court_count:
        ta = formed_teams.pop(0)
        ta_type, ta_rating = get_t_type(ta), sum(p['eff_rating'] for p in ta)
        best_tb, best_tb_idx, best_cost = None, -1, float('inf')
        for i, tb in enumerate(formed_teams):
            penalty = 0
            if rest_opt in ["여복 우선", "혼복 우선"]:
                if ta_type != get_t_type(tb): penalty += 500000
            for pa in ta:
                for pb in tb:
                    if pb['name'] in past_opponents[pa['name']]: penalty += 10000
            cost = abs(ta_rating - sum(p['eff_rating'] for p in tb)) + penalty
            if cost < best_cost: best_cost, best_tb, best_tb_idx = cost, tb, i
        if best_tb:
            matches.append({"team_a": ta, "team_b": best_tb, "winner": "입력 대기"})
            formed_teams.pop(best_tb_idx)

    waitlist.extend(playing_now)
    for t in formed_teams: waitlist.extend(t)
    return {"matches": matches, "waitlist": waitlist, "option": match_option}

def save_active_tournament(m_date, t_data, gen_params=None):
    conn = get_db_conn()
    try:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('active_match_date', ?)", (m_date,))
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('active_tournament_json', ?)", (json.dumps(t_data),))
        if gen_params is not None:
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('active_gen_params_json', ?)", (json.dumps(gen_params),))
        conn.commit()
    finally: conn.close()

# --- 라운드, 개별 매치 UI 렌더링 카드 ---
def render_match_card(r_num, c_idx, match, is_admin, filter_name, is_event, event_id, target_date, c_name_display, uniq_id, all_ex_m, auto_expand=False):
    team_a, team_b, current_winner = match['team_a'], match['team_b'], match['winner']
    if current_winner == '취소': return
    
    a_avg = sum(float(p.get('eff_rating', 5.0)) for p in team_a) / len(team_a) if team_a else 0
    b_avg = sum(float(p.get('eff_rating', 5.0)) for p in team_b) / len(team_b) if team_b else 0
    diff = abs((a_avg*len(team_a)) - (b_avg*len(team_b)))
    is_singles = len(team_a) == 1
    
    m_id_check = f"EVT{event_id}_R{r_num}_C{c_idx}" if is_event else f"{target_date}_R{r_num}_C{c_idx}"
    ex_m = all_ex_m[all_ex_m['id'] == m_id_check] if not all_ex_m.empty and m_id_check in all_ex_m['id'].values else pd.DataFrame()

    try: def_sa = int(ex_m.iloc[0]['score_a']) if not ex_m.empty and pd.notna(ex_m.iloc[0]['score_a']) else 0
    except: def_sa = 0
    try: def_sb = int(ex_m.iloc[0]['score_b']) if not ex_m.empty and pd.notna(ex_m.iloc[0]['score_b']) else 0
    except: def_sb = 0
    
    sv_ta_pos = ex_m.iloc[0]['team_a_pos'] if not ex_m.empty and 'team_a_pos' in ex_m.columns else "🎾 포 지정"
    sv_tb_pos = ex_m.iloc[0]['team_b_pos'] if not ex_m.empty and 'team_b_pos' in ex_m.columns else "🎾 포 지정"
    if sv_ta_pos in ["미지정", "A팀 포-백 미지정", None, "🎾 포/백 선택"]: sv_ta_pos = "🎾 포 지정"
    if sv_tb_pos in ["미지정", "B팀 포-백 미지정", None, "🎾 포/백 선택"]: sv_tb_pos = "🎾 포 지정"

    ta_n_display = " & ".join([p['name'] for p in team_a])
    tb_n_display = " & ".join([p['name'] for p in team_b])
    
    display_winner = current_winner
    if current_winner == "A팀 승리": display_winner = f"{ta_n_display} 승리"
    elif current_winner == "B팀 승리": display_winner = f"{tb_n_display} 승리"
    status_text = f"<span style='color:#1976d2;'>{def_sa} : {def_sb} ({display_winner})</span>" if current_winner not in ['입력 대기'] else f"<span style='color:#757575;'>{current_winner}</span>"

    edit_mode_key = f"edit_mode_{r_num}_{c_idx}_{uniq_id}"
    if auto_expand and edit_mode_key not in st.session_state: st.session_state[edit_mode_key] = True
    elif edit_mode_key not in st.session_state: st.session_state[edit_mode_key] = False

    if not st.session_state[edit_mode_key]:
        st.markdown(f"""
        <div style='border: 1px solid #ddd; border-radius: 8px; padding: 10px; margin-bottom: 5px; background-color: #fff;'>
            <div style='font-size:12px; color:#555; margin-bottom:3px;'>[🏆 {r_num}R / {c_name_display} 코트]</div>
            <div class='wrap-text' style='font-size:16px; font-weight:900; color:#111;'>{ta_n_display} <span style='color:#d32f2f; font-size:14px;'>VS</span> {tb_n_display}</div>
            <div class='nowrap-text' style='font-size:13px; margin-top:3px; margin-bottom:5px;'>👉 결과: {status_text}</div>
        </div>
        """, unsafe_allow_html=True)
        
        c_btn1, c_btn2 = st.columns([3, 1.2])
        with c_btn1:
            btn_label = "📝 점수 수정" if current_winner != '입력 대기' else "📝 점수 입력"
            if st.button(btn_label, key=f"open_edit_{r_num}_{c_idx}_{uniq_id}", use_container_width=True):
                st.session_state[edit_mode_key] = True; st.rerun()
        with c_btn2:
            del_state_key = f"c_del_{r_num}_{c_idx}_{uniq_id}"
            if del_state_key not in st.session_state: st.session_state[del_state_key] = False
            
            if not st.session_state[del_state_key]:
                if st.button("❌ 삭제", key=f"db_{r_num}_{c_idx}_{uniq_id}", use_container_width=True):
                    st.session_state[del_state_key] = True; st.rerun()

        if st.session_state.get(del_state_key, False):
            st.markdown("<div class='nowrap-text' style='text-align:right; font-weight:bold; font-size:13px; color:#d32f2f; margin-bottom:5px;'>⚠️ 대진을 삭제하시겠습니까?</div>", unsafe_allow_html=True)
            cy, cn = st.columns([1, 1])
            with cy:
                if st.button("확인", key=f"dy_{r_num}_{c_idx}_{uniq_id}", type="primary", use_container_width=True):
                    conn = get_db_conn()
                    try:
                        if is_event:
                            st.session_state['event_tournament_data'][str(r_num)]['matches'][c_idx]['winner'] = "취소"
                            conn.cursor().execute("DELETE FROM event_matches WHERE id=?", (m_id_check,))
                            conn.cursor().execute("DELETE FROM event_points_log WHERE match_id=?", (m_id_check,))
                            conn.cursor().execute("UPDATE events SET bracket_json=? WHERE id=?", (json.dumps(st.session_state['event_tournament_data'], default=str), int(event_id)))
                        else:
                            st.session_state['tournament_data'][str(r_num)]['matches'][c_idx]['winner'] = "취소"
                            conn.cursor().execute("DELETE FROM match_history WHERE id=?", (m_id_check,))
                            conn.cursor().execute("DELETE FROM points_log WHERE source_id=?", (m_id_check,))
                            conn.cursor().execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('active_tournament_json', ?)", (json.dumps(st.session_state['tournament_data']),))
                        conn.commit()
                    finally: conn.close()
                    st.session_state[del_state_key] = False; st.rerun()
            with cn:
                if st.button("취소", key=f"dn_{r_num}_{c_idx}_{uniq_id}", use_container_width=True):
                    st.session_state[del_state_key] = False; st.rerun()
    else:
        st.markdown("<div style='background-color:#f9f9f9; padding:10px; border-radius:8px; border:1px solid #ccc; margin-bottom:10px;'>", unsafe_allow_html=True)
        show_pos = (not is_singles) and (not is_event)
        ta1_pos, ta2_pos, tb1_pos, tb2_pos = "미지정", "미지정", "미지정", "미지정"

        if show_pos:
            n_a1, n_a2 = team_a[0]['name'], team_a[1]['name']
            n_b1, n_b2 = team_b[0]['name'], team_b[1]['name']
            pos_opts_a, pos_opts_b = ["🎾 포 지정", n_a1, n_a2], ["🎾 포 지정", n_b1, n_b2]
            key_pa, key_pb = f"fa_{r_num}_{c_idx}_{uniq_id}", f"fb_{r_num}_{c_idx}_{uniq_id}"
            
            curr_pa = st.session_state.get(key_pa, sv_ta_pos.split("(포)")[0].strip() if "(포)" in sv_ta_pos else "🎾 포 지정")
            curr_pb = st.session_state.get(key_pb, sv_tb_pos.split("(포)")[0].strip() if "(포)" in sv_tb_pos else "🎾 포 지정")
            
            if curr_pa not in pos_opts_a: curr_pa = "🎾 포 지정"
            if curr_pb not in pos_opts_b: curr_pb = "🎾 포 지정"
            idx_a, idx_b = pos_opts_a.index(curr_pa), pos_opts_b.index(curr_pb)
            
            if curr_pa == n_a1: ta1_pos, ta2_pos = "포", "백"
            elif curr_pa == n_a2: ta1_pos, ta2_pos = "백", "포"
            if curr_pb == n_b1: tb1_pos, tb2_pos = "포", "백"
            elif curr_pb == n_b2: tb1_pos, tb2_pos = "백", "포"
        else:
            ta1_pos, tb1_pos = "-", "-"

        def get_player_str(p, pos):
            g, rating = p.get('gender', '남'), float(p.get('eff_rating', 5.0))
            pos_html = f" <span style='font-size:13px; color:#d32f2f; font-weight:900;'>: {pos}</span>" if pos in ["포", "백"] else ""
            return f"<div class='nowrap-text' style='font-size:16px; font-weight:900; color:#111; margin-bottom:2px;'>{p['name']}({g}) {rating:.1f}{pos_html}</div>"

        c_top1, c_top2 = st.columns([5, 1.2])
        with c_top1: st.markdown(f"<div style='font-size:14px; font-weight:bold; color:#d32f2f; margin-bottom:5px; white-space:nowrap;'>🔥 평점 차이: {diff:.1f}</div>", unsafe_allow_html=True)
        with c_top2:
            if st.button("닫기", key=f"close_{r_num}_{c_idx}_{uniq_id}", use_container_width=True):
                st.session_state[edit_mode_key] = False; st.rerun()

        c_b1, c_b2 = st.columns(2)
        with c_b1: st.markdown(f"<div class='team-box-a'><div class='nowrap-text' style='font-size: 12px; color: #2e7d32; margin-bottom: 5px; font-weight: bold;'>A팀 평균 : {a_avg:.1f}</div>{get_player_str(team_a[0], ta1_pos)}{get_player_str(team_a[1], ta2_pos) if not is_singles else ''}</div>", unsafe_allow_html=True)
        with c_b2: st.markdown(f"<div class='team-box-b'><div class='nowrap-text' style='font-size: 12px; color: #1565c0; margin-bottom: 5px; font-weight: bold;'>B팀 평균 : {b_avg:.1f}</div>{get_player_str(team_b[0], tb1_pos)}{get_player_str(team_b[1], tb2_pos) if not is_singles else ''}</div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
        if not is_admin:
            if show_pos:
                cp1, cp2 = st.columns(2)
                with cp1: st.selectbox(f"A포", pos_opts_a, index=idx_a, key=key_pa, label_visibility="collapsed")
                with cp2: st.selectbox(f"B포", pos_opts_b, index=idx_b, key=key_pb, label_visibility="collapsed")

            cs1, cs2, cs3 = st.columns([1.5, 1.2, 1.5])
            with cs1: score_a = st.number_input("A", min_value=0, max_value=50, value=def_sa, key=f"sa_{r_num}_{c_idx}_{uniq_id}", label_visibility="collapsed")
            with cs3: score_b = st.number_input("B", min_value=0, max_value=50, value=def_sb, key=f"sb_{r_num}_{c_idx}_{uniq_id}", label_visibility="collapsed")
            
            with cs2:
                if st.button("저장", key=f"sv_{r_num}_{c_idx}_{uniq_id}", type="primary", use_container_width=True):
                    win_res = "A팀 승리" if score_a > score_b else "B팀 승리" if score_b > score_a else "무승부"
                    pa_val, pb_val = "미지정", "미지정"
                    if show_pos:
                        curr_fore_a_val = st.session_state.get(key_pa, "🎾 포 지정")
                        if curr_fore_a_val == n_a1: pa_val = f"{n_a1}(포) / {n_a2}(백)"
                        elif curr_fore_a_val == n_a2: pa_val = f"{n_a2}(포) / {n_a1}(백)"
                        curr_fore_b_val = st.session_state.get(key_pb, "🎾 포 지정")
                        if curr_fore_b_val == n_b1: pb_val = f"{n_b1}(포) / {n_b2}(백)"
                        elif curr_fore_b_val == n_b2: pb_val = f"{n_b2}(포) / {n_b1}(백)"

                    conn = get_db_conn()
                    try:
                        if is_event:
                            st.session_state['event_tournament_data'][str(r_num)]['matches'][c_idx]['winner'] = win_res
                            conn.cursor().execute("UPDATE events SET bracket_json=? WHERE id=?", (json.dumps(st.session_state['event_tournament_data'], default=str), int(event_id)))
                            conn.cursor().execute("INSERT OR REPLACE INTO event_matches (id, event_id, round, court, team_a, team_b, winner, score_a, score_b, team_a_pos, team_b_pos) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                                                  (m_id_check, int(event_id), r_num, c_idx, ta_n_display, tb_n_display, win_res, int(score_a), int(score_b), pa_val, pb_val))
                        else:
                            st.session_state['tournament_data'][str(r_num)]['matches'][c_idx]['winner'] = win_res
                            save_active_tournament(target_date, st.session_state['tournament_data'], st.session_state.get('gen_params'))
                            conn.cursor().execute("INSERT OR REPLACE INTO match_history (id, game_date, team_a, team_b, winner, score_a, score_b, team_a_pos, team_b_pos) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                                                  (m_id_check, target_date, ta_n_display, tb_n_display, win_res, int(score_a), int(score_b), pa_val, pb_val))
                        conn.commit()
                    finally: conn.close()
                    assign_points_db(m_id_check, target_date if not is_event else selected_event['event_date'], team_a, team_b, win_res, is_event, event_id, int(score_a), int(score_b))
                    st.session_state[edit_mode_key] = False; st.success("저장 완료!"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

def render_horizontal_bracket(r_num, round_data, is_admin=False, filter_name="전체 보기", is_event=False, event_id=None, target_date=None, court_names=None):
    is_my_waitlist = filter_name != "전체 보기" and filter_name in [p['name'] for p in round_data['waitlist']]
    filtered_matches = []
    is_my_match_exist = False
    
    for c_idx, match in enumerate(round_data['matches']):
        if match['winner'] == '취소': continue
        a_names = [p['name'] for p in match['team_a']]
        b_names = [p['name'] for p in match['team_b']]
        if filter_name == "전체 보기" or filter_name in a_names or filter_name in b_names:
            filtered_matches.append((c_idx, match))
            if filter_name != "전체 보기": is_my_match_exist = True
            
    if filter_name != "전체 보기" and not is_my_waitlist and not is_my_match_exist: return False

    uniq_id = f"evt_{event_id}" if is_event else f"reg_{target_date}"
    round_status = " [💤 휴식]" if is_my_waitlist else " [🎾 출전]" if is_my_match_exist else ""
    auto_expand = True if is_my_match_exist else False

    with st.expander(f"🏆 {r_num} 라운드 ({round_data['option']}){round_status}", expanded=auto_expand):
        if round_data['waitlist']:
            w_names = [f"{p['name']}(G)" if p.get('is_guest',0) else p['name'] for p in round_data['waitlist']]
            if filter_name == "전체 보기": st.markdown(f"<div class='wrap-text' style='font-size:13px; color:#e65100; margin-bottom:10px;'>💤 대기: {', '.join(w_names)}</div>", unsafe_allow_html=True)
            elif is_my_waitlist: st.markdown(f"<div style='font-size:15px; font-weight:bold; color:#e65100; margin-bottom:10px; padding:10px; background-color:#fff3e0; border-radius:5px; text-align:center;'>💤 이번 라운드는 휴식(대기)입니다.</div>", unsafe_allow_html=True)

        if court_names is None: court_names = [str(i+1) for i in range(20)]

        conn = get_db_conn()
        try:
            if is_event: all_ex_m = pd.read_sql_query("SELECT id, score_a, score_b, team_a_pos, team_b_pos FROM event_matches WHERE event_id=? AND round=?", conn, params=(event_id, r_num))
            else: all_ex_m = pd.read_sql_query("SELECT id, score_a, score_b, team_a_pos, team_b_pos FROM match_history WHERE game_date=? AND id LIKE ?", conn, params=(target_date, f"%_R{r_num}_%"))
        finally: conn.close()

        for c_idx, match in filtered_matches:
            c_name = court_names[c_idx] if c_idx < len(court_names) else str(c_idx + 1)
            render_match_card(r_num, c_idx, match, is_admin, filter_name, is_event, event_id, target_date, c_name, uniq_id, all_ex_m, auto_expand)
        
        if is_admin:
            regen_mode_key = f"regen_mode_{r_num}_{uniq_id}"
            if regen_mode_key not in st.session_state: st.session_state[regen_mode_key] = False
            
            if st.button("🔄 라운드 재설정 메뉴 열기/닫기", key=f"r_regen_btn_{r_num}_{uniq_id}"):
                st.session_state[regen_mode_key] = not st.session_state[regen_mode_key]
                st.rerun()

            if st.session_state[regen_mode_key]:
                st.markdown("<div style='background-color:#f0f2f6; padding:10px; border-radius:8px; margin-bottom:10px;'>", unsafe_allow_html=True)
                st.markdown("#### 🔄 단일 라운드 재생성")
                c_rm, c_ro = st.columns(2)
                with c_rm: new_mode = st.radio("경기 방식", ["복식", "단식"], horizontal=True, key=f"amode_{r_num}_{uniq_id}")
                with c_ro: new_opt = st.selectbox("대진 기준", ["기본 (평점 우선)", "혼복 우선", "여복 우선", "팀 상관없이 혼복우선"], key=f"aopt_{r_num}_{uniq_id}")
                if st.button("현재 라운드 다시 짜기", key=f"aregen_{r_num}_{uniq_id}", type="primary"):
                    p_names = [p['name'] for m in round_data['matches'] for p in m['team_a']+m['team_b']] + [w['name'] for w in round_data['waitlist']]
                    reg_df_tmp = get_members()
                    
                    if is_event:
                        e_gen_params = json.loads(pd.read_sql_query("SELECT gen_params_json FROM events WHERE id=?", get_db_conn(), params=(event_id,)).iloc[0]['gen_params_json'])
                        custom_ratings = e_gen_params.get('custom_ratings', {})
                        recon_dicts = []
                        for n in p_names:
                            match_df = reg_df_tmp[reg_df_tmp['name'] == n]
                            if not match_df.empty: recon_dicts.append({"name": n, "gender": match_df.iloc[0]['gender'], "eff_rating": custom_ratings.get(n, float(match_df.iloc[0]['eff_rating'])), "is_guest": match_df.iloc[0]['is_guest']})
                            else: recon_dicts.append({"name": n, "gender": '남', "eff_rating": 5.0, "is_guest": 1})
                        a_df = pd.DataFrame(recon_dicts)
                        evt_team_rosters = {'A': [strip_gender(n) for n in str(pd.read_sql_query("SELECT team_1_members FROM events WHERE id=?", get_db_conn(), params=(event_id,)).iloc[0,0]).split(',') if n], 'B': [strip_gender(n) for n in str(pd.read_sql_query("SELECT team_2_members FROM events WHERE id=?", get_db_conn(), params=(event_id,)).iloc[0,0]).split(',') if n]} if "팀 대항전" in pd.read_sql_query("SELECT event_type FROM events WHERE id=?", get_db_conn(), params=(event_id,)).iloc[0,0] else None
                        new_r = generate_single_round(a_df.copy(), len(court_names), new_mode, new_opt, [], "기본 (평점 우선)", int(r_num), st.session_state['event_tournament_data'], team_rosters=evt_team_rosters)
                        st.session_state['event_tournament_data'][str(r_num)] = new_r
                        conn = get_db_conn()
                        try:
                            wl_id = f"EVT{event_id}_R{r_num}_Waitlist"
                            conn.cursor().execute("DELETE FROM event_points_log WHERE match_id=?", (wl_id,))
                            rules = get_point_rules()
                            for w in new_r['waitlist']: conn.cursor().execute("INSERT INTO event_points_log (event_id, name, points, games, match_id, result) VALUES (?, ?, ?, ?, ?, ?)", (event_id, str(w['name']), rules.get('대기자', {'win':2})['win'], 0, wl_id, '대기'))
                            conn.cursor().execute("DELETE FROM event_matches WHERE event_id=? AND round=?", (event_id, int(r_num)))
                            conn.cursor().execute("DELETE FROM event_points_log WHERE event_id=? AND match_id LIKE ?", (event_id, f"EVT{event_id}_R{r_num}_C%"))
                            conn.cursor().execute("UPDATE events SET bracket_json=? WHERE id=?", (json.dumps(st.session_state['event_tournament_data'], default=str), event_id))
                            conn.commit()
                        finally: conn.close()
                    else:
                        p_df = reg_df_tmp[reg_df_tmp['name'].isin(p_names)]
                        new_r = generate_single_round(p_df, len(court_names), new_mode, new_opt, [], "기본 (평점 우선)", int(r_num), st.session_state['tournament_data'])
                        st.session_state['tournament_data'][str(r_num)] = new_r
                        conn = get_db_conn()
                        try:
                            wl_id = f"{target_date}_R{r_num}_Waitlist"
                            conn.cursor().execute("DELETE FROM points_log WHERE source_id=?", (wl_id,))
                            rules = get_point_rules()
                            for w in new_r['waitlist']:
                                if not w.get('is_guest', False): conn.cursor().execute("INSERT INTO points_log (source_id, name, input_date, points, games) VALUES (?, ?, ?, ?, ?)", (wl_id, str(w['name']), target_date, rules.get('대기자', {'win':2})['win'], 0))
                            conn.cursor().execute("DELETE FROM match_history WHERE id LIKE ?", (f"{target_date}_R{r_num}_C%",))
                            conn.cursor().execute("DELETE FROM points_log WHERE source_id LIKE ?", (f"{target_date}_R{r_num}_C%",))
                            conn.commit()
                        finally: conn.close()
                        save_active_tournament(target_date, st.session_state['tournament_data'], st.session_state.get('gen_params'))
                    st.session_state[regen_mode_key] = False; st.rerun()

                st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
                st.markdown("#### 🔄 개별 인원 교체")
                playing_names = []
                for m in round_data['matches']: 
                    if m['winner'] != '취소': playing_names.extend([p['name'] for p in m['team_a']] + [p['name'] for p in m['team_b']])
                wait_names = [p['name'] for p in round_data['waitlist']]
                reg_df = get_members()
                playing_names_opts = [f"{n}({reg_df[reg_df['name']==n]['gender'].iloc[0] if not reg_df[reg_df['name']==n].empty else '남'})" for n in playing_names]
                swap_out = strip_gender(st.selectbox("🔽 코트에서 뺄 사람", playing_names_opts, key=f"sout_{r_num}_{uniq_id}"))
                in_opts = [f"🟢 [대기자] {w}({reg_df[reg_df['name']==w]['gender'].iloc[0] if not reg_df[reg_df['name']==w].empty else '남'})" for w in wait_names if w != swap_out]
                
                if is_event:
                    conn = get_db_conn()
                    try: events_df = pd.read_sql_query("SELECT * FROM events WHERE id=?", conn, params=(event_id,))
                    finally: conn.close()
                    part_str = events_df.iloc[0].get('participants', "")
                    raw_players = [x.strip() for x in part_str.split(",") if x.strip()] if part_str else get_members()['name'].tolist()
                    clean_opts = []
                    for rp in raw_players:
                        g, n = '여' if '(여)' in rp else '남', strip_gender(rp)
                        m_df = reg_df[reg_df['name'] == n]
                        if not m_df.empty: clean_opts.append(f"{n}({m_df.iloc[0]['gender']})")
                        else: clean_opts.append(f"{n}({g})")
                    non_attending = [n for n in clean_opts if strip_gender(n) not in playing_names + wait_names]
                else:
                    all_names = reg_df['name'].tolist()
                    attending_names = st.session_state.get('gen_params', {}).get('selected_names', playing_names + wait_names)
                    non_attending = [n for n in all_names if n not in playing_names + wait_names and n in attending_names]
                    
                in_opts.extend([f"⚪ [미참석] {n}" for n in non_attending])
                swap_in_display = st.selectbox("🔼 대신 들어갈 사람", in_opts if in_opts else ["선택불가"], key=f"sin_{r_num}_{uniq_id}")
                
                if st.button("교체 실행", key=f"sbtn_{r_num}_{uniq_id}", type="primary"):
                    if swap_in_display == "선택불가": st.error("대체할 선수가 없습니다.")
                    else:
                        in_name = strip_gender(swap_in_display.replace("🟢 [대기자] ", "").replace("⚪ [미참석] ", ""))
                        match_df = reg_df[reg_df['name'] == in_name]
                        new_p_data = match_df.iloc[0].to_dict() if not match_df.empty else {'name': str(in_name), 'gender': '남', 'eff_rating': 5.0, 'is_guest': 1}
                        
                        if "대기자" in swap_in_display: round_data['waitlist'] = [w for w in round_data['waitlist'] if w['name'] != in_name]
                        for m in round_data['matches']:
                            if m['winner'] == '취소': continue
                            for i, p in enumerate(m['team_a']):
                                if p['name'] == swap_out: m['team_a'][i] = new_p_data; m['winner'] = "입력 대기"
                            for i, p in enumerate(m['team_b']):
                                if p['name'] == swap_out: m['team_b'][i] = new_p_data; m['winner'] = "입력 대기"
                        
                        rules, conn = get_point_rules(), get_db_conn()
                        try:
                            if is_event:
                                wl_id = f"EVT{event_id}_R{r_num}_Waitlist"
                                conn.cursor().execute("DELETE FROM event_points_log WHERE match_id=?", (wl_id,))
                                for w in round_data['waitlist']: conn.cursor().execute("INSERT INTO event_points_log (event_id, name, points, games, match_id, result) VALUES (?, ?, ?, ?, ?, ?)", (event_id, str(w['name']), rules.get('대기자', {'win':2})['win'], 0, wl_id, '대기'))
                                for c_idx, m in enumerate(round_data['matches']):
                                    if m['winner'] == "입력 대기":
                                        m_id = f"EVT{event_id}_R{r_num}_C{c_idx}"
                                        conn.cursor().execute("DELETE FROM event_matches WHERE id=?", (m_id,))
                                        conn.cursor().execute("DELETE FROM event_points_log WHERE match_id=?", (m_id,))
                                st.session_state['event_tournament_data'][str(r_num)] = round_data
                                conn.cursor().execute("UPDATE events SET bracket_json=? WHERE id=?", (json.dumps(st.session_state['event_tournament_data'], default=str), event_id))
                            else:
                                wl_id = f"{target_date}_R{r_num}_Waitlist"
                                conn.cursor().execute("DELETE FROM points_log WHERE source_id=?", (wl_id,))
                                for w in round_data['waitlist']: conn.cursor().execute("INSERT INTO points_log (source_id, name, input_date, points, games) VALUES (?, ?, ?, ?, ?)", (wl_id, str(w['name']), target_date, rules.get('대기자', {'win':2})['win'], 0))
                                for c_idx, m in enumerate(round_data['matches']):
                                    if m['winner'] == "입력 대기":
                                        m_id = f"{target_date}_R{r_num}_C{c_idx}"
                                        conn.cursor().execute("DELETE FROM match_history WHERE id=?", (m_id,))
                                        conn.cursor().execute("DELETE FROM points_log WHERE source_id=?", (m_id,))
                                st.session_state['tournament_data'][str(r_num)] = round_data
                                save_active_tournament(target_date, st.session_state['tournament_data'], st.session_state.get('gen_params'))
                            conn.commit()
                        finally: conn.close()
                        st.success("교체 완료!"); st.rerun()

# ==========================================
# 3단계: 메인 메뉴 UI
# ==========================================
st.markdown("<h2 style='text-align: center; color: #d32f2f; font-weight: 900; font-size: 1.8rem; white-space: nowrap;'>🎾 핫테 대진표</h2>", unsafe_allow_html=True)
menu = st.radio("메뉴 이동", ["대진표", "랭킹", "개인별 분석", "이벤트", "관리자"], horizontal=True, label_visibility="collapsed")

# ----------------------------------------
# 1. 정규 대진표
# ----------------------------------------
if menu == "대진표":
    conn = get_db_conn()
    try: mh_dates_df = pd.read_sql_query("SELECT DISTINCT game_date FROM match_history ORDER BY game_date DESC", conn)
    finally: conn.close()
    
    active_date = st.session_state['match_date']
    all_dates = mh_dates_df['game_date'].tolist()
    options = []
    if st.session_state['tournament_data']: options.append(f"{active_date} (오늘/현재)")
    for d in all_dates:
        if d != active_date: options.append(d)
        elif not st.session_state['tournament_data']: options.append(d)
        
    if not options: st.warning("생성된 대진표나 과거 기록이 없습니다.")
    else:
        all_members_df = get_members()
        all_names = all_members_df['name'].tolist()
        
        view_mode = st.radio("보기 방식", ["개인별", "라운드별", "코트별"], horizontal=True, label_visibility="collapsed")
        
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1: sel_opt = st.selectbox("📅 날짜 선택", options)
        with col_opt2: 
            if view_mode == "개인별": filter_name = st.selectbox("👤 선수 선택", all_names)
            else: filter_name = "전체 보기"
            
        st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
        
        if sel_opt.startswith(active_date):
            conn = get_db_conn()
            try:
                pts_df = pd.read_sql_query("SELECT * FROM points_log WHERE input_date=?", conn, params=(active_date,))
                matches_check = pd.read_sql_query("SELECT * FROM match_history WHERE game_date=? AND winner != '입력 대기' AND winner != '취소'", conn, params=(active_date,))
            finally: conn.close()
            
            render_realtime_podium(pts_df, matches_check, min_games=1, title="🏆 실시간 순위")
            
            t_data = st.session_state.get('tournament_data', {})
            uniq_id = f"reg_{active_date}"
            conn = get_db_conn()
            try: all_ex_m = pd.read_sql_query("SELECT id, score_a, score_b, team_a_pos, team_b_pos FROM match_history WHERE game_date=?", conn, params=(active_date,))
            finally: conn.close()
            reg_court_names = st.session_state.get('gen_params', {}).get('court_names', [str(i+1) for i in range(20)])

            if t_data:
                if view_mode == "개인별":
                    # 개인별 선택시, 내가 포함된 전체 라운드가 최우선 표시됨
                    for r_num, round_data in t_data.items():
                        render_horizontal_bracket(r_num, round_data, is_admin=False, filter_name=filter_name, target_date=active_date, court_names=reg_court_names)
                    display_missing_scores(t_data, False, None, active_date, uniq_id, all_ex_m, reg_court_names, filter_name)
                
                elif view_mode == "라운드별":
                    display_missing_scores(t_data, False, None, active_date, uniq_id, all_ex_m, reg_court_names, "전체 보기")
                    for r_num, round_data in t_data.items():
                        render_horizontal_bracket(r_num, round_data, is_admin=False, filter_name="전체 보기", target_date=active_date, court_names=reg_court_names)
                
                elif view_mode == "코트별":
                    display_missing_scores(t_data, False, None, active_date, uniq_id, all_ex_m, reg_court_names, "전체 보기")
                    courts_dict = {}
                    for r_num, round_data in t_data.items():
                        for c_idx, match in enumerate(round_data['matches']):
                            if match['winner'] == '취소': continue
                            if c_idx not in courts_dict: courts_dict[c_idx] = []
                            courts_dict[c_idx].append((r_num, match))
                            
                    for c_idx in sorted(courts_dict.keys()):
                        c_name = reg_court_names[c_idx] if c_idx < len(reg_court_names) else str(c_idx+1)
                        with st.expander(f"🎾 [{c_name} 코트] 전체 매치", expanded=False):
                            for r_num, match in courts_dict[c_idx]:
                                render_match_card(r_num, c_idx, match, False, "전체 보기", False, None, active_date, c_name, uniq_id, all_ex_m, auto_expand=False)

                conn = get_db_conn()
                try: manual_df = pd.read_sql_query("SELECT id, team_a, team_b, winner, score_a, score_b FROM match_history WHERE game_date=? AND id LIKE 'MANUAL_%'", conn, params=(active_date,))
                finally: conn.close()
                
                if not manual_df.empty:
                    st.markdown("#### 🏃‍♂️ 직접 등록한 현장 매치")
                    for idx, row in manual_df.iterrows():
                        ta_str, tb_str = row['team_a'].replace(',', ' & '), row['team_b'].replace(',', ' & ')
                        display_winner = f"{ta_str} 승리" if row['winner'] == "A팀 승리" else f"{tb_str} 승리" if row['winner'] == "B팀 승리" else row['winner']

                        st.markdown(f"""
                        <div style='display: flex; justify-content: space-between; align-items: center; background-color: #fff; padding: 10px 5px; border-radius: 5px; border: 1px solid #eee; margin-bottom: 5px;'>
                            <div class='wrap-text' style='flex: 1; text-align: right; font-size: 14px; font-weight: bold; color: #333;'>{ta_str}</div>
                            <div style='flex: 0 0 70px; text-align: center; font-size: 15px; font-weight: 900; color: {"#1976d2" if row['winner'] == 'A팀 승리' else "#d32f2f" if row['winner'] == 'B팀 승리' else "#757575"};'>
                                {"<br>".join([f"{row['score_a']}:{row['score_b']}"]) if row['score_a']>0 or row['score_b']>0 else display_winner}
                            </div>
                            <div class='wrap-text' style='flex: 1; text-align: left; font-size: 14px; font-weight: bold; color: #333;'>{tb_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        cd1, cd2, cd3 = st.columns([1, 1, 1])
                        with cd2:
                            del_key_man = f"c_del_man_{row['id']}"
                            if del_key_man not in st.session_state: st.session_state[del_key_man] = False
                            if not st.session_state[del_key_man]:
                                if st.button("❌ 삭제", key=f"dmb_{row['id']}", use_container_width=True):
                                    st.session_state[del_key_man] = True; st.rerun()
                            else:
                                st.markdown("<div class='nowrap-text' style='text-align:center; font-weight:bold; font-size:13px; color:#d32f2f; margin-bottom:3px;'>⚠️ 삭제 확인</div>", unsafe_allow_html=True)
                                cy, cn = st.columns(2)
                                with cy:
                                    if st.button("확인", key=f"dmy_{row['id']}", type="primary", use_container_width=True):
                                        conn = get_db_conn()
                                        try:
                                            conn.cursor().execute("DELETE FROM match_history WHERE id=?", (row['id'],))
                                            conn.cursor().execute("DELETE FROM points_log WHERE source_id=?", (row['id'],))
                                            conn.commit()
                                        finally: conn.close()
                                        st.session_state[del_key_man] = False; st.rerun()
                                with cn:
                                    if st.button("취소", key=f"dmn_{row['id']}", use_container_width=True):
                                        st.session_state[del_key_man] = False; st.rerun()
                        st.markdown("<hr style='margin:3px 0; border-top:1px dashed #eee;'>", unsafe_allow_html=True)

                with st.expander("➕ 현장 게임 추가 등록", expanded=False):
                    st.markdown("<div style='text-align:center; font-size:15px; font-weight:bold; color:#d32f2f; margin-bottom:8px;'>🔥 현장 추가 매치</div>", unsafe_allow_html=True)
                    pos_opts_a, pos_opts_b = ["🎾 포 지정", "A-1", "A-2"], ["🎾 포 지정", "B-1", "B-2"]
                    
                    m_col1, m_col2 = st.columns(2)
                    with m_col1:
                        st.markdown("<div class='team-box-a' style='min-height:30px; padding:5px;'><div style='font-size: 13px; color: #2e7d32; font-weight: bold;'>A팀 배정</div></div>", unsafe_allow_html=True)
                        ma_1 = st.selectbox("A-1", ["선택"] + all_names, key="ma_1")
                        ma_2 = st.selectbox("A-2 (단식 비움)", ["선택", "단식"] + all_names, key="ma_2")
                    with m_col2:
                        st.markdown("<div class='team-box-b' style='min-height:30px; padding:5px;'><div style='font-size: 13px; color: #1565c0; font-weight: bold;'>B팀 배정</div></div>", unsafe_allow_html=True)
                        mb_1 = st.selectbox("B-1", ["선택"] + all_names, key="mb_1")
                        mb_2 = st.selectbox("B-2 (단식 비움)", ["선택", "단식"] + all_names, key="mb_2")
                    
                    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                    cp1, cp2 = st.columns(2)
                    with cp1: ma_pos = st.selectbox("A포지정", pos_opts_a, key="ma_pos", label_visibility="collapsed")
                    with cp2: mb_pos = st.selectbox("B포지정", pos_opts_b, key="mb_pos", label_visibility="collapsed")
                        
                    ms1, ms2, ms3 = st.columns([1.5, 1.2, 1.5])
                    with ms1: score_a = st.number_input("A 점수", 0, 50, 0, key="m_sa", label_visibility="collapsed")
                    with ms3: score_b = st.number_input("B 점수", 0, 50, 0, key="m_sb", label_visibility="collapsed")
                    with ms2:
                        if st.button("저장", type="primary", use_container_width=True, key="m_btn"):
                            a_list = [x for x in [st.session_state.ma_1, st.session_state.ma_2] if x not in ["선택", "단식"]]
                            b_list = [x for x in [st.session_state.mb_1, st.session_state.mb_2] if x not in ["선택", "단식"]]
                            if not a_list or not b_list: st.error("선택 오류")
                            else:
                                win_res = "A팀 승리" if score_a > score_b else "B팀 승리" if score_b > score_a else "무승부"
                                pa_val, pb_val = "미지정", "미지정"
                                if ma_pos == "A-1" and len(a_list)>1: pa_val = f"{a_list[0]}(포) / {a_list[1]}(백)"
                                elif ma_pos == "A-2" and len(a_list)>1: pa_val = f"{a_list[1]}(포) / {a_list[0]}(백)"
                                if mb_pos == "B-1" and len(b_list)>1: pb_val = f"{b_list[0]}(포) / {b_list[1]}(백)"
                                elif mb_pos == "B-2" and len(b_list)>1: pb_val = f"{b_list[1]}(포) / {b_list[0]}(백)"

                                t_a = all_members_df[all_members_df['name'].isin(a_list)].to_dict('records')
                                t_b = all_members_df[all_members_df['name'].isin(b_list)].to_dict('records')
                                match_id = f"MANUAL_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                                a_str, b_str = ",".join(a_list), ",".join(b_list)
                                conn = get_db_conn()
                                try:
                                    conn.cursor().execute("INSERT INTO match_history (id, game_date, team_a, team_b, winner, score_a, score_b, team_a_pos, team_b_pos) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                                                          (match_id, active_date, a_str, b_str, win_res, int(score_a), int(score_b), pa_val, pb_val))
                                    conn.commit()
                                finally: conn.close()
                                assign_points_db(match_id, active_date, t_a, t_b, win_res, False, None, int(score_a), int(score_b))
                                st.success("완료!"); st.rerun()

                display_wait_counts_db(target_date=active_date)
        else:
            view_date = sel_opt.split(" ")[0]
            st.info(f"🔒 {view_date} 과거 기록 (수정 불가)")

# ----------------------------------------
# 2. 랭킹 조회
# ----------------------------------------
elif menu == "랭킹":
    conn = get_db_conn()
    try:
        df = pd.read_sql_query("SELECT name, input_date, points, games FROM points_log", conn)
        mh_df = pd.read_sql_query("SELECT id, game_date, team_a, team_b, winner, score_a, score_b FROM match_history WHERE winner != '입력 대기' AND winner != '취소'", conn)
    finally: conn.close()
    
    if df.empty: st.info("데이터가 없습니다.")
    else:
        df['month'] = df['input_date'].str[:7]
        available_months = sorted(df['month'].unique(), reverse=True)
        curr_m = datetime.now().strftime("%Y-%m")
        if curr_m not in available_months: available_months.insert(0, curr_m)
        
        c_rm1, c_rm2 = st.columns(2)
        with c_rm1: sel_month = st.selectbox("📅 년/월 선택", available_months, key="sel_month_rnk")
        with c_rm2: rank_type = st.radio("랭킹 기준", ["월간 랭킹", "누적 랭킹"], horizontal=True)
        st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
        
        df_curr = df[df['month'] == sel_month].copy()
        sorted_dates = sorted(df_curr['input_date'].unique())
        date_cols = []
        for d in sorted_dates:
            try: c_name = f"{datetime.strptime(d, '%Y-%m-%d').month}/{datetime.strptime(d, '%Y-%m-%d').day}"
            except: c_name = str(d)[-5:]
            if c_name not in date_cols: date_cols.append(c_name)

        members_df = get_members(exclude_guest=True)
        tot_stats = {n: {'w':0, 'l':0, 'd':0, 'diff':0} for n in members_df['name']}
        mon_stats = {n: {'w':0, 'l':0, 'd':0, 'diff':0} for n in members_df['name']}
        
        for _, m in mh_df.iterrows():
            ta, tb, winner = m['team_a'].split(','), m['team_b'].split(','), m['winner']
            sa = int(m['score_a']) if pd.notna(m['score_a']) else 0
            sb = int(m['score_b']) if pd.notna(m['score_b']) else 0
            m_month = m['game_date'][:7]
            for u in ta + tb:
                u = u.strip()
                if u not in tot_stats: continue
                u_team = 'A' if u in ta else 'B'
                is_win = (u_team == 'A' and winner == "A팀 승리") or (u_team == 'B' and winner == "B팀 승리")
                is_draw = (winner == "무승부")
                gd = (sa - sb) if u_team == 'A' else (sb - sa)
                
                if is_win: tot_stats[u]['w'] += 1
                elif is_draw: tot_stats[u]['d'] += 1
                else: tot_stats[u]['l'] += 1
                tot_stats[u]['diff'] += gd
                
                if m_month == sel_month:
                    if is_win: mon_stats[u]['w'] += 1
                    elif is_draw: mon_stats[u]['d'] += 1
                    else: mon_stats[u]['l'] += 1
                    mon_stats[u]['diff'] += gd

        records = []
        for name in members_df['name'].unique():
            user_df = df[df['name'] == name]
            if user_df.empty: continue
            
            tot_p, tot_g = user_df['points'].sum(), user_df['games'].sum()
            tot_avg = round(tot_p / tot_g, 1) if tot_g > 0 else 0
            mon_df = user_df[user_df['month'] == sel_month]
            mon_p, mon_g = mon_df['points'].sum(), mon_df['games'].sum()
            mon_avg = round(mon_p / mon_g, 1) if mon_g > 0 else 0
            
            record = {
                "이름": f"<b>{name}</b>",
                "월": f"<span class='pt-text'>{mon_p}점</span><br>{mon_avg}점<br>({mon_g}회)<br>{mon_stats[name]['w']}승<br>{mon_stats[name]['d']}무<br>{mon_stats[name]['l']}패",
                "누적": f"<span class='pt-text'>{tot_p}점</span><br>{tot_avg}점<br>({tot_g}회)<br>{tot_stats[name]['w']}승<br>{tot_stats[name]['d']}무<br>{tot_stats[name]['l']}패",
                "sort_score_mon": mon_p, "sort_score_tot": tot_p,
                "mon_diff": mon_stats[name]['diff'], "tot_diff": tot_stats[name]['diff'],
                "mon_w": mon_stats[name]['w'], "tot_w": tot_stats[name]['w'],
                "mon_l": mon_stats[name]['l'], "tot_l": tot_stats[name]['l']
            }
            
            for d, col_name in zip(sorted_dates, date_cols):
                daily_log = mon_df[mon_df['input_date'] == d]
                if not daily_log.empty:
                    pts = int(daily_log['points'].sum())
                    waits = len(daily_log[daily_log['games'] == 0])
                    wins, losses, draws = 0, 0, 0
                    for _, m in mh_df[mh_df['game_date'] == d].iterrows():
                        ta, tb = [x.strip() for x in m['team_a'].split(',')], [x.strip() for x in m['team_b'].split(',')]
                        if name in ta or name in tb:
                            if m['winner'] == "무승부": draws += 1
                            elif (name in ta and m['winner'] == "A팀 승리") or (name in tb and m['winner'] == "B팀 승리"): wins += 1
                            else: losses += 1
                    details = [f"<span class='pt-text'>{pts}점</span>"]
                    if wins > 0: details.append(f"{wins}승")
                    if losses > 0: details.append(f"{losses}패")
                    if draws > 0: details.append(f"{draws}무")
                    if waits > 0: details.append(f"대기{waits}")
                    record[col_name] = "<br>".join(details)
                else: record[col_name] = ""
            records.append(record)
            
        if not records: st.info("해당 기준에 데이터가 없습니다.")
        else:
            conn = get_db_conn()
            try:
                all_pts = pd.read_sql_query("SELECT * FROM points_log", conn)
                all_m = pd.read_sql_query("SELECT * FROM match_history WHERE winner != '입력 대기' AND winner != '취소'", conn)
            finally: conn.close()
            
            if rank_type == "월간 랭킹": all_pts = all_pts[all_pts['input_date'].str.startswith(sel_month)]
            render_realtime_podium(all_pts, all_m, min_games=1, title="🏆 이달의 탑 랭커" if rank_type == "월간 랭킹" else "🏆 누적 탑 랭커")

            final_df = pd.DataFrame(records)
            if rank_type == "월간 랭킹": final_df = final_df.sort_values(by=["sort_score_mon", "mon_diff", "mon_w", "mon_l"], ascending=[False, False, False, True])
            else: final_df = final_df.sort_values(by=["sort_score_tot", "tot_diff", "tot_w", "tot_l"], ascending=[False, False, False, True])
            
            final_df = final_df.drop(columns=['sort_score_mon', 'sort_score_tot', 'mon_diff', 'tot_diff', 'mon_w', 'tot_w', 'mon_l', 'tot_l'])
            final_df.insert(0, '순위', range(1, len(final_df) + 1))
            cols_order = ['순위', '이름'] + date_cols + ['월', '누적']
            final_df = final_df[cols_order]
            html_table = final_df.to_html(escape=False, index=False, justify='center', classes="rank-table")
            st.markdown(f"<div class='table-wrapper'>{html_table}</div>", unsafe_allow_html=True)

# ----------------------------------------
# 3. 개인별 분석
# ----------------------------------------
elif menu == "개인별 분석":
    st.subheader("📊 개인별 분석")
    regular_members_df = get_members(exclude_guest=True)
    if regular_members_df.empty: st.warning("등록된 정회원이 없습니다.")
    else:
        target_user = st.selectbox("분석할 회원 선택", regular_members_df['name'].tolist())
        if target_user:
            conn = get_db_conn()
            try:
                history_df = pd.read_sql_query("SELECT * FROM match_history WHERE winner != '입력 대기' AND winner != '취소'", conn)
                evt_history_df = pd.read_sql_query("SELECT * FROM event_matches WHERE winner != '입력 대기' AND winner != '취소'", conn)
            finally: conn.close()
            
            full_history = pd.concat([history_df, evt_history_df], ignore_index=True)
            
            if full_history.empty: st.info("저장된 기록이 없습니다.")
            else:
                my_wins, my_losses, my_draws = 0, 0, 0
                partner_stats, opponent_stats, opp_ind_stats = {}, {}, {}
                pos_stats = {'포': {'승':0, '패':0, '무':0, '득':0, '실':0}, '백': {'승':0, '패':0, '무':0, '득':0, '실':0}}
                
                for _, match in full_history.iterrows():
                    a_names, b_names, winner = match['team_a'].split(','), match['team_b'].split(','), match['winner']
                    pos_a, pos_b = match.get('team_a_pos', '🎾 포 지정'), match.get('team_b_pos', '🎾 포 지정')
                    sa = int(match['score_a']) if pd.notna(match['score_a']) else 0
                    sb = int(match['score_b']) if pd.notna(match['score_b']) else 0
                    
                    if target_user in a_names or target_user in b_names:
                        my_team = a_names if target_user in a_names else b_names
                        opp_team = b_names if target_user in a_names else a_names
                        partner = my_team[1] if len(my_team)>1 and my_team[0] == target_user else my_team[0]
                        opp_str = f"{opp_team[0]} & {opp_team[1]}" if len(opp_team)>1 else opp_team[0]
                        my_score = sa if target_user in a_names else sb
                        opp_score = sb if target_user in a_names else sa
                        
                        is_win = (target_user in a_names and winner == "A팀 승리") or (target_user in b_names and winner == "B팀 승리")
                        is_draw = (winner == "무승부")
                        if is_win: my_wins += 1; res_text = "🔵 승리"
                        elif is_draw: my_draws += 1; res_text = "⚪ 무승부"
                        else: my_losses += 1; res_text = "🔴 패배"
                        
                        my_pos = None
                        if target_user in a_names and target_user in pos_a:
                            if f"{target_user}(포)" in pos_a: my_pos = '포'
                            elif f"{target_user}(백)" in pos_a: my_pos = '백'
                        elif target_user in b_names and target_user in pos_b:
                            if f"{target_user}(포)" in pos_b: my_pos = '포'
                            elif f"{target_user}(백)" in pos_b: my_pos = '백'
                        if my_pos:
                            if is_win: pos_stats[my_pos]['승'] += 1
                            elif is_draw: pos_stats[my_pos]['무'] += 1
                            else: pos_stats[my_pos]['패'] += 1
                            pos_stats[my_pos]['득'] += my_score; pos_stats[my_pos]['실'] += opp_score
                        
                        if partner not in partner_stats: partner_stats[partner] = {'승':0, '패':0, '무':0, '득':0, '실':0, 'list':[]}
                        if is_win: partner_stats[partner]['승'] += 1
                        elif is_draw: partner_stats[partner]['무'] += 1
                        else: partner_stats[partner]['패'] += 1
                        partner_stats[partner]['득'] += my_score; partner_stats[partner]['실'] += opp_score
                        partner_stats[partner]['list'].append({"opp": opp_str, "res": res_text, "score": f"{my_score}:{opp_score}"})
                            
                        if opp_str not in opponent_stats: opponent_stats[opp_str] = {'승':0, '패':0, '무':0, '득':0, '실':0, 'list':[]}
                        if is_win: opponent_stats[opp_str]['승'] += 1
                        elif is_draw: opponent_stats[opp_str]['무'] += 1
                        else: opponent_stats[opp_str]['패'] += 1
                        opponent_stats[opp_str]['득'] += my_score; opponent_stats[opp_str]['실'] += opp_score
                        opponent_stats[opp_str]['list'].append({"partner": partner, "res": res_text, "score": f"{my_score}:{opp_score}"})

                        for opp_p in opp_team:
                            if opp_p not in opp_ind_stats: opp_ind_stats[opp_p] = {'승':0, '패':0, '무':0, '득':0, '실':0}
                            if is_win: opp_ind_stats[opp_p]['승'] += 1
                            elif is_draw: opp_ind_stats[opp_p]['무'] += 1
                            else: opp_ind_stats[opp_p]['패'] += 1
                            opp_ind_stats[opp_p]['득'] += my_score; opp_ind_stats[opp_p]['실'] += opp_score
                
                tot_games = my_wins + my_losses + my_draws
                if tot_games == 0: st.warning("분석할 경기 데이터가 없습니다.")
                else:
                    def get_best_worst(stats_dict):
                        rates = []
                        for k, v in stats_dict.items():
                            t = v['승'] + v['무'] + v['패']
                            diff = v['득'] - v['실']
                            if t > 0: rates.append({"name": k, "rate": v['승']/t, "avg_diff": diff/t, "tot": t, "w": v['승'], "d": v['무'], "l": v['패'], "diff": diff})
                        if not rates: return None, None
                        rates.sort(key=lambda x: (x['rate'], x['avg_diff'], x['tot']))
                        return rates[-1], rates[0] 

                    b_pt, w_pt = get_best_worst(partner_stats) 
                    b_op_tm, w_op_tm = get_best_worst(opponent_stats)
                    b_op_id, w_op_id = get_best_worst(opp_ind_stats)

                    st.success(f"**🥇 {target_user}님의 종합 전적: {tot_games}전 {my_wins}승 {my_draws}무 {my_losses}패 (승률 {round((my_wins/tot_games)*100,1)}%)**")
                    
                    st.markdown("#### 🎯 나의 상세 분석 리포트")
                    st.markdown("##### 🍯 베스트")
                    if b_pt:
                        with st.expander(f"🤝 찰떡 파트너: **{b_pt['name']}** (승률 {int(b_pt['rate']*100)}% / 평균 득실 +{b_pt['avg_diff']:.1f})"):
                            st.write(f"└ 함께 **{b_pt['tot']}전 {b_pt['w']}승 {b_pt['d']}무 {b_pt['l']}패** (총 득실차: {b_pt['diff']})를 기록했습니다.")
                    if b_op_tm:
                        with st.expander(f"💸 자판기(팀): **{b_op_tm['name']}** (승률 {int(b_op_tm['rate']*100)}% / 평균 득실 +{b_op_tm['avg_diff']:.1f})"):
                            st.write(f"└ 해당 팀을 만나 **{b_op_tm['tot']}전 {b_op_tm['w']}승 {b_op_tm['d']}무 {b_op_tm['l']}패** (총 득실차: {b_op_tm['diff']})를 기록했습니다.")
                    if b_op_id:
                        with st.expander(f"💸 자판기(개인): **{b_op_id['name']}** (승률 {int(b_op_id['rate']*100)}% / 평균 득실 +{b_op_id['avg_diff']:.1f})"):
                            st.write(f"└ 해당 선수를 상대로 **{b_op_id['tot']}전 {b_op_id['w']}승 {b_op_id['d']}무 {b_op_id['l']}패** (총 득실차: {b_op_id['diff']})를 기록했습니다.")

                    st.markdown("##### 👿 워스트")
                    if w_op_tm:
                        with st.expander(f"💢 천적(팀): **{w_op_tm['name']}** (승률 {int(w_op_tm['rate']*100)}% / 평균 득실 {w_op_tm['avg_diff']:.1f})"):
                            st.write(f"└ 해당 팀을 만나 **{w_op_tm['tot']}전 {w_op_tm['w']}승 {w_op_tm['d']}무 {w_op_tm['l']}패** (총 득실차: {w_op_tm['diff']})를 기록했습니다.")
                    if w_op_id:
                        with st.expander(f"💢 천적(개인): **{w_op_id['name']}** (승률 {int(w_op_id['rate']*100)}% / 평균 득실 {w_op_id['avg_diff']:.1f})"):
                            st.write(f"└ 해당 선수를 상대로 **{w_op_id['tot']}전 {w_op_id['w']}승 {w_op_id['d']}무 {w_op_id['l']}패** (총 득실차: {w_op_id['diff']})를 기록했습니다.")

                    st.divider()
                    st.markdown("#### 🏸 포지션별 득실 분석")
                    pf, pb = pos_stats['포'], pos_stats['백']
                    ptot, btot = pf['승']+pf['패']+pf['무'], pb['승']+pb['패']+pb['무']
                    prate = round((pf['승']/ptot)*100, 1) if ptot > 0 else 0
                    brate = round((pb['승']/btot)*100, 1) if btot > 0 else 0
                    p_avg_diff = (pf['득'] - pf['실'])/ptot if ptot > 0 else 0
                    b_avg_diff = (pb['득'] - pb['실'])/btot if btot > 0 else 0
                    st.info(f"**🔴 포(Fore):** 승률 {prate}% | 평균 득실 {p_avg_diff:+.1f} 점 ({pf['승']}승 {pf['무']}무 {pf['패']}패)")
                    st.error(f"**🔵 백(Back):** 승률 {brate}% | 평균 득실 {b_avg_diff:+.1f} 점 ({pb['승']}승 {pb['무']}무 {pb['패']}패)")

                    st.divider()
                    st.markdown("#### 🤝 파트너별 상세 기록")
                    sorted_pt = sorted(partner_stats.items(), key=lambda x: (x[1]['승']/(x[1]['승']+x[1]['무']+x[1]['패']), (x[1]['득']-x[1]['실'])), reverse=True)
                    for p_name, data in sorted_pt:
                        tot = data['승'] + data['무'] + data['패']
                        diff = data['득'] - data['실']
                        with st.expander(f"**{p_name}** | {data['승']}승 {data['무']}무 {data['패']}패 (득실 {diff:+.0f})"):
                            for item in data['list']: st.write(f"vs **{item['opp']}** ➔ {item['res']} ({item['score']})")
                    
                    st.markdown("#### ⚔️ 상대팀별 상세 기록")
                    sorted_op = sorted(opponent_stats.items(), key=lambda x: (x[1]['승']/(x[1]['승']+x[1]['무']+x[1]['패']), (x[1]['득']-x[1]['실'])), reverse=True)
                    for o_name, data in sorted_op:
                        tot = data['승'] + data['무'] + data['패']
                        diff = data['득'] - data['실']
                        with st.expander(f"**{o_name}** | {data['승']}승 {data['무']}무 {data['패']}패 (득실 {diff:+.0f})"):
                            for item in data['list']: st.write(f"with **{item['partner']}** ➔ {item['res']} ({item['score']})")

# ----------------------------------------
# 4. 이벤트 / 교류전
# ----------------------------------------
elif menu == "이벤트":
    st.markdown("<h3 style='color:#e65100; font-weight:900;'>🎉 이벤트 대진표</h3>", unsafe_allow_html=True)
    
    conn = get_db_conn()
    try: events_df = pd.read_sql_query("SELECT * FROM events ORDER BY id DESC", conn)
    finally: conn.close()
    
    if events_df.empty: st.info("관리자 메뉴에서 이벤트를 먼저 생성해주세요.")
    else:
        options = [f"[{row['event_date']}] {row['event_name']}" for _, row in events_df.iterrows()]
        
        c_opt1, c_opt2 = st.columns(2)
        with c_opt1: selected_event_str = st.selectbox("📌 이벤트 선택", options)
        
        idx = options.index(selected_event_str)
        selected_event = events_df.iloc[idx]
        e_id, e_type = int(selected_event['id']), selected_event.get('event_type', '개인전')
        
        part_str = selected_event.get('participants', "")
        raw_players = [x.strip() for x in part_str.split(",") if x.strip()] if part_str else get_members()['name'].tolist()
        clean_opts = []
        reg_df = get_members()
        for rp in raw_players:
            g = '여' if '(여)' in rp else '남'
            n = strip_gender(rp)
            m_df = reg_df[reg_df['name'] == n]
            if not m_df.empty: clean_opts.append(f"{n}({m_df.iloc[0]['gender']})")
            else: clean_opts.append(f"{n}({g})")
            
        event_players_opts = ["선택", "단식"] + clean_opts 
        
        view_mode = st.radio("보기 방식", ["개인별", "라운드별", "코트별"], horizontal=True, label_visibility="collapsed")
        with c_opt2: filter_name = st.selectbox("👤 선수 선택", [strip_gender(x) for x in clean_opts]) if view_mode == "개인별" else "전체 보기"
        st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
        
        conn = get_db_conn()
        try:
            pts_df = pd.read_sql_query("SELECT * FROM event_points_log WHERE event_id=?", conn, params=(e_id,))
            matches_check = pd.read_sql_query("SELECT * FROM event_matches WHERE event_id=? AND winner != '입력 대기' AND winner != '취소'", conn, params=(e_id,))
        finally: conn.close()
        
        rules = get_point_rules()
        min_games = int(rules.get('최소 게임수 (이벤트용)', {'win': 1})['win'])
        
        agg = render_realtime_podium(pts_df, matches_check, min_games=min_games, title="🏆 실시간 순위")
        
        b_json = selected_event.get('bracket_json', None)
        if pd.notna(b_json) and str(b_json).strip() not in ["", "None", "nan"]:
            try:
                st.session_state['event_tournament_data'] = json.loads(b_json)
                e_gen_params = json.loads(selected_event.get('gen_params_json', '{}'))
                evt_court_names = e_gen_params.get('court_names', [str(i+1) for i in range(20)])
                t_data = st.session_state['event_tournament_data']
                uniq_id = f"evt_{e_id}"
                
                conn = get_db_conn()
                try: all_ex_m = pd.read_sql_query("SELECT id, score_a, score_b, team_a_pos, team_b_pos FROM event_matches WHERE event_id=?", conn, params=(e_id,))
                finally: conn.close()

                if view_mode == "개인별":
                    for r_num, round_data in t_data.items():
                        render_horizontal_bracket(r_num, round_data, is_admin=False, filter_name=filter_name, is_event=True, event_id=e_id, target_date=selected_event['event_date'], court_names=evt_court_names)
                    display_missing_scores(t_data, True, e_id, selected_event['event_date'], uniq_id, all_ex_m, evt_court_names, filter_name)
                
                elif view_mode == "라운드별":
                    display_missing_scores(t_data, True, e_id, selected_event['event_date'], uniq_id, all_ex_m, evt_court_names, "전체 보기")
                    for r_num, round_data in t_data.items():
                        render_horizontal_bracket(r_num, round_data, is_admin=False, filter_name="전체 보기", is_event=True, event_id=e_id, target_date=selected_event['event_date'], court_names=evt_court_names)
                
                elif view_mode == "코트별":
                    display_missing_scores(t_data, True, e_id, selected_event['event_date'], uniq_id, all_ex_m, evt_court_names, "전체 보기")
                    courts_dict = {}
                    for r_num, round_data in t_data.items():
                        for c_idx, match in enumerate(round_data['matches']):
                            if match['winner'] == '취소': continue
                            if c_idx not in courts_dict: courts_dict[c_idx] = []
                            courts_dict[c_idx].append((r_num, match))
                    for c_idx in sorted(courts_dict.keys()):
                        c_name = evt_court_names[c_idx] if c_idx < len(evt_court_names) else str(c_idx+1)
                        with st.expander(f"🎾 [{c_name} 코트] 전체 매치", expanded=False):
                            for r_num, match in courts_dict[c_idx]: render_match_card(r_num, c_idx, match, False, "전체 보기", True, e_id, selected_event['event_date'], c_name, uniq_id, all_ex_m, auto_expand=False)
                                
            except Exception as e:
                st.error(f"대진표 에러. 관리자 메뉴에서 전체 다시 생성 요망. ({e})")

        if "팀 대항전" in e_type:
            conn = get_db_conn()
            try: t_matches_df = pd.read_sql_query("SELECT winner FROM event_matches WHERE event_id=? AND winner != '취소'", conn, params=(e_id,))
            finally: conn.close()
            t1, t2 = selected_event['team_1_name'] or "A팀", selected_event['team_2_name'] or "B팀"
            t1_wins = len(t_matches_df[t_matches_df['winner'] == 'A팀 승리'])
            t2_wins = len(t_matches_df[t_matches_df['winner'] == 'B팀 승리'])
            draws = len(t_matches_df[t_matches_df['winner'] == '무승부'])
            st.markdown(f"<div style='text-align:center; padding:15px; background-color:#1e293b; color:white; border-radius:10px; margin-bottom:20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>"
                        f"<p style='margin:0; font-size:12px; color:#94a3b8;'>팀 대항전 스코어 현황판</p>"
                        f"<h2 style='margin:5px 0; color:#38bdf8;'>{t1} <span style='color:white; font-size:30px;'>{t1_wins}</span> <span style='color:#64748b; font-size:20px;'>:</span> <span style='color:white; font-size:30px;'>{t2_wins}</span> <span style='color:#fb7185;'>{t2}</span></h2>"
                        f"<p style='margin:0; font-size:13px; color:#cbd5e1;'>무승부: {draws}</p></div>", unsafe_allow_html=True)
        
        if filter_name == "전체 보기":
            conn = get_db_conn()
            try: event_matches_df = pd.read_sql_query("SELECT * FROM event_matches WHERE event_id=?", conn, params=(e_id,))
            finally: conn.close()
            
            if not event_matches_df.empty:
                has_manual = any("_R" not in str(m['id']) for _, m in event_matches_df.iterrows())
                if has_manual:
                    st.markdown("#### 📜 직접 기록된 현장 매치")
                    for _, m in event_matches_df.iterrows():
                        if "_R" in str(m['id']): continue 
                        ta_str, tb_str = m['team_a'].replace(',', ' & '), m['team_b'].replace(',', ' & ')
                        display_winner = f"{ta_str} 승리" if m['winner'] == "A팀 승리" else f"{tb_str} 승리" if m['winner'] == "B팀 승리" else m['winner']
                        
                        st.markdown(f"""
                        <div style='display: flex; justify-content: space-between; align-items: center; background-color: #fff; padding: 10px 5px; border-radius: 5px; border: 1px solid #eee; margin-bottom: 5px;'>
                            <div class='wrap-text' style='flex: 1; text-align: right; font-size: 14px; font-weight: bold; color: #333;'>{ta_str}</div>
                            <div style='flex: 0 0 70px; text-align: center; font-size: 15px; font-weight: 900; color: {"#1976d2" if m['winner'] == 'A팀 승리' else "#d32f2f" if m['winner'] == 'B팀 승리' else "#757575"};'>
                                {"<br>".join([f"{m['score_a']}:{m['score_b']}"]) if m['score_a']>0 or m['score_b']>0 else display_winner}
                            </div>
                            <div class='wrap-text' style='flex: 1; text-align: left; font-size: 14px; font-weight: bold; color: #333;'>{tb_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        cd1, cd2, cd3 = st.columns([1, 1, 1])
                        with cd2:
                            del_key_evt = f"c_del_evt_{m['id']}"
                            if del_key_evt not in st.session_state: st.session_state[del_key_evt] = False
                            if not st.session_state[del_key_evt]:
                                if st.button("❌ 삭제", key=f"d_ev_{m['id']}", use_container_width=True): st.session_state[del_key_evt] = True; st.rerun()
                            else:
                                st.markdown("<div class='nowrap-text' style='text-align:center; font-weight:bold; font-size:13px; color:#d32f2f; margin-bottom:3px;'>⚠️ 삭제 확인</div>", unsafe_allow_html=True)
                                cy, cn = st.columns(2)
                                with cy:
                                    if st.button("확인", key=f"dy_{m['id']}", type="primary", use_container_width=True):
                                        conn = get_db_conn()
                                        try:
                                            conn.cursor().execute("DELETE FROM event_matches WHERE id=?", (m['id'],))
                                            conn.cursor().execute("DELETE FROM event_points_log WHERE match_id=?", (m['id'],))
                                            conn.commit()
                                        finally: conn.close()
                                        st.session_state[del_key_evt] = False; st.rerun()
                                with cn:
                                    if st.button("취소", key=f"dn_{m['id']}", use_container_width=True): st.session_state[del_key_evt] = False; st.rerun()
                        st.markdown("<hr style='margin:3px 0; border-top:1px dashed #eee;'>", unsafe_allow_html=True)

            with st.expander("➕ 현장 게임 추가 등록", expanded=False):
                st.markdown("<div style='text-align:center; font-size:15px; font-weight:bold; color:#d32f2f; margin-bottom:8px;'>🔥 현장 추가 매치</div>", unsafe_allow_html=True)
                pos_opts_a, pos_opts_b = ["🎾 포 지정", "A-1", "A-2"], ["🎾 포 지정", "B-1", "B-2"]
                
                m_col1, m_col2 = st.columns(2)
                with m_col1:
                    st.markdown("<div class='team-box-a' style='min-height:30px; padding:5px;'><div style='font-size: 13px; color: #2e7d32; font-weight: bold;'>A팀 배정</div></div>", unsafe_allow_html=True)
                    ea1 = st.selectbox("A-1", event_players_opts, key='i_ea1')
                    ea2 = st.selectbox("A-2 (단식 비움)", ["선택", "단식"] + event_players_opts[1:], key='i_ea2')
                with m_col2:
                    st.markdown("<div class='team-box-b' style='min-height:30px; padding:5px;'><div style='font-size: 13px; color: #1565c0; font-weight: bold;'>B팀 배정</div></div>", unsafe_allow_html=True)
                    eb1 = st.selectbox("B-1", event_players_opts, key='i_eb1')
                    eb2 = st.selectbox("B-2 (단식 비움)", ["선택", "단식"] + event_players_opts[1:], key='i_eb2')
                
                st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                cp1, cp2 = st.columns(2)
                with cp1: ma_pos = st.selectbox("A포지정", pos_opts_a, key="ma_pos", label_visibility="collapsed")
                with cp2: mb_pos = st.selectbox("B포지정", pos_opts_b, key="mb_pos", label_visibility="collapsed")
                    
                ms1, ms2, ms3 = st.columns([1.5, 1.2, 1.5])
                with ms1: score_a = st.number_input("A 점수", 0, 50, 0, key="me_sa", label_visibility="collapsed")
                with ms3: score_b = st.number_input("B 점수", 0, 50, 0, key="me_sb", label_visibility="collapsed")
                with ms2:
                    if st.button("저장", type="primary", use_container_width=True, key="me_btn"):
                        a_players = [strip_gender(x) for x in [st.session_state.i_ea1, st.session_state.i_ea2] if x not in ["선택", "단식"]]
                        b_players = [strip_gender(x) for x in [st.session_state.i_eb1, st.session_state.i_eb2] if x not in ["선택", "단식"]]
                        if not a_players or not b_players: st.error("양 팀 선수를 선택해주세요.")
                        else:
                            win_res = "A팀 승리" if score_a > score_b else "B팀 승리" if score_b > score_a else "무승부"
                            pa_val, pb_val = "미지정", "미지정"
                            if ma_pos == "A-1" and len(a_list)>1: pa_val = f"{a_list[0]}(포) / {a_list[1]}(백)"
                            elif ma_pos == "A-2" and len(a_list)>1: pa_val = f"{a_list[1]}(포) / {a_list[0]}(백)"
                            if mb_pos == "B-1" and len(b_list)>1: pb_val = f"{b_list[0]}(포) / {b_list[1]}(백)"
                            elif mb_pos == "B-2" and len(b_list)>1: pb_val = f"{b_list[1]}(포) / {b_list[0]}(백)"

                            match_id = f"EVT_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            a_str, b_str = ",".join(a_players), ",".join(b_players)
                            conn = get_db_conn()
                            try:
                                conn.cursor().execute("INSERT INTO event_matches (id, event_id, round, court, team_a, team_b, winner, score_a, score_b, team_a_pos, team_b_pos) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                                                      (match_id, e_id, 0, 0, a_str, b_str, win_res, int(score_a), int(score_b), "미지정", "미지정"))
                                conn.commit()
                            finally: conn.close()
                            def get_p_dict(n):
                                match_df = reg_df[reg_df['name']==n]
                                return match_df.iloc[0].to_dict() if not match_df.empty else {'name': str(n), 'gender': '남', 'eff_rating': 5.0, 'is_guest': 1}
                            assign_points_db(match_id, selected_event['event_date'], [get_p_dict(n) for n in a_players], [get_p_dict(n) for n in b_players], win_res, True, e_id, int(score_a), int(score_b))
                            st.success("저장 완료!"); st.rerun()

            display_wait_counts_db(event_id=e_id)

        if not matches_check.empty and not agg.empty and '순위' in agg.columns:
            st.divider()
            st.markdown("### 📊 상세 성적표")
            final_table = agg[['순위', 'name', '경기수', '승점', '평균승점', '승', '패', '무', '승률', '득점', '득실차', '평균득실차', '자격미달']].copy()
            final_table['승-무-패'] = final_table.apply(lambda x: f"{int(x['승'])}-{int(x['무'])}-{int(x['패'])}", axis=1)
            final_table = final_table[['순위', 'name', '경기수', '승점', '평균승점', '승-무-패', '승률', '득점', '득실차', '평균득실차', '자격미달']]
            final_table.columns = ['순위', '이름', '게임수', '총승점', '평균승점', '승-무-패', '승률', '총득점', '총득실차', '평균득실', '자격미달']
            def style_disqualified(row): return ['color: #9e9e9e; text-decoration: line-through;'] * len(row) if final_table.loc[row.name, '자격미달'] else [''] * len(row)
            styled_table = final_table.drop(columns=['자격미달']).style.apply(style_disqualified, axis=1)
            st.dataframe(styled_table, use_container_width=True, hide_index=True)
            st.caption(f"※ 최소 게임수({min_games}게임) 미달자는 순위 산정에서 밀리며, 회색 취소선으로 표시됩니다.")

# ----------------------------------------
# 5. 관리자 메뉴
# ----------------------------------------
elif menu == "관리자":
    st.subheader("⚙️ 관리자 시스템")
    if not st.session_state['admin_logged_in']:
        if st.text_input("비밀번호 (초기: 1234)", type="password") == get_admin_pwd(): st.session_state['admin_logged_in'] = True; st.rerun()
                
    if st.session_state['admin_logged_in']:
        if st.button("로그아웃"): st.session_state['admin_logged_in'] = False; st.rerun()
        
        tab_reg, tab_evt = st.tabs(["🎾 정규 리그 관리", "🎉 이벤트/교류전 관리"])
        
        with tab_evt:
            st.markdown("#### ✨ 1. 이벤트 방 기본 설정 및 참가자 등록")
            e_date = st.date_input("📅 이벤트 날짜", datetime.now()).strftime("%Y-%m-%d")
            e_name = st.text_input("📌 이벤트 이름 (예: 3월 월례대회)")
            e_type = st.radio("🏆 이벤트 방식", ["개인전 (월례대회/자체전)", "팀 대항전 (교류전/청백전)"], horizontal=True)

            with st.expander("🛠️ 승점 부여 방식 및 최소 게임수 수정", expanded=False):
                conn = get_db_conn()
                try: rules_df = pd.read_sql_query("SELECT category as '구분', win as '승', lose as '패', draw as '무승부' FROM point_rules", conn)
                finally: conn.close()
                edited_df = st.data_editor(rules_df, hide_index=True, use_container_width=True, key="evt_rules_editor_admin")
                if st.button("변경한 설정 저장", key="btn_evt_rules_admin"):
                    conn = get_db_conn()
                    try:
                        for _, row in edited_df.iterrows(): conn.cursor().execute("UPDATE point_rules SET win=?, lose=?, draw=? WHERE category=?", (row['승'], row['패'], row['무승부'], row['구분']))
                        conn.commit()
                    finally: conn.close()
                    st.success("저장 완료!")

            all_members_df = get_members()
            all_members_names = [f"{r['name']}({r['gender']})" + ("(G)" if r['is_guest'] else "") for _, r in all_members_df.iterrows()]
            
            if 'evt_selected_names' not in st.session_state: st.session_state.evt_selected_names = []
            
            st.markdown("##### ✔️ 참가할 핫테 회원 선택")
            cols = st.columns(3)
            for idx, row in all_members_df.iterrows():
                with cols[idx % 3]:
                    c_name = f"{row['name']}({row['gender']})" + ("(G)" if row['is_guest'] else "")
                    if st.checkbox(c_name, value=True, key=f"chk_evt_{idx}_{row['name']}"):
                        if c_name not in st.session_state.evt_selected_names: st.session_state.evt_selected_names.append(c_name)
                    else:
                        if c_name in st.session_state.evt_selected_names: st.session_state.evt_selected_names.remove(c_name)

            with st.expander("➕ 외부 게스트 추가 등록", expanded=False):
                c_g1, c_g2, c_g3, c_g4 = st.columns([2, 1.2, 1.5, 1.2])
                with c_g1: g_name = st.text_input("이름", key="evt_g_name")
                with c_g2: g_gender = st.selectbox("성별", ["남", "여"], key="evt_g_gender")
                with c_g3: g_rating = st.number_input("평점", min_value=1.0, max_value=10.0, value=5.0, step=0.1, key="evt_g_rating")
                with c_g4:
                    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                    if st.button("추가", key="evt_g_save", type="primary", use_container_width=True):
                        if g_name:
                            conn = get_db_conn()
                            try:
                                conn.cursor().execute("INSERT INTO members (name, gender, base_rating, is_active, is_guest) VALUES (?, ?, ?, 1, 1)", (g_name, g_gender, g_rating))
                                conn.commit()
                            finally: conn.close()
                            
                            new_member = f"{g_name}({g_gender})(G)"
                            if new_member not in st.session_state.evt_selected_names:
                                st.session_state.evt_selected_names.append(new_member)
                            st.success(f"{g_name} 추가됨! 참가자 명단에 자동 반영됩니다."); st.rerun()

            st.divider()
            st.markdown("#### ✨ 2. 참가자 명단 확인 및 평점 조정")
            reg_df, e_member_dicts = get_members(), []
            m_cnt, f_cnt = 0, 0
            for i, item in enumerate(st.session_state.evt_selected_names):
                item = item.strip()
                if not item: continue
                n = strip_gender(item)
                match_df = reg_df[reg_df['name'] == n]
                if not match_df.empty:
                    gen = match_df.iloc[0]['gender']
                    if gen == '남': m_cnt += 1
                    else: f_cnt += 1
                    e_member_dicts.append({"NO": i+1, "이름": n, "성별": gen, "구분": "정회원" if match_df.iloc[0]['is_guest']==0 else "게스트", "평점": float(match_df.iloc[0]['eff_rating'])})
            
            df_e_players = pd.DataFrame(e_member_dicts) if e_member_dicts else pd.DataFrame(columns=["NO", "이름", "성별", "구분", "평점"])
            st.markdown(f"<div style='font-size:14px; font-weight:bold; color:#1976d2; margin-bottom:5px;'>총 {len(e_member_dicts)}명 (남성: {m_cnt}명 / 여성: {f_cnt}명)</div>", unsafe_allow_html=True)
            st.caption("선택된 인원만 아래에 표시됩니다. 현장 상황에 맞게 밸런스 점수를 조절하세요.")
            
            edited_evt_df = st.data_editor(
                df_e_players, 
                column_config={"NO": st.column_config.NumberColumn("NO", disabled=True), "이름": st.column_config.TextColumn("이름", disabled=True), "성별": st.column_config.TextColumn("성별", disabled=True), "구분": st.column_config.TextColumn("구분", disabled=True), "평점": st.column_config.NumberColumn("평점(1~10)", min_value=1.0, max_value=10.0, step=0.1)}, 
                hide_index=True, use_container_width=True, key="evt_player_editor_admin"
            )
            
            st.divider()
            st.markdown("#### ✨ 3. 팀 배정 및 방 생성")
            adj_opts = [f"{row['이름']}({row['성별']})" for _, row in edited_evt_df.iterrows()] if not edited_evt_df.empty else []
            final_selected_e = edited_evt_df['이름'].tolist() if not edited_evt_df.empty else []
            
            t1_name, t2_name, t1_members, t2_members, selected_members = "A팀", "B팀", [], [], []
            if "팀 대항전" in e_type:
                st.caption("※ A팀원을 선택하면 B팀원 목록에서는 자동으로 제외됩니다.")
                c1, c2 = st.columns(2)
                with c1: 
                    t1_name = st.text_input("A팀 이름 (예: 청팀)", value="A팀")
                    t1_members = st.multiselect("A팀 소속 팀원", adj_opts)
                with c2: 
                    t2_name = st.text_input("B팀 이름 (예: 백팀)", value="B팀")
                    avail_t2 = [x for x in adj_opts if x not in t1_members]
                    t2_members = st.multiselect("B팀 소속 팀원", avail_t2)
            else:
                selected_members = st.multiselect("개인전 참석자", adj_opts, default=adj_opts)
                
            if st.button("위 설정으로 새 이벤트 방 생성", use_container_width=True, type="primary"):
                if e_name and final_selected_e:
                    final_participants = list(set([strip_gender(x) for x in t1_members + t2_members])) if "팀 대항전" in e_type else [strip_gender(x) for x in selected_members]
                    part_str = ",".join(final_participants)
                    t1_str = ",".join([strip_gender(x) for x in t1_members])
                    t2_str = ",".join([strip_gender(x) for x in t2_members])
                    
                    custom_ratings = {row['이름']: row['평점'] for _, row in edited_evt_df.iterrows()}
                    conn = get_db_conn()
                    try:
                        conn.cursor().execute("INSERT INTO events (event_date, event_name, event_type, team_1_name, team_2_name, team_1_members, team_2_members, participants, gen_params_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                                              (e_date, e_name, e_type, t1_name, t2_name, t1_str, t2_str, part_str, json.dumps({'custom_ratings': custom_ratings})))
                        conn.commit()
                    finally: conn.close()
                    st.session_state.evt_selected_names = []
                    st.success(f"'{e_name}' 방이 생성되었습니다! 아래에서 대진표를 뽑으세요."); st.rerun()
                else: st.error("이벤트 이름을 입력하고 참가자를 1명 이상 배정해주세요.")
            
            st.divider()
            st.markdown("#### 🚀 4. 기존 이벤트 대진표 생성 및 관리")
            conn = get_db_conn()
            try: events_df = pd.read_sql_query("SELECT * FROM events ORDER BY id DESC", conn)
            finally: conn.close()
            
            if events_df.empty: st.warning("위에서 이벤트를 먼저 만들어주세요.")
            else:
                options = [f"[{row['event_date']}] {row['event_name']}" for _, row in events_df.iterrows()]
                selected_event_str = st.selectbox("적용할 이벤트 방 선택", options, key="evt_sel_for_gen_admin")
                idx = options.index(selected_event_str)
                selected_event = events_df.iloc[idx]
                e_id, is_team_match = int(selected_event['id']), "팀 대항전" in selected_event.get('event_type', '')
                
                e_gen_params = json.loads(selected_event.get('gen_params_json', '{}'))
                custom_ratings = e_gen_params.get('custom_ratings', {})
                part_str = selected_event.get('participants', "")
                raw_players = [x.strip() for x in part_str.split(",") if x.strip()] if part_str else []
                
                reg_df, e_member_dicts = get_members(), []
                for n in raw_players:
                    match_df = reg_df[reg_df['name'] == n]
                    if not match_df.empty:
                        rating = custom_ratings.get(n, float(match_df.iloc[0]['eff_rating']))
                        e_member_dicts.append({"name": n, "gender": match_df.iloc[0]['gender'], "eff_rating": rating, "is_guest": match_df.iloc[0]['is_guest']})
                
                active_e_members_df = pd.DataFrame(e_member_dicts)
                final_selected_e = active_e_members_df['name'].tolist() if not active_e_members_df.empty else []
                
                st.info(f"실제 대진표 투입: **{len(final_selected_e)}명** (생성 시 저장한 평점이 자동 적용됩니다)")
                
                ce1, ce2, ce3 = st.columns([1, 1, 1])
                with ce1: e_play_mode = st.radio("경기 방식", ["복식", "단식"], horizontal=True, key="e_play_mode_admin")
                with ce2: e_r_cnt = st.number_input("라운드 수", 1, 20, 4, key="e_r_cnt_admin")
                with ce3: 
                    e_court_input = st.text_input("사용 코트 (쉼표구분)", "1,2", key="e_c_cnt_admin")
                    e_court_names = [c.strip() for c in e_court_input.split(",") if c.strip()]
                    e_c_cnt = len(e_court_names)
                
                e_opt, e_sub_opt, e_spec = "기본 (평점 우선)", "기본 (평점 우선)", []
                if e_play_mode == "복식" and not is_team_match:
                    cx1, cx2 = st.columns(2)
                    with cx1: e_opt = st.selectbox("1차 기준", ["기본 (평점 우선)", "혼복 우선", "여복 우선", "팀 상관없이 혼복우선", "특정 페어 우선", "특정팀 대결 우선"], key="e_opt_admin")
                    with cx2: 
                        if e_opt in ["특정 페어 우선", "특정팀 대결 우선"]: e_sub_opt = st.selectbox("2차 기준", ["기본 (평점 우선)", "혼복 우선", "여복 우선"], key="e_sub_opt_admin")
                    
                    if e_opt == "특정 페어 우선":
                        for i in range(st.session_state['e_pair_count']):
                            c_p1, c_p2 = st.columns(2)
                            with c_p1: p1_a = st.selectbox(f"페어{i+1}-선수1", ["선택"] + final_selected_e, key=f"admin_ep1_a_{i}")
                            with c_p2: p1_b = st.selectbox(f"페어{i+1}-선수2", ["선택"] + final_selected_e, key=f"admin_ep1_b_{i}")
                            if p1_a != "선택" and p1_b != "선택": e_spec.append((strip_gender(p1_a), strip_gender(p1_b)))
                        cb1, cb2 = st.columns(2)
                        with cb1: 
                            if st.button("➕ 페어 추가"): st.session_state['e_pair_count']+=1; st.rerun()
                        with cb2: 
                            if st.session_state['e_pair_count']>1 and st.button("➖ 줄이기"): st.session_state['e_pair_count']-=1; st.rerun()
                    elif e_opt == "특정팀 대결 우선":
                        for i in range(st.session_state['e_team_count']):
                            c_t1, c_t2, c_t3, c_t4 = st.columns(4)
                            with c_t1: ta1 = st.selectbox(f"A-1", ["선택"]+final_selected_e, key=f"admin_eta1_{i}")
                            with c_t2: ta2 = st.selectbox(f"A-2", ["선택"]+final_selected_e, key=f"admin_eta2_{i}")
                            with c_t3: tb1 = st.selectbox(f"매치{i+1}-B1", ["선택"]+final_selected_e, key=f"admin_etb1_{i}")
                            with c_t4: tb2 = st.selectbox(f"매치{i+1}-B2", ["선택"]+final_selected_e, key=f"admin_etb2_{i}")
                            if "선택" not in [ta1, ta2, tb1, tb2]: e_spec.append(((strip_gender(ta1), strip_gender(ta2)), (strip_gender(tb1), strip_gender(tb2))))
                        cb1, cb2 = st.columns(2)
                        with cb1: 
                            if st.button("➕ 대결 추가"): st.session_state['e_team_count']+=1; st.rerun()
                        with cb2: 
                            if st.session_state['e_team_count']>1 and st.button("➖ 줄이기"): st.session_state['e_team_count']-=1; st.rerun()
                elif is_team_match: st.info("💡 팀 대항전 모드로, 생성 시 자동으로 A팀 명단과 B팀 명단끼리 대결하게 짜여집니다.")
                else: e_opt = "단식"

                if 'gen_confirm_evt_admin' not in st.session_state: st.session_state.gen_confirm_evt_admin = False
                conn = get_db_conn()
                try: existing_e_matches = pd.read_sql_query("SELECT COUNT(*) FROM event_matches WHERE event_id=?", conn, params=(e_id,)).iloc[0,0]
                finally: conn.close()

                if st.button("🔥 스위치 온 (전체 라운드 대진표 생성)", type="primary", use_container_width=True, key="btn_evt_gen_start_admin"):
                    if existing_e_matches > 0: st.session_state.gen_confirm_evt_admin = True
                    else:
                        st.session_state.gen_confirm_evt_admin = False
                        evt_team_rosters = {'A': [strip_gender(n) for n in str(selected_event.get('team_1_members', '')).split(',') if n], 'B': [strip_gender(n) for n in str(selected_event.get('team_2_members', '')).split(',') if n]} if is_team_match else None
                            
                        new_bracket = {}
                        for r in range(1, e_r_cnt + 1): new_bracket[str(r)] = generate_single_round(active_e_members_df.copy(), e_c_cnt, e_play_mode, e_opt, e_spec, e_sub_opt, r, new_bracket, team_rosters=evt_team_rosters)
                        
                        rules = get_point_rules()
                        conn = get_db_conn()
                        try:
                            for r_str, r_data in new_bracket.items():
                                wl_id = f"EVT{e_id}_R{r_str}_Waitlist"
                                for w in r_data['waitlist']: conn.cursor().execute("INSERT INTO event_points_log (event_id, name, points, games, match_id, result) VALUES (?, ?, ?, ?, ?, ?)", (e_id, str(w['name']), rules.get('대기자', {'win':2})['win'], 0, wl_id, '대기'))
                            e_gen_params['c_cnt'] = e_c_cnt
                            e_gen_params['court_names'] = e_court_names
                            e_gen_params['play_mode'] = e_play_mode
                            e_gen_params['opt'] = e_opt
                            e_gen_params['sub_opt'] = e_sub_opt
                            e_gen_params['spec'] = e_spec
                            e_gen_params['selected_names'] = final_selected_e
                            conn.cursor().execute("UPDATE events SET bracket_json=?, gen_params_json=? WHERE id=?", (json.dumps(new_bracket, default=str), json.dumps(e_gen_params), e_id))
                            conn.commit()
                        finally: conn.close()
                        st.success("생성 완료! [이벤트] 탭으로 이동하세요."); st.rerun()

                if st.session_state.gen_confirm_evt_admin:
                    st.markdown("<div class='nowrap-text' style='text-align:center; font-weight:bold; font-size:14px; color:#d32f2f; margin-bottom:5px;'>⚠️ 이미 대진표가 존재합니다. 삭제하고 다시 생성할까요?</div>", unsafe_allow_html=True)
                    c_yes, c_no = st.columns([1, 1])
                    with c_yes:
                        if st.button("확인", use_container_width=True, key="btn_evt_gen_confirm_admin"):
                            conn = get_db_conn()
                            try:
                                conn.cursor().execute("DELETE FROM event_matches WHERE event_id=? AND id LIKE '%_R%'", (e_id,))
                                conn.cursor().execute("DELETE FROM event_points_log WHERE match_id LIKE '%_R%'")
                                conn.commit()
                            finally: conn.close()
                            
                            evt_team_rosters = {'A': [strip_gender(n) for n in str(selected_event.get('team_1_members', '')).split(',') if n], 'B': [strip_gender(n) for n in str(selected_event.get('team_2_members', '')).split(',') if n]} if is_team_match else None
                            new_bracket = {}
                            for r in range(1, e_r_cnt + 1): new_bracket[str(r)] = generate_single_round(active_e_members_df.copy(), e_c_cnt, e_play_mode, e_opt, e_spec, e_sub_opt, r, new_bracket, team_rosters=evt_team_rosters)
                            
                            rules = get_point_rules()
                            conn = get_db_conn()
                            try:
                                for r_str, r_data in new_bracket.items():
                                    wl_id = f"EVT{e_id}_R{r_str}_Waitlist"
                                    for w in r_data['waitlist']: conn.cursor().execute("INSERT INTO event_points_log (event_id, name, points, games, match_id, result) VALUES (?, ?, ?, ?, ?, ?)", (e_id, str(w['name']), rules.get('대기자', {'win':2})['win'], 0, wl_id, '대기'))
                                e_gen_params['c_cnt'] = e_c_cnt
                                e_gen_params['court_names'] = e_court_names
                                e_gen_params['play_mode'] = e_play_mode
                                e_gen_params['opt'] = e_opt
                                e_gen_params['sub_opt'] = e_sub_opt
                                e_gen_params['spec'] = e_spec
                                e_gen_params['selected_names'] = final_selected_e
                                conn.cursor().execute("UPDATE events SET bracket_json=?, gen_params_json=? WHERE id=?", (json.dumps(new_bracket, default=str), json.dumps(e_gen_params), e_id))
                                conn.commit()
                            finally: conn.close()
                            st.session_state.gen_confirm_evt_admin = False; st.success("생성 완료! [이벤트] 탭으로 이동하세요."); st.rerun()
                    with c_no:
                        if st.button("취소", use_container_width=True, key="btn_evt_gen_cancel_admin"): st.session_state.gen_confirm_evt_admin = False; st.rerun()
                            
            b_json = selected_event.get('bracket_json')
            if pd.notna(b_json) and str(b_json).strip() not in ["", "None", "nan"]:
                st.markdown("<br><h3 style='color:#1976D2;'>👇 생성된 이벤트 대진표 관리 (라운드 단일 재생성/인원 교체)</h3>", unsafe_allow_html=True)
                st.session_state['event_tournament_data'] = json.loads(b_json)
                e_gen_json = selected_event.get('gen_params_json')
                e_gen = json.loads(e_gen_json) if e_gen_json and pd.notna(e_gen_json) else None
                
                for r_num, round_data in st.session_state['event_tournament_data'].items():
                    render_horizontal_bracket(r_num, round_data, is_admin=True, filter_name="전체 보기", is_event=True, event_id=e_id, target_date=selected_event['event_date'], court_names=e_gen.get('court_names') if e_gen else None)
        
        with tab_reg:
            with st.expander("⚠️ 데이터 초기화 (테스트 기록 삭제)", expanded=False):
                st.warning("지금까지 입력된 모든 대진표, 경기 결과, 승점(과거 엑셀 데이터 포함)이 영구적으로 삭제됩니다.")
                confirm_reset = st.checkbox("네, 모든 데이터를 삭제하는 것에 동의합니다.", key="reg_reset_chk")
                if confirm_reset:
                    if st.button("🔥 전체 데이터 초기화 실행", type="primary", use_container_width=True, key="reg_reset_btn"):
                        conn = get_db_conn()
                        try:
                            c = conn.cursor()
                            c.execute("DELETE FROM match_history")
                            c.execute("DELETE FROM points_log")
                            c.execute("DELETE FROM event_matches")
                            c.execute("DELETE FROM event_points_log")
                            c.execute("DELETE FROM events")
                            c.execute("DELETE FROM settings WHERE key IN ('active_match_date', 'active_tournament_json', 'active_gen_params_json')")
                            conn.commit()
                        finally: conn.close()
                        st.session_state['tournament_data'] = {}
                        st.session_state['gen_params'] = None
                        st.success("테스트 데이터가 완벽하게 삭제되었습니다!"); st.rerun()
                        
            with st.expander("📥 과거 데이터(엑셀) 일괄 업로드", expanded=False):
                st.info("이전에 사용하던 엑셀 데이터를 업로드하여 랭킹에 합산할 수 있습니다.")
                st.markdown("**[필수 엑셀 양식]** 첫 줄(헤더)에 아래 4개 항목을 정확히 적어주세요.\n* `날짜` (예: 2025-12-01) | `이름` | `승점` | `게임수`")
                uploaded_file = st.file_uploader("엑셀 파일 첨부 (.xlsx, .xls)", type=["xlsx", "xls"], key="reg_file_up")
                if uploaded_file is not None:
                    if st.button("데이터 업로드 실행", type="primary", use_container_width=True, key="reg_file_btn"):
                        try:
                            df_up = pd.read_excel(uploaded_file)
                            req_cols = ['날짜', '이름', '승점', '게임수']
                            if not all(c in df_up.columns for c in req_cols): st.error("엑셀 양식이 맞지 않습니다. 열(Column) 이름을 확인해주세요.")
                            else:
                                conn = get_db_conn()
                                try:
                                    c = conn.cursor()
                                    c.execute("DELETE FROM points_log WHERE source_id='EXCEL_IMPORT'")
                                    for _, row in df_up.iterrows():
                                        if pd.notna(row['이름']) and pd.notna(row['승점']):
                                            date_str = str(row['날짜'])[:10]
                                            c.execute("INSERT INTO points_log (source_id, name, input_date, points, games) VALUES (?, ?, ?, ?, ?)", ('EXCEL_IMPORT', str(row['이름']), date_str, int(row['승점']), int(row['게임수'])))
                                    conn.commit()
                                finally: conn.close()
                                st.success("🎉 병합 완료!")
                        except Exception as e: st.error(f"엑셀 에러: {e}")

            with st.expander("🛠️ 승점 부여 방식 설정", expanded=False):
                conn = get_db_conn()
                try: rules_df = pd.read_sql_query("SELECT category as '구분', win as '승', lose as '패', draw as '무승부' FROM point_rules", conn)
                finally: conn.close()
                edited_df = st.data_editor(rules_df, hide_index=True, use_container_width=True, key="reg_rule_editor")
                if st.button("변경한 승점 저장", key="btn_reg_rules"):
                    conn = get_db_conn()
                    try:
                        c = conn.cursor()
                        for _, row in edited_df.iterrows(): c.execute("UPDATE point_rules SET win=?, lose=?, draw=? WHERE category=?", (row['승'], row['패'], row['무승부'], row['구분']))
                        conn.commit()
                    finally: conn.close()
                    st.success("저장 완료!")

            with st.expander("👥 회원 명부 및 관리 (등록/삭제/승급)", expanded=False):
                members_df = get_members()
                reg_df = members_df[members_df['is_guest'] == 0][['name', 'gender', 'base_rating', 'eff_rating']].copy()
                gst_df = members_df[members_df['is_guest'] == 1][['name', 'gender', 'base_rating', 'eff_rating']].copy()
                reg_df.columns = ['이름', '성별', '초기평점', '적용평점(실제)']
                gst_df.columns = ['이름', '성별', '초기평점', '적용평점(실제)']
                st.markdown("##### 👑 정회원 명단")
                st.dataframe(reg_df, hide_index=True, use_container_width=True)
                st.markdown("##### 🏃‍♂️ 게스트 명단")
                st.dataframe(gst_df, hide_index=True, use_container_width=True)
                
                st.divider()
                st.markdown("##### ➕ 신규 등록")
                c_reg1, c_reg2 = st.columns(2)
                with c_reg1: new_n, new_g = st.text_input("이름", key="reg_new_name"), st.selectbox("성별", ["남", "여"], key="reg_new_gender")
                with c_reg2: new_r, is_guest = st.number_input("초기 평점", value=5.0, key="reg_new_rating"), st.checkbox("게스트로 등록", key="reg_new_guest")
                if st.button("신규 회원 추가", type="primary", use_container_width=True, key="reg_new_btn"):
                    if new_n:
                        conn = get_db_conn()
                        try:
                            conn.cursor().execute("INSERT INTO members (name, gender, base_rating, is_active, is_guest) VALUES (?, ?, ?, 1, ?)", (new_n, new_g, new_r, 1 if is_guest else 0))
                            conn.commit()
                        finally: conn.close()
                        st.rerun()
                        
                st.divider()
                st.markdown("##### 🔄 게스트 ➔ 정회원 승급 (전적 소급)")
                gst_names = gst_df['이름'].tolist()
                up_g = st.selectbox("승급할 게스트 선택", gst_names if gst_names else ["승급할 게스트 없음"], key="reg_up_guest")
                if st.button("정회원으로 승급", use_container_width=True, key="reg_up_btn"):
                    if up_g != "승급할 게스트 없음":
                        conn = get_db_conn()
                        try:
                            conn.cursor().execute("UPDATE members SET is_guest=0 WHERE name=?", (up_g,))
                            conn.commit()
                        finally: conn.close()
                        retro_calculate_points_for_user(up_g); st.success(f"🎉 {up_g}님이 정회원으로 승급되었습니다!"); st.rerun()
                        
                st.divider()
                st.markdown("##### ❌ 회원 삭제")
                del_n = st.selectbox("삭제할 사람", members_df['name'].tolist(), key="reg_del_member")
                if st.button("회원 삭제", use_container_width=True, key="reg_del_btn"):
                    conn = get_db_conn()
                    try:
                        conn.cursor().execute("UPDATE members SET is_active=0 WHERE name=?", (del_n,))
                        conn.commit()
                    finally: conn.close()
                    st.rerun()
                    
            st.divider()
            st.subheader("🎾 정규 대진표 생성")
            full_df = get_members()
            selected_names = []
            cols = st.columns(3)
            for idx, row in full_df.iterrows():
                with cols[idx % 3]:
                    if st.checkbox(f"{row['name']}(G)" if row['is_guest'] == 1 else row['name'], value=True, key=f"chk_reg_{idx}_{row['name']}"): selected_names.append(row['name'])
            st.info(f"✅ 선택된 참여 인원: **{len(selected_names)}명**")
                    
            active_date_obj = datetime.strptime(st.session_state['match_date'], "%Y-%m-%d") if st.session_state['match_date'] else datetime.now()
            m_date = st.date_input("📅 대진표 적용 날짜", value=active_date_obj, key="reg_match_date").strftime("%Y-%m-%d")
            
            c0, c1, c2 = st.columns([1.2, 1, 1])
            with c0: play_mode = st.radio("경기 방식", ["복식", "단식"], horizontal=True, key="reg_play_mode")
            with c1: r_cnt = st.number_input("라운드 수", 1, 20, 4, key="reg_r_cnt")
            with c2: 
                court_input = st.text_input("사용 코트 (쉼표 구분)", "1,2", key="reg_c_cnt")
                reg_court_names = [c.strip() for c in court_input.split(",") if c.strip()]
                c_cnt = len(reg_court_names)
            
            if play_mode == "복식":
                c3, c4 = st.columns(2)
                with c3: opt = st.selectbox("1차 기준", ["기본 (평점 우선)", "혼복 우선", "여복 우선", "팀 상관없이 혼복우선", "특정 페어 우선", "특정팀 대결 우선"], key="reg_opt")
                with c4: sub_opt = st.selectbox("2차 기준(나머지)", ["기본 (평점 우선)", "혼복 우선", "여복 우선"], key="reg_sub_opt") if opt in ["특정 페어 우선", "특정팀 대결 우선"] else "기본 (평점 우선)"

                special_data_list = []
                if opt == "특정 페어 우선":
                    for i in range(st.session_state['pair_count']):
                        c_p1, c_p2 = st.columns(2)
                        with c_p1: p1_a = st.selectbox(f"선수 1", ["선택"] + selected_names, key=f"p1_a_reg_{i}")
                        with c_p2: p1_b = st.selectbox(f"선수 2", ["선택"] + selected_names, key=f"p1_b_reg_{i}")
                        if p1_a != "선택" and p1_b != "선택": special_data_list.append((p1_a, p1_b))
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        if st.button("➕ 페어 추가하기"): st.session_state['pair_count'] += 1; st.rerun()
                    with c_btn2:
                        if st.session_state['pair_count'] > 1 and st.button("➖ 페어 줄이기"): st.session_state['pair_count'] -= 1; st.rerun()
                elif opt == "특정팀 대결 우선":
                    for i in range(st.session_state['team_count']):
                        c_t1, c_t2, c_t3, c_t4 = st.columns(4)
                        with c_t1: ta_1 = st.selectbox(f"A-1", ["선택"] + selected_names, key=f"ta_1_reg_{i}")
                        with c_t2: ta_2 = st.selectbox(f"A-2", ["선택"] + selected_names, key=f"ta_2_reg_{i}")
                        with c_t3: tb_1 = st.selectbox(f"B-1", ["선택"] + selected_names, key=f"tb_1_reg_{i}")
                        with c_t4: tb_2 = st.selectbox(f"B-2", ["선택"] + selected_names, key=f"tb_2_reg_{i}")
                        if "선택" not in [ta1, ta2, tb1, tb2]: special_data_list.append(((ta_1, ta_2), (tb_1, tb_2)))
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        if st.button("➕ 대결 추가하기"): st.session_state['team_count'] += 1; st.rerun()
                    with c_btn2:
                        if st.session_state['team_count'] > 1 and st.button("➖ 대결 줄이기"): st.session_state['team_count'] -= 1; st.rerun()
            else: opt, sub_opt, special_data_list = "단식", "기본 (평점 우선)", []

            if 'gen_confirm_reg' not in st.session_state: st.session_state.gen_confirm_reg = False
            conn = get_db_conn()
            try: existing_matches = pd.read_sql_query("SELECT COUNT(*) FROM match_history WHERE game_date=?", conn, params=(m_date,)).iloc[0,0]
            finally: conn.close()

            if st.button("🚀 정규 대진표 생성", type="primary", use_container_width=True, key="btn_reg_gen_start"):
                if existing_matches > 0: st.session_state.gen_confirm_reg = True
                else:
                    st.session_state.gen_confirm_reg = False
                    st.session_state['match_date'] = m_date 
                    p_df = full_df[full_df['name'].isin(selected_names)]
                    gen_params = {'r_cnt': r_cnt, 'c_cnt': c_cnt, 'court_names': reg_court_names, 'opt': opt, 'sub_opt': sub_opt, 'play_mode': play_mode, 'special_data': special_data_list, 'selected_names': selected_names}
                    st.session_state['gen_params'] = gen_params
                    st.session_state['tournament_data'] = {}
                    for r in range(1, r_cnt + 1):
                        round_result = generate_single_round(p_df, c_cnt, play_mode, opt, special_data_list, sub_opt, r, st.session_state['tournament_data'])
                        st.session_state['tournament_data'][str(r)] = round_result
                        rules = get_point_rules()
                        wl_id = f"{m_date}_R{r}_Waitlist"
                        conn = get_db_conn()
                        try:
                            conn.cursor().execute("DELETE FROM points_log WHERE source_id=?", (wl_id,))
                            for w in round_result['waitlist']:
                                if not w.get('is_guest', False): conn.cursor().execute("INSERT INTO points_log (source_id, name, input_date, points, games) VALUES (?, ?, ?, ?, ?)", (wl_id, w['name'], m_date, rules.get('대기자', {'win':2})['win'], 0))
                            conn.commit()
                        finally: conn.close()
                    save_active_tournament(m_date, st.session_state['tournament_data'], gen_params)
                    st.success("생성 완료!")

            if st.session_state.gen_confirm_reg:
                st.markdown("<div class='nowrap-text' style='text-align:center; font-weight:bold; font-size:14px; color:#d32f2f; margin-bottom:5px;'>⚠️ 이미 대진표가 존재합니다. 삭제하고 다시 생성할까요?</div>", unsafe_allow_html=True)
                c_yes, c_no = st.columns([1, 1])
                with c_yes:
                    if st.button("확인", use_container_width=True, key="btn_reg_gen_confirm"):
                        conn = get_db_conn()
                        try:
                            conn.cursor().execute("DELETE FROM match_history WHERE game_date=?", (m_date,))
                            conn.cursor().execute("DELETE FROM points_log WHERE input_date=? AND source_id LIKE '%_C%'", (m_date,))
                            conn.commit()
                        finally: conn.close()
                        
                        st.session_state['match_date'] = m_date 
                        p_df = full_df[full_df['name'].isin(selected_names)]
                        gen_params = {'r_cnt': r_cnt, 'c_cnt': c_cnt, 'court_names': reg_court_names, 'opt': opt, 'sub_opt': sub_opt, 'play_mode': play_mode, 'special_data': special_data_list, 'selected_names': selected_names}
                        st.session_state['gen_params'] = gen_params
                        st.session_state['tournament_data'] = {}
                        for r in range(1, r_cnt + 1):
                            round_result = generate_single_round(p_df, c_cnt, play_mode, opt, special_data_list, sub_opt, r, st.session_state['tournament_data'])
                            st.session_state['tournament_data'][str(r)] = round_result
                            rules = get_point_rules()
                            wl_id = f"{m_date}_R{r}_Waitlist"
                            conn = get_db_conn()
                            try:
                                conn.cursor().execute("DELETE FROM points_log WHERE source_id=?", (wl_id,))
                                for w in round_result['waitlist']:
                                    if not w.get('is_guest', False): conn.cursor().execute("INSERT INTO points_log (source_id, name, input_date, points, games) VALUES (?, ?, ?, ?, ?)", (wl_id, w['name'], m_date, rules.get('대기자', {'win':2})['win'], 0))
                                conn.commit()
                            finally: conn.close()
                        save_active_tournament(m_date, st.session_state['tournament_data'], gen_params)
                        st.session_state.gen_confirm_reg = False
                        st.success("생성 완료!"); st.rerun()
                with c_no:
                    if st.button("취소", use_container_width=True, key="btn_reg_gen_cancel"):
                        st.session_state.gen_confirm_reg = False
                        st.rerun()

            if st.session_state['tournament_data'] and not st.session_state.gen_confirm_reg:
                st.markdown("<br><h3 style='color:#1976D2;'>👇 생성된 정규 대진표 관리 (라운드 단일 재생성/인원 교체)</h3>", unsafe_allow_html=True)
                for r_num, round_data in st.session_state['tournament_data'].items():
                    render_horizontal_bracket(r_num, round_data, is_admin=True, filter_name="전체 보기", target_date=m_date, court_names=reg_court_names)
