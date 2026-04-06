import streamlit as st, sqlite3, pandas as pd, random, json, re
from datetime import datetime

# ==========================================
# 모바일 UI 최적화 및 스타일 세팅
# ==========================================
st.set_page_config(page_title="핫테 매니저", page_icon="🎾", layout="wide", initial_sidebar_state="collapsed")

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
    table.rank-table { border-collapse: separate; border-spacing: 0; width: 100%; text-align: center; font-size: 12px; font-family: sans-serif; white-space: nowrap; }
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
    
    .pulse-bg { animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

    .acc-card { padding: 15px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 10px; text-align: center; }
    .acc-balance { background-color: #f1f8e9; color: #2e7d32; border: 2px solid #2e7d32; font-size: 18px; font-weight: 900;}
    
    @media (max-width: 640px) {
        [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; overflow: hidden !important; }
        [data-testid="stHorizontalBlock"] > div { min-width: 0 !important; padding: 0 3px !important; }
        div[data-testid="stExpander"] details summary p { font-size: 15px !important; font-weight: bold !important; white-space: nowrap !important; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1단계: 강력한 DB 연결 모듈 및 초기화
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
            default_members = [("상국", "남", 5.0, 1), ("홍만", "남", 5.0, 1), ("체야", "여", 5.0, 1), ("재윤", "여", 5.0, 1), ("인숙", "여", 5.0, 1), ("상철", "남", 5.0, 1), ("효경", "여", 5.0, 1), ("재민", "남", 5.0, 1), ("재경", "남", 5.0, 1), ("정호", "남", 5.0, 1), ("대홍", "남", 5.0, 1), ("영익", "남", 5.0, 1), ("영도", "남", 5.0, 1), ("진철", "남", 5.0, 1)]
            c.executemany("INSERT INTO members (name, gender, base_rating, is_active) VALUES (?, ?, ?, ?)", default_members)
        
        c.execute('''CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, category TEXT, description TEXT, income INTEGER DEFAULT 0, expense INTEGER DEFAULT 0, member_name TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS points_log (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, input_date TEXT, points INTEGER, games INTEGER)''')
        c.execute('''CREATE TABLE IF NOT EXISTS match_history (id TEXT PRIMARY KEY, game_date TEXT, team_a TEXT, team_b TEXT, winner TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, event_date TEXT, event_name TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS event_matches (id TEXT PRIMARY KEY, event_id INTEGER, round INTEGER, court INTEGER, team_a TEXT, team_b TEXT, winner TEXT)''')
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
            ("event_matches", "score_a", "INTEGER DEFAULT 0"),
            ("event_matches", "score_b", "INTEGER DEFAULT 0"),
            ("event_matches", "team_a_pos", "TEXT DEFAULT '미지정'"),
            ("event_matches", "team_b_pos", "TEXT DEFAULT '미지정'"),
            ("event_points_log", "score_won", "INTEGER DEFAULT 0"),
            ("event_points_log", "score_lost", "INTEGER DEFAULT 0")]:
            add_column_safe(t, c_name, defs)
        conn.commit()
    finally: conn.close()

init_db()

# 상태 초기화
if 'pair_count' not in st.session_state: st.session_state['pair_count'] = 1
if 'team_count' not in st.session_state: st.session_state['team_count'] = 1
if 'admin_logged_in' not in st.session_state: st.session_state['admin_logged_in'] = False
if 'sync_done' not in st.session_state:
    conn = get_db_conn()
    try:
        c = conn.cursor()
        d_row = c.execute("SELECT value FROM settings WHERE key='active_match_date'").fetchone()
        j_row = c.execute("SELECT value FROM settings WHERE key='active_tournament_json'").fetchone()
        g_row = c.execute("SELECT value FROM settings WHERE key='active_gen_params_json'").fetchone()
        
        st.session_state['match_date'] = d_row[0] if d_row else datetime.now().strftime("%Y-%m-%d")
        st.session_state['tournament_data'] = {str(k): v for k, v in json.loads(j_row[0]).items()} if j_row and j_row[0] and j_row[0] != 'null' else {}
        st.session_state['gen_params'] = json.loads(g_row[0]) if g_row and g_row[0] and g_row[0] != 'null' else None
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

def strip_gender(s): return str(s).replace('(여)','').replace('(남)','').replace('(G)','').strip() if isinstance(s, str) else s

# ==========================================
# 코트별 자동 출전 추적기
# ==========================================
def get_next_up_matches(t_data, court_names):
    next_up_details = []
    next_up_set = set()
    if not t_data: return next_up_details, next_up_set
    try: r_keys = sorted([str(k) for k in t_data.keys()], key=lambda x: int(x))
    except: return next_up_details, next_up_set
    if not r_keys: return next_up_details, next_up_set
    
    c_cnt = max([len(t_data[r].get('matches', [])) for r in r_keys])
    
    for c in range(c_cnt):
        for r in r_keys:
            matches = t_data[r].get('matches', [])
            if c < len(matches):
                match = matches[c]
                if match['winner'] == '입력 대기':
                    if int(r) > 1: # 1라운드는 출전 알림 제외
                        ta_n_display = " & ".join([p['name'] for p in match['team_a']])
                        tb_n_display = " & ".join([p['name'] for p in match['team_b']])
                        c_name = court_names[c] if court_names and c < len(court_names) else str(c+1)
                        next_up_details.append({'round': r, 'court_idx': c, 'court_name': c_name, 'team_a': ta_n_display, 'team_b': tb_n_display})
                        next_up_set.add((str(r), c))
                    break
    return next_up_details, next_up_set

# ==========================================
# 실시간 순위 및 대기자 지연 반영 
# ==========================================
def render_realtime_podium(pts_df, matches_df, min_games=1, title="🏆 실시간 순위", t_data=None):
    if pts_df.empty:
        st.info("🎯 스코어가 저장된 경기가 없어 순위를 산정할 수 없습니다.")
        return pd.DataFrame()

    if t_data is not None:
        completed_rounds = []
        for r_num, r_info in t_data.items():
            matches = r_info.get('matches', [])
            if len(matches) > 0 and all(m['winner'] not in ['입력 대기', '취소'] for m in matches):
                completed_rounds.append(str(r_num))
        
        id_col = 'match_id' if 'match_id' in pts_df.columns else 'source_id'
        if id_col in pts_df.columns:
            def is_valid_waitlist(row):
                if row['games'] > 0: return True
                parts = str(row[id_col]).split('_R')
                if len(parts) > 1:
                    r_part = parts[1].split('_')[0]
                    if r_part in completed_rounds: return True
                    return False
                return True
            pts_df['is_valid'] = pts_df.apply(is_valid_waitlist, axis=1)
            pts_df = pts_df[pts_df['is_valid']].drop(columns=['is_valid'])

    agg = pts_df.groupby('name').agg(승점=('points', 'sum'), 경기수=('games', 'sum')).reset_index()
    wl_dict = {n: {'승':0, '무':0, '패':0, '득점':0, '실점':0} for n in agg['name']}
    
    if not matches_df.empty:
        for _, m in matches_df.iterrows():
            ta = [x.strip() for x in str(m['team_a']).replace('&', ',').split(',') if x.strip()]
            tb = [x.strip() for x in str(m['team_b']).replace('&', ',').split(',') if x.strip()]
            w = m['winner']
            try: sa, sb = int(m['score_a']), int(m['score_b'])
            except: sa, sb = 0, 0

            for u in ta:
                if u not in wl_dict: wl_dict[u] = {'승':0, '무':0, '패':0, '득점':0, '실점':0}
                wl_dict[u]['득점'] += sa; wl_dict[u]['실점'] += sb
                if w == "A팀 승리": wl_dict[u]['승'] += 1
                elif w == "무승부": wl_dict[u]['무'] += 1
                elif w == "B팀 승리": wl_dict[u]['패'] += 1
                
            for u in tb:
                if u not in wl_dict: wl_dict[u] = {'승':0, '무':0, '패':0, '득점':0, '실점':0}
                wl_dict[u]['득점'] += sb; wl_dict[u]['실점'] += sa
                if w == "B팀 승리": wl_dict[u]['승'] += 1
                elif w == "무승부": wl_dict[u]['무'] += 1
                elif w == "A팀 승리": wl_dict[u]['패'] += 1
                
    agg['승'] = agg['name'].map(lambda x: wl_dict.get(x, {}).get('승', 0)).fillna(0).astype(int)
    agg['무'] = agg['name'].map(lambda x: wl_dict.get(x, {}).get('무', 0)).fillna(0).astype(int)
    agg['패'] = agg['name'].map(lambda x: wl_dict.get(x, {}).get('패', 0)).fillna(0).astype(int)
    agg['득점'] = agg['name'].map(lambda x: wl_dict.get(x, {}).get('득점', 0)).fillna(0).astype(int)
    agg['실점'] = agg['name'].map(lambda x: wl_dict.get(x, {}).get('실점', 0)).fillna(0).astype(int)
    agg['득실차'] = agg['득점'] - agg['실점']
    
    wait_counts = pts_df[pts_df['games'] == 0].groupby('name').size().to_dict()
    agg['대기'] = agg['name'].map(lambda x: wait_counts.get(x, 0)).fillna(0).astype(int)
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

def display_assigned_counts(t_data):
    if not t_data: return
    stats = {}
    for r_num, r_data in t_data.items():
        for m in r_data.get('matches', []):
            if m['winner'] == '취소': continue
            for p in m.get('team_a', []) + m.get('team_b', []):
                n = p['name']
                if n not in stats: stats[n] = {'play': 0, 'wait': 0}
                stats[n]['play'] += 1
        for w in r_data.get('waitlist', []):
            n = w['name']
            if n not in stats: stats[n] = {'play': 0, 'wait': 0}
            stats[n]['wait'] += 1
            
    if not stats: return
    
    st.markdown("<div style='font-size:15px; font-weight:bold; color:#e65100; margin-top:15px; margin-bottom:5px;'>💤 개인별 배정 현황표 (전체 라운드 기준)</div>", unsafe_allow_html=True)
    sorted_stats = sorted(stats.items(), key=lambda x: (-x[1]['wait'], x[1]['play'], x[0]))
    
    html = "<table style='width:100%; border-collapse: collapse; text-align:center; font-size:13px; margin-bottom:10px;'>"
    for i in range(0, len(sorted_stats), 3):
        html += "<tr>"
        for j in range(3):
            if i + j < len(sorted_stats):
                p = sorted_stats[i+j]
                border_left = "border-left:1px dashed #ccc;" if j > 0 else ""
                html += f"<td style='padding:6px; border-bottom:1px solid #ddd; {border_left}'><b style='color:#333; font-size:14px;'>{p[0]}</b><br><span style='color:#1976d2; font-weight:bold;'>{p[1]['play']}게임</span> / <span style='color:#d32f2f; font-weight:bold;'>{p[1]['wait']}대기</span></td>"
            else:
                border_left = "border-left:1px dashed #ccc;" if j > 0 else ""
                html += f"<td style='padding:6px; border-bottom:1px solid #ddd; {border_left}'></td>"
        html += "</tr>"
    html += "</table>"
    st.markdown(f"<div style='background-color:#fff; border-radius:8px; border:1px solid #ccc; padding:5px;'>{html}</div>", unsafe_allow_html=True)

# ==========================================
# 승점 계산 및 배분 AI 로직
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

def calculate_earned_points(team_a, team_b, winner):
    rules = get_point_rules()
    if len(team_a) == 1:
        r = rules.get("단식", {'win':3, 'lose':0, 'draw':1})
        if winner == 'A팀 승리': return r['win'], r['lose']
        elif winner == 'B팀 승리': return r['lose'], r['win']
        return r['draw'], r['draw']
    ga, gb = [p.get('gender','남') for p in team_a], [p.get('gender','남') for p in team_b]
    type_a = 'MM' if ga.count('남') == 2 else 'FF' if ga.count('여') == 2 else 'MF'
    type_b = 'MM' if gb.count('남') == 2 else 'FF' if gb.count('여') == 2 else 'MF'
    if type_a == 'MF' and type_b == 'MM':
        if winner == 'A팀 승리': return rules.get('남녀 (남남과 대결)',{'win':5})['win'], rules.get('남남 (혼복과 대결)',{'lose':0})['lose']
        elif winner == 'B팀 승리': return rules.get('남녀 (남남과 대결)',{'lose':0})['lose'], rules.get('남남 (혼복과 대결)',{'win':3})['win']
        return rules.get('남녀 (남남과 대결)',{'draw':2})['draw'], rules.get('남남 (혼복과 대결)',{'draw':1})['draw']
    elif type_a == 'MM' and type_b == 'MF':
        if winner == 'A팀 승리': return rules.get('남남 (혼복과 대결)',{'win':3})['win'], rules.get('남녀 (남남과 대결)',{'lose':0})['lose']
        elif winner == 'B팀 승리': return rules.get('남남 (혼복과 대결)',{'lose':0})['lose'], rules.get('남녀 (남남과 대결)',{'win':5})['win']
        return rules.get('남남 (혼복과 대결)',{'draw':1})['draw'], rules.get('남녀 (남남과 대결)',{'draw':2})['draw']
    else:
        cat_a = get_match_rule_category(team_a, team_b)
        r = rules.get(cat_a, rules.get('남남 대 남남', {'win':3, 'lose':0, 'draw':1}))
        if winner == 'A팀 승리': return r['win'], r['lose']
        elif winner == 'B팀 승리': return r['lose'], r['win']
        return r['draw'], r['draw']

def assign_points_db(match_id, target_date, team_a, team_b, result, is_event=False, event_id=None, score_a=0, score_b=0):
    conn = get_db_conn()
    try:
        c = conn.cursor()
        score_a, score_b = int(score_a), int(score_b)
        if is_event: c.execute("DELETE FROM event_points_log WHERE match_id=?", (match_id,))
        else: c.execute("DELETE FROM points_log WHERE source_id=?", (match_id,))

        if result not in ["입력 대기", "취소"]:
            pts_a, pts_b = calculate_earned_points(team_a, team_b, result)
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
    for p in player_dicts: p['rand'] = random.random()
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
    rounds_present = {p['name']: 0 for p in player_dicts}
    
    for r_num, r_data in all_rounds_data.items():
        if int(r_num) >= current_r_num: continue
        for match in r_data['matches']:
            if match['winner'] == '취소': continue
            ta, tb = [p['name'] for p in match['team_a']], [p['name'] for p in match['team_b']]
            for n in ta + tb:
                if n in play_counts: play_counts[n] += 1
                if n in rounds_present: rounds_present[n] += 1
            if len(ta) == 2:
                if ta[0] in past_partners and ta[1] in past_partners: past_partners[ta[0]].add(ta[1]); past_partners[ta[1]].add(ta[0])
            if len(tb) == 2:
                if tb[0] in past_partners and tb[1] in past_partners: past_partners[tb[0]].add(tb[1]); past_partners[tb[1]].add(tb[0])
            for pa in ta:
                for pb in tb:
                    if pa in past_opponents and pb in past_opponents: past_opponents[pa].add(pb); past_opponents[pb].add(pa)
        for w in r_data.get('waitlist', []):
            if w['name'] in rounds_present: rounds_present[w['name']] += 1
                
    prev_r_num = str(int(current_r_num) - 1)
    prev_waiters = [w['name'] for w in all_rounds_data.get(prev_r_num, {}).get('waitlist', [])]

    # 공평 비례 배분 핵심 로직
    def waitlist_sort_key(x):
        avail = max(1, rounds_present.get(x['name'], 0))
        played = play_counts.get(x['name'], 0)
        play_ratio = played / avail
        eff_play = play_ratio
        if x['name'] in prev_waiters: eff_play -= 1000 
        # 1순위: 출전비율 높은사람 우선 대기, 2순위: 많이 뛴 사람, 3순위: 완전 랜덤(평점 배제)
        return (eff_play, played, x['rand'])
    
    waitlist = []
    if needed_waitlist > 0:
        avail_for_wait = [p for p in player_dicts if p['name'] not in reserved_names]
        sorted_by_plays = sorted(avail_for_wait, key=waitlist_sort_key, reverse=True)
        waitlist = sorted_by_plays[:needed_waitlist]
        if len(waitlist) < needed_waitlist:
            rem = needed_waitlist - len(waitlist)
            avail_reserved = [p for p in player_dicts if p['name'] in reserved_names and p not in waitlist]
            waitlist.extend(sorted(avail_reserved, key=waitlist_sort_key, reverse=True)[:rem])
            
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
        team_rosters = None; match_option = "기본 (평점 우선)"; sub_option = "혼복 우선"

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
            tb_type = get_t_type(tb)
            tb_rating = sum(p['eff_rating'] for p in tb)
            penalty = 0
            if rest_opt in ["여복 우선", "혼복 우선"]:
                if ta_type != tb_type: penalty += 500000
                
            # [강력 페널티] 혼복 vs 여복 완전 배제
            if (ta_type == 'MF' and tb_type == 'FF') or (ta_type == 'FF' and tb_type == 'MF'):
                penalty += 2000000
                
            # [강력 페널티] 남복 vs 혼복은 혼복이 1.2 이상 높을 때만 허용
            if ta_type == 'MM' and tb_type == 'MF':
                if tb_rating < ta_rating + 1.2: penalty += 2000000
            elif ta_type == 'MF' and tb_type == 'MM':
                if ta_rating < tb_rating + 1.2: penalty += 2000000

            for pa in ta:
                for pb in tb:
                    if pb['name'] in past_opponents[pa['name']]: penalty += 10000
            cost = abs(ta_rating - tb_rating) + penalty
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
def render_match_card(r_num, c_idx, match, is_admin, filter_name, is_event, event_id, target_date, c_name_display, uniq_id, all_ex_m, auto_expand=False, next_up_matches=None):
    if next_up_matches is None: next_up_matches = set()
    is_next_up = (str(r_num), c_idx) in next_up_matches

    team_a, team_b, current_winner = match['team_a'], match['team_b'], match['winner']
    if current_winner == '취소': return
    
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
    
    if current_winner not in ['입력 대기']:
        pts_a, pts_b = calculate_earned_points(team_a, team_b, current_winner)
        pts_str = f"승점 {pts_a}점" if current_winner == "A팀 승리" else f"승점 {pts_b}점" if current_winner == "B팀 승리" else f"각 {pts_a}점"
        display_winner_with_pts = f"{display_winner} - {pts_str}"
        status_text = f"<span style='color:#1976d2;'>{def_sa} : {def_sb} ({display_winner_with_pts})</span>"
    else:
        status_text = f"<span style='color:#e65100; font-weight:bold;'>🚨 점수 미입력 (클릭)</span>"

    edit_mode_key = f"edit_mode_{r_num}_{c_idx}_{uniq_id}"
    if edit_mode_key not in st.session_state: st.session_state[edit_mode_key] = False

    if not st.session_state[edit_mode_key]:
        next_up_html = f"<div class='pulse-bg' style='background:linear-gradient(90deg, #ffcdd2, #ffebee); color:#c62828; padding:6px; border-radius:5px; text-align:center; font-weight:900; margin-bottom:8px; font-size:14px; border-left:4px solid #d32f2f;'>👉 지금 [ {c_name_display} 코트 ] 출전 바랍니다!</div>" if is_next_up else ""
        
        html_str = f"<div class='match-card'>{next_up_html}<div style='font-size:12px; color:#555; margin-bottom:3px;'>[🏆 {r_num}R / {c_name_display} 코트]</div><div class='wrap-text' style='font-size:16px; font-weight:900; color:#111;'>{ta_n_display} <span style='color:#d32f2f; font-size:14px;'>VS</span> {tb_n_display}</div><div class='nowrap-text' style='font-size:13px; margin-top:3px; margin-bottom:5px;'>👉 결과: {status_text}</div></div>"
        st.markdown(html_str, unsafe_allow_html=True)
        
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
        st.markdown(f"<div style='font-size:13px; color:#1976d2; margin-bottom:5px; font-weight:900;'>[🏆 {r_num}R / {c_name_display} 코트] 점수 수정 모드</div>", unsafe_allow_html=True)
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

        # 평점 표시 완전 제거
        def get_player_str(p, pos):
            g = p.get('gender', '남')
            pos_html = f" <span style='font-size:13px; color:#d32f2f; font-weight:900;'>: {pos}</span>" if pos in ["포", "백"] else ""
            return f"<div class='nowrap-text' style='font-size:16px; font-weight:900; color:#111; margin-bottom:2px;'>{p['name']}({g}){pos_html}</div>"

        c_top1, c_top2 = st.columns([5, 1.2])
        with c_top1: pass
        with c_top2:
            if st.button("닫기", key=f"close_{r_num}_{c_idx}_{uniq_id}", use_container_width=True):
                st.session_state[edit_mode_key] = False; st.rerun()

        c_b1, c_b2 = st.columns(2)
        with c_b1: st.markdown(f"<div class='team-box-a'>{get_player_str(team_a[0], ta1_pos)}{get_player_str(team_a[1], ta2_pos) if not is_singles else ''}</div>", unsafe_allow_html=True)
        with c_b2: st.markdown(f"<div class='team-box-b'>{get_player_str(team_b[0], tb1_pos)}{get_player_str(team_b[1], tb2_pos) if not is_singles else ''}</div>", unsafe_allow_html=True)

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
                    assign_points_db(m_id_check, target_date if not is_event else target_date, team_a, team_b, win_res, is_event, event_id, int(score_a), int(score_b))
                    st.session_state[edit_mode_key] = False; st.success("저장 완료!"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

def render_horizontal_bracket(r_num, round_data, is_admin=False, filter_name="전체 보기", is_event=False, event_id=None, target_date=None, court_names=None, next_up_matches=None):
    if next_up_matches is None: next_up_matches = set()
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
            
    if filter_name != "전체 보기" and not is_my_match_exist: return False

    missing_courts = []
    for c_idx, match in filtered_matches:
        if match['winner'] == '입력 대기':
            c_name = court_names[c_idx] if court_names and c_idx < len(court_names) else str(c_idx + 1)
            missing_courts.append(str(c_name))

    has_unentered = len(missing_courts) > 0
    missing_str = ""
    if has_unentered:
        missing_str = ", ".join(missing_courts) + "번코트"

    uniq_id = f"evt_{event_id}" if is_event else f"reg_{target_date}"
    
    if filter_name != "전체 보기":
        if has_unentered:
            title_text = f"🏆 {r_num} 라운드 ({round_data['option']}) - 🚨 {missing_str} 점수 등록 안됨"
        else:
            title_text = f"🏆 {r_num} 라운드 ({round_data['option']}) - ✅ 입력 완료"
        auto_expand = False
    else:
        auto_expand = False
        round_status = " [💤 휴식]" if is_my_waitlist else ""
        if has_unentered:
            title_text = f"🏆 {r_num} 라운드 ({round_data['option']}){round_status} - 🚨 {missing_str} 점수 등록 안됨"
        else:
            title_text = f"🏆 {r_num} 라운드 ({round_data['option']}){round_status}"

    with st.expander(title_text, expanded=auto_expand):
        if filter_name != "전체 보기" and has_unentered:
            st.markdown("<div style='margin-top:-10px; margin-bottom:10px;'><span style='color:#d32f2f; font-weight:900;'>🚨 아래를 클릭하여 점수를 입력하세요</span></div>", unsafe_allow_html=True)
            
        if round_data['waitlist']:
            w_names = [f"{p['name']}(G)" if p.get('is_guest',0) else p['name'] for p in round_data['waitlist']]
            if filter_name == "전체 보기": st.markdown(f"<div class='wrap-text' style='font-size:13px; color:#e65100; margin-bottom:10px;'>💤 대기: {', '.join(w_names)}</div>", unsafe_allow_html=True)

        if court_names is None: court_names = [str(i+1) for i in range(20)]

        conn = get_db_conn()
        try:
            if is_event: all_ex_m = pd.read_sql_query("SELECT id, score_a, score_b, team_a_pos, team_b_pos FROM event_matches WHERE event_id=? AND round=?", conn, params=(event_id, r_num))
            else: all_ex_m = pd.read_sql_query("SELECT id, score_a, score_b, team_a_pos, team_b_pos FROM match_history WHERE game_date=? AND id LIKE ?", conn, params=(target_date, f"%_R{r_num}_%"))
        finally: conn.close()

        for c_idx, match in filtered_matches:
            c_name = court_names[c_idx] if c_idx < len(court_names) else str(c_idx + 1)
            render_match_card(r_num, c_idx, match, is_admin, filter_name, is_event, event_id, target_date, c_name, uniq_id, all_ex_m, False, next_up_matches)
        
        if is_admin:
            regen_mode_key = f"regen_mode_{r_num}_{uniq_id}"
            if regen_mode_key not in st.session_state: st.session_state[regen_mode_key] = False
            
            if st.button("🔄 라운드 재설정 메뉴 열기/닫기", key=f"r_regen_btn_{r_num}_{uniq_id}"):
                st.session_state[regen_mode_key] = not st.session_state[regen_mode_key]
                st.rerun()

            if st.session_state[regen_mode_key]:
                st.markdown("<div style='background-color:#f0f2f6; padding:10px; border-radius:8px; margin-bottom:10px;'>", unsafe_allow_html=True)
                st.markdown("#### 🔄 단일 라운드 재생성 (지각/조퇴 인원 반영)")
                
                p_names = [p['name'] for m in round_data['matches'] for p in m['team_a']+m['team_b']] + [w['name'] for w in round_data['waitlist']]
                reg_df_tmp = get_members()
                all_member_names = [n for n in reg_df_tmp['name'].tolist()]
                
                if is_event:
                    part_str = pd.read_sql_query("SELECT participants FROM events WHERE id=?", get_db_conn(), params=(event_id,)).iloc[0,0]
                    raw_players = [x.strip() for x in part_str.split(",") if x.strip()]
                    all_member_names = list(set([strip_gender(x) for x in raw_players] + all_member_names))

                r_participants = st.multiselect("👥 이 라운드 참가자 (지각자 추가 / 조퇴자 삭제)", all_member_names, default=[n for n in p_names if n in all_member_names], key=f"rpart_{r_num}_{uniq_id}")

                c_rm, c_ro = st.columns(2)
                with c_rm: new_mode = st.radio("경기 방식", ["복식", "단식"], horizontal=True, key=f"amode_{r_num}_{uniq_id}")
                with c_ro: new_opt = st.selectbox("대진 기준", ["기본 (평점 우선)", "혼복 우선", "여복 우선", "팀 상관없이 혼복우선"], key=f"aopt_{r_num}_{uniq_id}")
                if st.button("현재 라운드 다시 짜기", key=f"aregen_{r_num}_{uniq_id}", type="primary"):
                    if is_event:
                        e_gen_params = json.loads(pd.read_sql_query("SELECT gen_params_json FROM events WHERE id=?", get_db_conn(), params=(event_id,)).iloc[0]['gen_params_json'])
                        custom_ratings = e_gen_params.get('custom_ratings', {})
                        recon_dicts = []
                        for n in r_participants:
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
                        p_df = reg_df_tmp[reg_df_tmp['name'].isin(r_participants)]
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

# ----------------------------------------
# 개인별 3열 배정 현황표 렌더링
# ----------------------------------------
def display_assigned_counts(t_data):
    if not t_data: return
    stats = {}
    for r_num, r_data in t_data.items():
        for m in r_data.get('matches', []):
            if m['winner'] == '취소': continue
            for p in m.get('team_a', []) + m.get('team_b', []):
                n = p['name']
                if n not in stats: stats[n] = {'play': 0, 'wait': 0}
                stats[n]['play'] += 1
        for w in r_data.get('waitlist', []):
            n = w['name']
            if n not in stats: stats[n] = {'play': 0, 'wait': 0}
            stats[n]['wait'] += 1
            
    if not stats: return
    
    st.markdown("<div style='font-size:15px; font-weight:bold; color:#e65100; margin-top:15px; margin-bottom:5px;'>💤 개인별 배정 현황 (전체 라운드 기준)</div>", unsafe_allow_html=True)
    sorted_stats = sorted(stats.items(), key=lambda x: (-x[1]['wait'], x[1]['play'], x[0]))
    
    html = "<table style='width:100%; border-collapse: collapse; text-align:center; font-size:13px; margin-bottom:10px;'>"
    for i in range(0, len(sorted_stats), 3):
        html += "<tr>"
        for j in range(3):
            if i + j < len(sorted_stats):
                p = sorted_stats[i+j]
                border_left = "border-left:1px dashed #ccc;" if j > 0 else ""
                html += f"<td style='padding:6px; border-bottom:1px solid #ddd; {border_left}'><b style='color:#333; font-size:14px;'>{p[0]}</b><br><span style='color:#1976d2; font-weight:bold;'>{p[1]['play']}게임</span> / <span style='color:#d32f2f; font-weight:bold;'>{p[1]['wait']}대기</span></td>"
            else:
                border_left = "border-left:1px dashed #ccc;" if j > 0 else ""
                html += f"<td style='padding:6px; border-bottom:1px solid #ddd; {border_left}'></td>"
        html += "</tr>"
    html += "</table>"
    st.markdown(f"<div style='background-color:#fff; border-radius:8px; border:1px solid #ccc; padding:5px;'>{html}</div>", unsafe_allow_html=True)

# ==========================================
# 4단계: 메인 메뉴 라우팅
# ==========================================
if menu == "정규리그":
    reg_sub = st.radio("서브", ["📅 대진표/순위", "📊 랭킹", "👤 개인별분석"], horizontal=True, label_visibility="collapsed")
    
    if "대진표" in reg_sub:
        conn = get_db_conn()
        mh_dates_df = pd.read_sql_query("SELECT DISTINCT game_date FROM match_history ORDER BY game_date DESC", conn)
        conn.close()
        
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
            view_mode = st.radio("보기 방식", ["라운드별", "코트별", "개인별"], horizontal=True, label_visibility="collapsed")
            
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1: sel_opt = st.selectbox("📅 날짜 선택", options)
            with col_opt2: filter_name = st.selectbox("👤 선수 선택", all_names) if view_mode == "개인별" else "전체 보기"
                
            st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
            
            if sel_opt.startswith(active_date):
                conn = get_db_conn()
                pts_df = pd.read_sql_query("SELECT * FROM points_log WHERE input_date=?", conn, params=(active_date,))
                matches_check = pd.read_sql_query("SELECT * FROM match_history WHERE game_date=? AND winner != '입력 대기' AND winner != '취소'", conn, params=(active_date,))
                all_ex_m = pd.read_sql_query("SELECT id, score_a, score_b, team_a_pos, team_b_pos FROM match_history WHERE game_date=?", conn, params=(active_date,))
                conn.close()
                
                t_data = st.session_state.get('tournament_data', {})
                agg = render_realtime_podium(pts_df, matches_check, min_games=1, title="🏆 실시간 순위", t_data=t_data)
                uniq_id = f"reg_{active_date}"
                
                gen_params = st.session_state.get('gen_params') or {}
                reg_court_names = gen_params.get('court_names', [str(i+1) for i in range(20)])
                next_up_details, next_up_set = get_next_up_matches(t_data, reg_court_names)

                if filter_name == "전체 보기" and next_up_details:
                    st.markdown("<div style='margin-top:10px; margin-bottom:20px; padding:15px; border-radius:10px; background:linear-gradient(135deg, #ffebee, #ffcdd2); border-left:5px solid #d32f2f; box-shadow:0 4px 6px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
                    st.markdown("<h4 style='color:#c62828; margin-top:0; margin-bottom:10px; font-weight:900;'>🏃 다음 출전 준비</h4>", unsafe_allow_html=True)
                    for nu in next_up_details:
                        st.markdown(f"<div style='font-size:15px; color:#111; margin-bottom:8px;'><b>🏆 {nu['round']} 라운드 - {nu['court_name']} 코트</b><br><span style='font-size:18px; font-weight:900; color:#1976d2;'>{nu['team_a']}</span> <span style='color:#d32f2f; font-weight:bold;'>VS</span> <span style='font-size:18px; font-weight:900; color:#1976d2;'>{nu['team_b']}</span><br><span style='color:#e65100; font-weight:bold;'>👉 출전 바랍니다!</span></div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                if t_data:
                    if view_mode == "라운드별":
                        for r_num, round_data in t_data.items(): render_horizontal_bracket(r_num, round_data, is_admin=False, filter_name="전체 보기", target_date=active_date, court_names=reg_court_names, next_up_matches=next_up_set)
                    elif view_mode == "코트별":
                        courts_dict = {}
                        for r_num, round_data in t_data.items():
                            for c_idx, match in enumerate(round_data['matches']):
                                if match['winner'] == '취소': continue
                                if c_idx not in courts_dict: courts_dict[c_idx] = []
                                courts_dict[c_idx].append((r_num, match))
                        for c_idx in sorted(courts_dict.keys()):
                            c_name = reg_court_names[c_idx] if c_idx < len(reg_court_names) else str(c_idx+1)
                            with st.expander(f"🎾 [{c_name} 코트] 전체 매치", expanded=False):
                                for r_num, match in courts_dict[c_idx]: render_match_card(r_num, c_idx, match, False, "전체 보기", False, None, active_date, c_name, uniq_id, all_ex_m, auto_expand=False, next_up_matches=next_up_set)
                    elif view_mode == "개인별":
                        for r_num, round_data in t_data.items(): render_horizontal_bracket(r_num, round_data, is_admin=False, filter_name=filter_name, target_date=active_date, court_names=reg_court_names, next_up_matches=next_up_set)

                    display_assigned_counts(t_data)
                    
                    # (현장 매치 및 통계 코드는 기존과 동일...)
            else: st.info("과거 기록 조회 모드")

    elif "랭킹" in reg_sub:
        conn = get_db_conn()
        df = pd.read_sql_query("SELECT name, input_date, points, games FROM points_log", conn)
        mh_df = pd.read_sql_query("SELECT id, game_date, team_a, team_b, winner, score_a, score_b FROM match_history WHERE winner != '입력 대기' AND winner != '취소'", conn)
        conn.close()
        
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
            # (기존 랭킹 출력 로직...)

    elif "개인별분석" in reg_sub:
        st.subheader("👤 개인별 상세 전적 분석")
        members = get_members()['name'].tolist()
        target = st.selectbox("분석할 회원 선택", ["선택"] + members)
        
        if target != "선택":
            conn = get_db_conn()
            m1 = pd.read_sql_query("SELECT team_a, team_b, winner, score_a, score_b FROM match_history WHERE winner NOT IN ('입력 대기','취소')", conn)
            m2 = pd.read_sql_query("SELECT team_a, team_b, winner, score_a, score_b FROM event_matches WHERE winner NOT IN ('입력 대기','취소')", conn)
            all_m = pd.concat([m1, m2])
            conn.close()

            stats = {"wins": 0, "losses": 0, "draws": 0, "total": 0}
            partners = {}
            
            for _, r in all_m.iterrows():
                ta = [x.strip() for x in re.split('[&,]', str(r['team_a']))]
                tb = [x.strip() for x in re.split('[&,]', str(r['team_b']))]
                
                if target in ta or target in tb:
                    stats["total"] += 1
                    is_team_a = target in ta
                    my_team = ta if is_team_a else tb
                    
                    if r['winner'] == '무승부': stats["draws"] += 1
                    elif (is_team_a and r['winner'] == 'A팀 승리') or (not is_team_a and r['winner'] == 'B팀 승리'):
                        stats["wins"] += 1
                    else: stats["losses"] += 1
                    
                    for p in my_team:
                        if p != target: partners[p] = partners.get(p, 0) + 1

            if stats["total"] > 0:
                st.success(f"### **{target}** 님의 종합 성적")
                st.markdown(f"**총 {stats['total']}전 {stats['wins']}승 {stats['draws']}무 {stats['losses']}패** (승률: {int(stats['wins']/stats['total']*100)}%)")
                if partners:
                    best_p = max(partners, key=partners.get)
                    st.info(f"🤝 가장 많이 함께한 파트너: **{best_p}** ({partners[best_p]}회)")
            else:
                st.warning("아직 기록된 경기 데이터가 없습니다.")

# ----------------------------------------
# 2. 이벤트
# ----------------------------------------
elif menu == "이벤트":
    st.markdown("<h3 style='color:#e65100; font-weight:900;'>🎉 이벤트 대진표</h3>", unsafe_allow_html=True)
    conn = get_db_conn()
    events_df = pd.read_sql_query("SELECT * FROM events ORDER BY id DESC", conn)
    conn.close()
    
    if events_df.empty: st.info("관리자 메뉴에서 이벤트를 먼저 생성해주세요.")
    else:
        options = [f"[{row['event_date'][5:10]}] {row['event_name']}" for _, row in events_df.iterrows()]
        c_opt1, c_opt2 = st.columns(2)
        with c_opt1: selected_event_str = st.selectbox("📌 이벤트 선택", options)
        idx = options.index(selected_event_str)
        selected_event = events_df.iloc[idx]
        e_id, e_type = int(selected_event['id']), selected_event.get('event_type', '개인전')
        
        part_str = selected_event.get('participants', "")
        raw_players = [x.strip() for x in part_str.split(",") if x.strip()] if part_str else []
        view_mode = st.radio("보기 방식", ["라운드별", "코트별", "개인별"], horizontal=True, label_visibility="collapsed")
        with c_opt2: filter_name = st.selectbox("👤 선수 선택", raw_players) if view_mode == "개인별" else "전체 보기"
        st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
        
        conn = get_db_conn()
        pts_df = pd.read_sql_query("SELECT * FROM event_points_log WHERE event_id=?", conn, params=(e_id,))
        matches_check = pd.read_sql_query("SELECT * FROM event_matches WHERE event_id=? AND winner != '입력 대기' AND winner != '취소' AND id NOT LIKE 'EVT_MAN_%'", conn, params=(e_id,))
        all_ex_m = pd.read_sql_query("SELECT id, score_a, score_b, team_a_pos, team_b_pos FROM event_matches WHERE event_id=?", conn, params=(e_id,))
        conn.close()
        
        rules = get_point_rules()
        min_games = int(rules.get('최소 게임수 (이벤트용)', {'win': 1})['win'])
        b_json = selected_event.get('bracket_json')
        t_data = json.loads(b_json) if pd.notna(b_json) and str(b_json).strip() not in ["", "None", "nan", "null"] else {}
            
        agg = render_realtime_podium(pts_df, matches_check, min_games=min_games, title="🏆 실시간 순위", t_data=t_data)
        
        if t_data:
            st.session_state['event_tournament_data'] = t_data
            e_gen_json = selected_event.get('gen_params_json')
            e_gen_params = json.loads(e_gen_json) if pd.notna(e_gen_json) and str(e_gen_json).strip() not in ["", "None", "nan", "null"] else {}
            evt_court_names = e_gen_params.get('court_names', [str(i+1) for i in range(20)])
            uniq_id = f"evt_{e_id}"
            
            next_up_details, next_up_set = get_next_up_matches(t_data, evt_court_names)

            if filter_name == "전체 보기" and next_up_details:
                st.markdown("<div style='margin-top:10px; margin-bottom:20px; padding:15px; border-radius:10px; background:linear-gradient(135deg, #ffebee, #ffcdd2); border-left:5px solid #d32f2f; box-shadow:0 4px 6px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
                st.markdown("<h4 style='color:#c62828; margin-top:0; margin-bottom:10px; font-weight:900;'>🏃 다음 출전 준비</h4>", unsafe_allow_html=True)
                for nu in next_up_details:
                    st.markdown(f"<div style='font-size:15px; color:#111; margin-bottom:8px;'><b>🏆 {nu['round']} 라운드 - {nu['court_name']} 코트</b><br><span style='font-size:18px; font-weight:900; color:#1976d2;'>{nu['team_a']}</span> <span style='color:#d32f2f; font-weight:bold;'>VS</span> <span style='font-size:18px; font-weight:900; color:#1976d2;'>{nu['team_b']}</span><br><span style='color:#e65100; font-weight:bold;'>👉 출전 바랍니다!</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            if view_mode == "라운드별":
                for r_num, round_data in t_data.items(): render_horizontal_bracket(r_num, round_data, is_admin=False, filter_name="전체 보기", is_event=True, event_id=e_id, target_date=selected_event['event_date'], court_names=evt_court_names, next_up_matches=next_up_set)
            elif view_mode == "코트별":
                courts_dict = {}
                for r_num, round_data in t_data.items():
                    for c_idx, match in enumerate(round_data['matches']):
                        if match['winner'] == '취소': continue
                        if c_idx not in courts_dict: courts_dict[c_idx] = []
                        courts_dict[c_idx].append((r_num, match))
                for c_idx in sorted(courts_dict.keys()):
                    c_name = evt_court_names[c_idx] if c_idx < len(evt_court_names) else str(c_idx+1)
                    with st.expander(f"🎾 [{c_name} 코트] 전체 매치", expanded=False):
                        for r_num, match in courts_dict[c_idx]: render_match_card(r_num, c_idx, match, False, "전체 보기", True, e_id, selected_event['event_date'], c_name, uniq_id, all_ex_m, auto_expand=False, next_up_matches=next_up_set)
            elif view_mode == "개인별":
                for r_num, round_data in t_data.items(): render_horizontal_bracket(r_num, round_data, is_admin=False, filter_name=filter_name, is_event=True, event_id=e_id, target_date=selected_event['event_date'], court_names=evt_court_names, next_up_matches=next_up_set)
            
            display_assigned_counts(t_data)

# ----------------------------------------
# 3. 관리자
# ----------------------------------------
elif menu == "관리자":
    conn = get_db_conn()
    stored_pwd = conn.cursor().execute("SELECT value FROM settings WHERE key='admin_password'").fetchone()[0]
    conn.close()

    if not st.session_state['admin_logged_in']:
        if st.text_input("관리자 비밀번호 (초기:1234)", type="password") == stored_pwd:
            st.session_state['admin_logged_in'] = True; st.rerun()
    else:
        st.subheader("⚙️ 시스템 관리")
        adm_tabs = st.tabs(["🎾 정규 리그 관리", "🎉 이벤트 관리", "💰 회계 장부", "🔐 설정"])
        
        # --- 1번: 정규 리그 관리 ---
        with adm_tabs[0]:
            st.markdown("#### 🚀 정규 대진표 생성")
            full_df = get_members()
            selected_names = []
            cols = st.columns(3)
            for idx, row in full_df.iterrows():
                with cols[idx % 3]:
                    if st.checkbox(row['name'], value=True, key=f"chk_reg_{idx}_{row['name']}"): selected_names.append(row['name'])
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
                
            r_late_dict, r_leave_dict = {}, {}
            with st.expander("⏰ 지각/조퇴자 자동 배정 설정 (선택사항)", expanded=False):
                r_latecomers = st.multiselect("🏃 지각자 선택", selected_names, key="r_latecomers")
                for p in r_latecomers: r_late_dict[p] = st.number_input(f"{p}님 합류 라운드", min_value=2, max_value=int(r_cnt), value=2, key=f"r_late_{p}")
                r_leavers = st.multiselect("👋 조퇴자 선택", [n for n in selected_names if n not in r_latecomers], key="r_leavers")
                for p in r_leavers: r_leave_dict[p] = st.number_input(f"{p}님 이탈 라운드", min_value=2, max_value=int(r_cnt), value=int(r_cnt), key=f"r_leave_{p}")
            
            opt, sub_opt, special_data_list = "기본 (평점 우선)", "기본 (평점 우선)", []
            if play_mode == "복식":
                c3, c4 = st.columns(2)
                with c3: opt = st.selectbox("1차 기준", ["기본 (평점 우선)", "혼복 우선", "여복 우선", "팀 상관없이 혼복우선"], key="reg_opt")
                with c4: sub_opt = "기본 (평점 우선)"

            if st.button("🔥 정규 대진표 생성", type="primary", use_container_width=True, key="btn_reg_gen_start"):
                st.session_state['match_date'] = m_date 
                gen_params = {'r_cnt': r_cnt, 'c_cnt': c_cnt, 'court_names': reg_court_names, 'opt': opt, 'sub_opt': sub_opt, 'play_mode': play_mode, 'special_data': special_data_list, 'selected_names': selected_names}
                st.session_state['gen_params'] = gen_params
                st.session_state['tournament_data'] = {}
                
                conn = get_db_conn()
                conn.cursor().execute("DELETE FROM match_history WHERE game_date=?", (m_date,))
                conn.cursor().execute("DELETE FROM points_log WHERE input_date=? AND source_id LIKE '%_R%'", (m_date,))
                conn.commit()
                conn.close()
                
                for r in range(1, int(r_cnt) + 1):
                    curr_round_players = []
                    for n in selected_names:
                        if n in r_late_dict and r < r_late_dict[n]: continue
                        if n in r_leave_dict and r >= r_leave_dict[n]: continue
                        curr_round_players.append(n)
                    
                    p_df = full_df[full_df['name'].isin(curr_round_players)]
                    round_result = generate_single_round(p_df.copy(), c_cnt, play_mode, opt, special_data_list, sub_opt, r, st.session_state['tournament_data'])
                    st.session_state['tournament_data'][str(r)] = round_result
                    
                    rules = get_point_rules()
                    wl_id = f"{m_date}_R{r}_Waitlist"
                    conn = get_db_conn()
                    for w in round_result['waitlist']:
                        conn.cursor().execute("INSERT INTO points_log (source_id, name, input_date, points, games) VALUES (?, ?, ?, ?, ?)", (wl_id, w['name'], m_date, rules.get('대기자', {'win':2})['win'], 0))
                    conn.commit()
                    conn.close()
                save_active_tournament(m_date, st.session_state['tournament_data'], gen_params)
                st.success("생성 완료! 정규리그 탭에서 확인하세요.")

        # --- 2번: 이벤트 관리 ---
        with adm_tabs[1]:
            st.markdown("#### ✨ 1. 새로운 이벤트 방 만들기")
            e_date = st.date_input("📅 이벤트 날짜", datetime.now()).strftime("%Y-%m-%d")
            e_name = st.text_input("📌 이벤트 이름 (예: 3월 월례대회)")
            e_type = st.radio("🏆 이벤트 방식", ["개인전", "팀 대항전"], horizontal=True)

            st.markdown("##### 📥 엑셀로 참가자 명단 업로드")
            uploaded_file = st.file_uploader("엑셀 파일 첨부 (이름|성별|평점)", type=["xlsx", "xls"], key="evt_file_up")
            if uploaded_file:
                df_up = pd.read_excel(uploaded_file)
                st.session_state['temp_participants'] = df_up[['이름', '성별', '평점']].dropna(subset=['이름'])
                st.success("업로드 성공! 아래 표에서 확인 및 수정하세요.")

            edited_evt_df = st.data_editor(
                st.session_state['temp_participants'], 
                num_rows="dynamic",
                column_config={"이름": st.column_config.TextColumn("이름", required=True), "성별": st.column_config.SelectboxColumn("성별", options=["남", "여"], required=True), "평점": st.column_config.NumberColumn("평점", min_value=1.0, max_value=10.0, step=0.1, required=True)}, 
                hide_index=True, use_container_width=True, key="evt_player_editor_admin"
            )
            
            final_selected_e = [str(row['이름']).strip() for _, row in edited_evt_df.iterrows() if pd.notna(row['이름']) and str(row['이름']).strip()]
            if st.button("위 설정으로 새 이벤트 방 생성", use_container_width=True, type="primary"):
                if e_name and final_selected_e:
                    part_str = ",".join(final_selected_e)
                    c_ratings = {str(r['이름']).strip(): float(r['평점']) for _, r in edited_evt_df.iterrows() if pd.notna(r['이름'])}
                    g_map = {str(r['이름']).strip(): str(r['성별']).strip() for _, r in edited_evt_df.iterrows() if pd.notna(r['이름'])}
                    conn = get_db_conn()
                    conn.cursor().execute("INSERT INTO events (event_date, event_name, event_type, participants, gen_params_json) VALUES (?, ?, ?, ?, ?)", 
                                          (e_date, e_name, e_type, part_str, json.dumps({'custom_ratings': c_ratings, 'gender_map': g_map})))
                    conn.commit()
                    conn.close()
                    st.success("방 생성 완료!")
                else: st.error("이름과 참가자를 입력하세요.")

            st.divider()
            st.markdown("#### 🚀 2. 대진표 생성 및 관리")
            conn = get_db_conn()
            events_df = pd.read_sql_query("SELECT * FROM events ORDER BY id DESC", conn)
            conn.close()
            
            if not events_df.empty:
                options = [f"[{row['event_date'][5:10]}] {row['event_name']}" for _, row in events_df.iterrows()]
                selected_event_str = st.selectbox("적용할 이벤트 방", options)
                idx = options.index(selected_event_str)
                selected_event = events_df.iloc[idx]
                e_id = int(selected_event['id'])
                
                e_gen_params = json.loads(selected_event.get('gen_params_json') or '{}')
                c_ratings = e_gen_params.get('custom_ratings', {})
                g_map = e_gen_params.get('gender_map', {})
                raw_players = [x.strip() for x in str(selected_event.get('participants', '')).split(",") if x.strip()]
                
                e_member_dicts = [{"name": n, "gender": g_map.get(n, "남"), "eff_rating": c_ratings.get(n, 5.0)} for n in raw_players]
                active_e_members_df = pd.DataFrame(e_member_dicts)
                
                ce1, ce2, ce3 = st.columns([1, 1, 1])
                with ce1: e_play_mode = st.radio("경기 방식", ["복식", "단식"], horizontal=True, key="e_play_mode_admin")
                with ce2: e_r_cnt = st.number_input("라운드 수", 1, 20, 4, key="e_r_cnt_admin")
                with ce3: 
                    e_court_input = st.text_input("사용 코트", "1,2", key="e_c_cnt_admin")
                    e_court_names = [c.strip() for c in e_court_input.split(",") if c.strip()]
                    e_c_cnt = len(e_court_names)

                if st.button("🔥 대진표 생성 (기존 대진 덮어쓰기)", type="primary", use_container_width=True):
                    conn = get_db_conn()
                    conn.cursor().execute("DELETE FROM event_points_log WHERE event_id=?", (e_id,))
                    conn.cursor().execute("DELETE FROM event_matches WHERE event_id=?", (e_id,))
                    conn.commit()
                    conn.close()

                    new_bracket = {}
                    for r in range(1, int(e_r_cnt) + 1):
                        new_bracket[str(r)] = generate_single_round(active_e_members_df.copy(), e_c_cnt, e_play_mode, "기본 (평점 우선)", [], "기본 (평점 우선)", r, new_bracket)
                    
                    rules = get_point_rules()
                    conn = get_db_conn()
                    for r_str, r_data in new_bracket.items():
                        wl_id = f"EVT{e_id}_R{r_str}_Waitlist"
                        for w in r_data['waitlist']: conn.cursor().execute("INSERT INTO event_points_log (event_id, name, points, games, match_id, result) VALUES (?, ?, ?, ?, ?, ?)", (e_id, str(w['name']), rules.get('대기자', {'win':2})['win'], 0, wl_id, '대기'))
                    e_gen_params['c_cnt'] = e_c_cnt
                    e_gen_params['court_names'] = e_court_names
                    conn.cursor().execute("UPDATE events SET bracket_json=?, gen_params_json=? WHERE id=?", (json.dumps(new_bracket, default=str), json.dumps(e_gen_params), e_id))
                    conn.commit()
                    conn.close()
                    st.success("생성 완료!")

                b_json = selected_event.get('bracket_json')
                if pd.notna(b_json) and str(b_json).strip() not in ["", "None", "nan", "null"]:
                    st.markdown("#### ⏱️ 진행 시간 연장 (추가 라운드 생성)")
                    t_data = json.loads(b_json)
                    c_add1, c_add2 = st.columns(2)
                    with c_add1: add_r_cnt = st.number_input("추가할 라운드 수", 1, 10, 1)
                    with c_add2: add_r_opt = st.selectbox("추가 라운드 대진 기준", ["기본 (평점 우선)", "혼복 우선", "여복 우선"])
                    
                    if st.button("➕ 추가 라운드 지능형 생성", type="primary", use_container_width=True):
                        current_max_r = max([int(k) for k in t_data.keys()]) if t_data else 0
                        rules = get_point_rules()
                        conn = get_db_conn()
                        for r in range(current_max_r + 1, current_max_r + 1 + int(add_r_cnt)):
                            new_r = generate_single_round(active_e_members_df.copy(), e_c_cnt, e_play_mode, add_r_opt, [], add_r_opt, r, t_data)
                            t_data[str(r)] = new_r
                            wl_id = f"EVT{e_id}_R{r}_Waitlist"
                            for w in new_r['waitlist']: 
                                conn.cursor().execute("INSERT INTO event_points_log (event_id, name, points, games, match_id, result) VALUES (?, ?, ?, ?, ?, ?)", (e_id, str(w['name']), rules.get('대기자', {'win':2})['win'], 0, wl_id, '대기'))
                        conn.cursor().execute("UPDATE events SET bracket_json=? WHERE id=?", (json.dumps(t_data, default=str), e_id))
                        conn.commit()
                        conn.close()
                        st.success(f"{int(add_r_cnt)}개의 라운드가 추가되었습니다!"); st.rerun()

        # --- 3번: 회계 장부 ---
        with adm_tabs[2]:
            st.markdown("### 💰 동호회 통합 장부")
            conn = get_db_conn()
            acc_df = pd.read_sql_query("SELECT * FROM accounts ORDER BY date DESC", conn)
            balance = acc_df['income'].sum() - acc_df['expense'].sum()
            st.markdown(f"<div class='acc-card acc-balance'>🏦 현재 은행 잔고: ₩{balance:,}</div>", unsafe_allow_html=True)
            
            with st.expander("💵 월간 회비 납부자 체크"):
                target_m = st.date_input("기준월", datetime.now()).strftime("%Y-%m")
                m_list = get_members()
                paid_m = acc_df[(acc_df['category']=='기본회비') & (acc_df['date'].str.startswith(target_m))]['member_name'].tolist()
                cols = st.columns(4)
                for i, row in m_list.iterrows():
                    with cols[i % 4]:
                        is_paid = row['name'] in paid_m
                        if st.button(f"{'✅' if is_paid else '❌'} {row['name']}", key=f"pay_{row['name']}"):
                            if not is_paid:
                                conn.cursor().execute("INSERT INTO accounts (date, category, description, income, member_name) VALUES (?,?,?,?,?)",
                                                      (datetime.now().strftime("%Y-%m-%d"), "기본회비", f"{target_m} 회비", 30000, row['name']))
                                conn.commit(); st.rerun()
            
            with st.expander("🏟️ 정기대관(월테/수테) 입출금 확인"):
                r_cat = st.selectbox("대관 선택", ["월테 대관", "수테 대관"])
                st.dataframe(acc_df[acc_df['category'] == r_cat][['date', 'description', 'income', 'expense']], use_container_width=True, hide_index=True)
            
            with st.expander("➕ 기타 지출/입금 직접 입력"):
                c1, c2, c3 = st.columns(3)
                with c1: d_date = st.date_input("날짜", datetime.now())
                with c2: d_cat = st.selectbox("분류", ["기본회비", "월테 대관", "수테 대관", "식대/음료", "기타"])
                with c3: d_amt = st.number_input("금액", step=1000)
                d_type = st.radio("구분", ["입금", "출금"], horizontal=True)
                d_desc = st.text_input("상세 내용")
                if st.button("장부 저장"):
                    inc, exp = (d_amt, 0) if d_type == "입금" else (0, d_amt)
                    conn.cursor().execute("INSERT INTO accounts (date, category, description, income, expense) VALUES (?,?,?,?,?)",
                                          (d_date.strftime("%Y-%m-%d"), d_cat, d_desc, inc, exp))
                    conn.commit(); st.success("저장 완료!"); st.rerun()
            conn.close()

        # --- 4번: 비밀번호 변경 ---
        with adm_tabs[3]:
            st.markdown("#### 🔐 관리자 비밀번호 변경")
            new_p = st.text_input("새 비밀번호", type="password")
            if st.button("비밀번호 변경 저장"):
                conn = get_db_conn()
                conn.cursor().execute("UPDATE settings SET value=? WHERE key='admin_password'", (new_p,))
                conn.commit(); conn.close()
                st.success("변경되었습니다.")
                
            if st.button("로그아웃"):
                st.session_state['admin_logged_in'] = False; st.rerun()
