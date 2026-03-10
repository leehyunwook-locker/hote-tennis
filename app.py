import streamlit as st
import sqlite3
import pandas as pd
import random
import itertools
import json
from datetime import datetime

# ==========================================
# 모바일 UI 최적화
# ==========================================
st.set_page_config(page_title="핫테 테니스 매니저", page_icon="🎾", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 1.5rem; padding-left: 0.8rem; padding-right: 0.8rem; max-width: 100%; }
    [data-testid="collapsedControl"] { display: none; }
    h1, h2, h3, h4, h5 { margin-bottom: 0.4rem !important; margin-top: 0.4rem !important; }
    
    div[role="radiogroup"] { justify-content: space-around; background-color: #f0f2f6; padding: 5px; border-radius: 8px; margin-bottom: 8px;}
    .stRadio label { font-size: 14px !important; font-weight: bold; cursor: pointer; padding: 5px; }
    
    .team-a {background-color:#e0f7fa; padding:5px; border-radius:4px; text-align:center; font-size:11px; line-height:1.4; margin-bottom: 2px;}
    .team-b {background-color:#ffebee; padding:5px; border-radius:4px; text-align:center; font-size:11px; line-height:1.4; margin-bottom: 2px;}
    .team-name { font-size: 15px !important; font-weight: 900; color: #111; letter-spacing: -0.5px; }
    .vs-text {text-align:center; font-weight:bold; color:#757575; padding-top:10px; font-size:10px; line-height:1.3;}
    
    div[data-baseweb="select"] { margin-top: -5px; font-size: 12px !important; }
    div[role="radiogroup"] { flex-wrap: wrap !important; gap: 2px !important; padding: 3px !important; }
    .stRadio label { font-size: 11px !important; padding: 2px 4px !important; }
    
    .table-wrapper { overflow: auto; width: 100%; max-height: 65vh; margin-bottom: 1rem; border: 1px solid #ddd; }
    table.rank-table { border-collapse: separate; border-spacing: 0; width: 100%; text-align: center; font-size: 12px; font-family: sans-serif; white-space: nowrap; }
    table.rank-table td { padding: 8px 5px; border-bottom: 1px solid #ddd; border-right: 1px solid #ddd; vertical-align: top !important; text-align: center; background-color: #fff; }
    table.rank-table th { padding: 8px 5px; border-bottom: 1px solid #ddd; border-right: 1px solid #ddd; vertical-align: middle !important; text-align: center !important; position: sticky; top: 0; background-color: #f0f2f6; z-index: 4; box-shadow: 0 2px 2px -1px rgba(0,0,0,0.4); }
    
    table.rank-table th:nth-child(1), table.rank-table td:nth-child(1) { position: sticky; left: 0px; background-color: #f9f9f9; z-index: 3; min-width: 35px; }
    table.rank-table th:nth-child(2), table.rank-table td:nth-child(2) { position: sticky; left: 35px; background-color: #f9f9f9; z-index: 3; min-width: 50px; box-shadow: inset -2px 0 3px -2px rgba(0,0,0,0.2); }
    table.rank-table th:nth-child(1), table.rank-table th:nth-child(2) { z-index: 5 !important; background-color: #eceff1; }
    .pt-text { font-size: 13px; font-weight: bold; color: #1976d2; }
    
    @media (max-width: 640px) {
        [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
        [data-testid="stHorizontalBlock"] > div { min-width: 0 !important; padding: 0 3px !important; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1단계: DB 설정 및 초기화
# ==========================================
def init_db():
    conn = sqlite3.connect('hote_tennis.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_password', '1234')")
    c.execute('''CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, gender TEXT, base_rating REAL, is_active INTEGER)''')
    try: c.execute("ALTER TABLE members ADD COLUMN is_guest INTEGER DEFAULT 0")
    except: pass
    c.execute("SELECT COUNT(*) FROM members")
    if c.fetchone()[0] == 0:
        default_members = [("상국", "남", 5.0, 0), ("홍만", "남", 5.0, 0), ("체야", "여", 5.0, 0), ("재윤", "여", 5.0, 0), ("인숙", "여", 5.0, 0), ("상철", "남", 5.0, 0), ("효경", "여", 5.0, 0), ("재민", "남", 5.0, 0), ("재경", "남", 5.0, 0), ("정호", "남", 5.0, 0), ("대홍", "남", 5.0, 0), ("영익", "남", 5.0, 0), ("영도", "남", 5.0, 0), ("진철", "남", 5.0, 0)]
        c.executemany("INSERT INTO members (name, gender, base_rating, is_active, is_guest) VALUES (?, ?, ?, 1, ?)", default_members)
    c.execute('''CREATE TABLE IF NOT EXISTS points_log (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, input_date TEXT, points INTEGER, games INTEGER)''')
    try: c.execute("ALTER TABLE points_log ADD COLUMN source_id TEXT")
    except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS match_history (id TEXT PRIMARY KEY, game_date TEXT, team_a TEXT, team_b TEXT, winner TEXT)''')
    try: c.execute("ALTER TABLE match_history ADD COLUMN team_a_pos TEXT DEFAULT '미지정'")
    except: pass
    try: c.execute("ALTER TABLE match_history ADD COLUMN team_b_pos TEXT DEFAULT '미지정'")
    except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS point_rules (category TEXT PRIMARY KEY, win INTEGER, lose INTEGER, draw INTEGER)''')
    c.execute("SELECT COUNT(*) FROM point_rules")
    if c.fetchone()[0] == 0:
        default_rules = [("남남 대 남남", 3, 0, 1), ("여여 대 여여", 3, 0, 1), ("남녀 대 남녀", 3, 0, 1), ("남남 (혼복과 대결)", 3, 1, 1), ("남녀 (남남과 대결)", 5, 0, 2), ("대기자", 2, 0, 0)]
        c.executemany("INSERT INTO point_rules VALUES (?, ?, ?, ?)", default_rules)
    conn.commit(); conn.close()

init_db()

def retro_calculate_points_for_user(user_name):
    conn = sqlite3.connect('hote_tennis.db')
    c = conn.cursor()
    c.execute("DELETE FROM points_log WHERE name=? AND source_id != 'EXCEL_IMPORT'", (user_name,)) 
    
    mh_df = pd.read_sql_query("SELECT * FROM match_history WHERE winner != '입력 대기' AND winner != '취소'", conn)
    rules = get_point_rules()
    members_df = pd.read_sql_query("SELECT name, gender FROM members", conn)
    gender_map = dict(zip(members_df['name'], members_df['gender']))
    
    for _, m in mh_df.iterrows():
        ta_names = m['team_a'].split(',')
        tb_names = m['team_b'].split(',')
        
        if user_name in ta_names or user_name in tb_names:
            ta_genders = [gender_map.get(n.strip(), '남') for n in ta_names]
            tb_genders = [gender_map.get(n.strip(), '남') for n in tb_names]
            
            type_a = 'MM' if ta_genders.count('남')==2 else 'FF' if ta_genders.count('여')==2 else 'MF'
            type_b = 'MM' if tb_genders.count('남')==2 else 'FF' if tb_genders.count('여')==2 else 'MF'
            
            if type_a == 'MM' and type_b == 'MM': r = rules['남남 대 남남']
            elif type_a == 'FF' and type_b == 'FF': r = rules['여여 대 여여']
            elif type_a == 'MF' and type_b == 'MF': r = rules['남녀 대 남녀']
            elif type_a == 'MM' and type_b == 'MF': r = rules['남남 (혼복과 대결)']
            elif type_a == 'MF' and type_b == 'MM': r = rules['남녀 (남남과 대결)']
            else: r = rules['남남 대 남남']
            
            res = m['winner']
            pts_a, pts_b = 0, 0
            if type_a == 'MF' and type_b == 'MM': 
                if res == 'A팀 승리': pts_a, pts_b = r['win'], rules['남남 (혼복과 대결)']['lose']
                elif res == 'B팀 승리': pts_a, pts_b = r['lose'], rules['남남 (혼복과 대결)']['win']
                else: pts_a, pts_b = r['draw'], rules['남남 (혼복과 대결)']['draw']
            else:
                if res == 'A팀 승리': pts_a, pts_b = r['win'], r['lose']
                elif res == 'B팀 승리': pts_a, pts_b = r['lose'], r['win']
                else: pts_a, pts_b = r['draw'], r['draw']
            
            my_pts = pts_a if user_name in ta_names else pts_b
            c.execute("INSERT INTO points_log (source_id, name, input_date, points, games) VALUES (?, ?, ?, ?, ?)", 
                      (m['id'], user_name, m['game_date'], my_pts, 1))
    conn.commit(); conn.close()

def save_active_tournament(m_date, t_data, gen_params=None):
    conn = sqlite3.connect('hote_tennis.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('active_match_date', ?)", (m_date,))
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('active_tournament_json', ?)", (json.dumps(t_data),))
    if gen_params is not None:
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('active_gen_params_json', ?)", (json.dumps(gen_params),))
    conn.commit(); conn.close()

# 세션 기본값 세팅 (페어/팀 카운트 포함)
if 'sync_done' not in st.session_state:
    conn = sqlite3.connect('hote_tennis.db')
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='active_match_date'")
    d_row = c.fetchone()
    c.execute("SELECT value FROM settings WHERE key='active_tournament_json'")
    j_row = c.fetchone()
    c.execute("SELECT value FROM settings WHERE key='active_gen_params_json'")
    g_row = c.fetchone()
    conn.close()
    
    st.session_state['match_date'] = d_row[0] if d_row else datetime.now().strftime("%Y-%m-%d")
    if j_row and j_row[0]:
        try: st.session_state['tournament_data'] = {int(k): v for k, v in json.loads(j_row[0]).items()}
        except: st.session_state['tournament_data'] = {}
    else: st.session_state['tournament_data'] = {}
    
    if g_row and g_row[0]:
        try: st.session_state['gen_params'] = json.loads(g_row[0])
        except: st.session_state['gen_params'] = None
    else: st.session_state['gen_params'] = None
    
    if not st.session_state.get('gen_params') and st.session_state.get('tournament_data'):
        r1 = st.session_state['tournament_data'][1]
        p_names = []
        for m in r1['matches']: p_names.extend([p['name'] for p in m['team_a']] + [p['name'] for p in m['team_b']])
        p_names.extend([p['name'] for p in r1['waitlist']])
        st.session_state['gen_params'] = {
            'r_cnt': len(st.session_state['tournament_data']), 'c_cnt': len(r1['matches']),
            'opt': r1['option'], 'sub_opt': r1['option'], 'special_data': None, 'selected_names': p_names
        }
        
    st.session_state['pair_count'] = 1
    st.session_state['team_count'] = 1
    st.session_state['sync_done'] = True

if 'pair_count' not in st.session_state: st.session_state['pair_count'] = 1
if 'team_count' not in st.session_state: st.session_state['team_count'] = 1
if 'admin_logged_in' not in st.session_state: st.session_state['admin_logged_in'] = False

def get_admin_pwd():
    conn = sqlite3.connect('hote_tennis.db')
    pwd = conn.cursor().execute("SELECT value FROM settings WHERE key='admin_password'").fetchone()[0]
    conn.close(); return pwd

def update_admin_pwd(new_pwd):
    conn = sqlite3.connect('hote_tennis.db')
    conn.cursor().execute("UPDATE settings SET value=? WHERE key='admin_password'", (new_pwd,))
    conn.commit(); conn.close()

def get_members(exclude_guest=False):
    conn = sqlite3.connect('hote_tennis.db')
    query = "SELECT * FROM members WHERE is_active=1"
    if exclude_guest: query += " AND is_guest=0"
    query += " ORDER BY name ASC"
    df = pd.read_sql_query(query, conn)
    pts_df = pd.read_sql_query("SELECT name, SUM(points) as p, SUM(games) as g FROM points_log GROUP BY name", conn)
    conn.close()
    eff_dict = {}
    for _, row in pts_df.iterrows():
        if pd.notna(row['g']) and row['g'] > 0: eff_dict[row['name']] = round(row['p'] / row['g'], 1)
    df['eff_rating'] = df.apply(lambda x: eff_dict.get(x['name'], x['base_rating']), axis=1)
    return df

def get_point_rules():
    conn = sqlite3.connect('hote_tennis.db')
    df = pd.read_sql_query("SELECT * FROM point_rules", conn)
    conn.close()
    return df.set_index('category').to_dict('index')

# ==========================================
# 2단계: 승점 계산 및 알고리즘
# ==========================================
def get_team_type(team):
    genders = [p['gender'] for p in team]
    if genders.count('남') == 2: return 'MM'
    if genders.count('여') == 2: return 'FF'
    return 'MF'

def assign_points(match_id, match_date, team_a, team_b, result, rules):
    conn = sqlite3.connect('hote_tennis.db')
    c = conn.cursor()
    c.execute("DELETE FROM points_log WHERE source_id=?", (match_id,))

    if result not in ["입력 대기", "취소"]:
        type_a, type_b = get_team_type(team_a), get_team_type(team_b)
        pts_a, pts_b = 0, 0
        if type_a == 'MM' and type_b == 'MM': r = rules['남남 대 남남']
        elif type_a == 'FF' and type_b == 'FF': r = rules['여여 대 여여']
        elif type_a == 'MF' and type_b == 'MF': r = rules['남녀 대 남녀']
        elif type_a == 'MM' and type_b == 'MF': r = rules['남남 (혼복과 대결)']
        elif type_a == 'MF' and type_b == 'MM': r = rules['남녀 (남남과 대결)']
        else: r = rules['남남 대 남남']

        if type_a == 'MF' and type_b == 'MM': 
            if result == 'A팀 승리': pts_a, pts_b = r['win'], rules['남남 (혼복과 대결)']['lose']
            elif result == 'B팀 승리': pts_a, pts_b = r['lose'], rules['남남 (혼복과 대결)']['win']
            else: pts_a, pts_b = r['draw'], rules['남남 (혼복과 대결)']['draw']
        else:
            if result == 'A팀 승리': pts_a, pts_b = r['win'], r['lose']
            elif result == 'B팀 승리': pts_a, pts_b = r['lose'], r['win']
            else: pts_a, pts_b = r['draw'], r['draw']

        for p in team_a:
            if not p.get('is_guest', False): c.execute("INSERT INTO points_log (source_id, name, input_date, points, games) VALUES (?, ?, ?, ?, ?)", (match_id, p['name'], match_date, pts_a, 1))
        for p in team_b:
            if not p.get('is_guest', False): c.execute("INSERT INTO points_log (source_id, name, input_date, points, games) VALUES (?, ?, ?, ?, ?)", (match_id, p['name'], match_date, pts_b, 1))
    conn.commit(); conn.close()

# [핵심] 다중 배열 지원 알고리즘으로 업그레이드
def generate_single_round(players_df, court_count, match_option, special_data_list, sub_option, current_r_num, all_rounds_data):
    player_dicts = players_df.to_dict('records')
    random.shuffle(player_dicts) 
    needed_players = court_count * 4
    needed_waitlist = max(0, len(player_dicts) - needed_players)
    
    waitlist = []
    if needed_waitlist > 0:
        rest_counts = {p['name']: 0 for p in player_dicts}
        for r_num, r_data in all_rounds_data.items():
            if r_num != current_r_num:
                for w in r_data['waitlist']:
                    if w['name'] in rest_counts: rest_counts[w['name']] += 1
        sorted_by_rest = sorted(player_dicts, key=lambda x: rest_counts[x['name']])
        waitlist = sorted_by_rest[:needed_waitlist]
        
    playing_now = [p for p in player_dicts if p not in waitlist]
    matches = []

    # 1. 다중 특정 조건 매칭
    if match_option == "특정팀 대결 우선" and special_data_list:
        for matchup in special_data_list:
            if len(matches) >= court_count: break
            team_a_names, team_b_names = matchup
            team_a_players = [p for p in playing_now if p['name'] in team_a_names]
            team_b_players = [p for p in playing_now if p['name'] in team_b_names]
            if len(team_a_players) == 2 and len(team_b_players) == 2:
                matches.append({"team_a": team_a_players, "team_b": team_b_players, "winner": "입력 대기"})
                playing_now = [p for p in playing_now if p not in team_a_players and p not in team_b_players]

    elif match_option == "특정 페어 우선" and special_data_list:
        for pair in special_data_list:
            if len(matches) >= court_count: break
            p1_name, p2_name = pair
            team_a_players = [p for p in playing_now if p['name'] in (p1_name, p2_name)]
            if len(team_a_players) == 2:
                playing_now = [p for p in playing_now if p not in team_a_players]
                min_diff = float('inf'); best_opponents = None
                team_a_rating = sum(p['eff_rating'] for p in team_a_players)
                if len(playing_now) >= 2:
                    for opp in itertools.combinations(playing_now, 2):
                        diff = abs(team_a_rating - sum(p['eff_rating'] for p in opp))
                        if diff < min_diff: min_diff = diff; best_opponents = list(opp)
                    if best_opponents:
                        matches.append({"team_a": team_a_players, "team_b": best_opponents, "winner": "입력 대기"})
                        playing_now = [p for p in playing_now if p not in best_opponents]

    # 2. 2차 조건 적용 (남은 코트 채우기)
    rest_opt = sub_option if match_option in ["특정팀 대결 우선", "특정 페어 우선"] else match_option

    if rest_opt == "여복 우선":
        females = [p for p in playing_now if p['gender'] == '여']
        if len(females) >= 4 and len(matches) < court_count:
            matches.append({"team_a": females[0:2], "team_b": females[2:4], "winner": "입력 대기"})
            playing_now = [p for p in playing_now if p not in females[0:4]]

    elif rest_opt == "혼복 우선":
        males = [p for p in playing_now if p['gender'] == '남']
        females = [p for p in playing_now if p['gender'] == '여']
        while len(males) >= 2 and len(females) >= 2 and len(matches) < court_count:
            team_a = [males.pop(0), females.pop(0)]
            team_b = [males.pop(0), females.pop(0)]
            matches.append({"team_a": team_a, "team_b": team_b, "winner": "입력 대기"})
        playing_now = males + females

    # 3. 기본 조건으로 나머지 배정
    while len(playing_now) >= 4 and len(matches) < court_count:
        group = playing_now[:4]
        min_diff = float('inf')
        best_match = None
        for team_a, team_b in [((group[0], group[1]), (group[2], group[3])), ((group[0], group[2]), (group[1], group[3])), ((group[0], group[3]), (group[1], group[2]))]:
            diff = abs(sum(p['eff_rating'] for p in team_a) - sum(p['eff_rating'] for p in team_b))
            if diff < min_diff:
                min_diff = diff
                best_match = {"team_a": list(team_a), "team_b": list(team_b), "winner": "입력 대기"}
        matches.append(best_match)
        playing_now = playing_now[4:]

    waitlist.extend(playing_now)
    return {"matches": matches, "waitlist": waitlist, "option": match_option}

def render_horizontal_bracket(r_num, round_data, is_admin=False, filter_name="전체 보기"):
    is_my_waitlist = False
    
    if filter_name != "전체 보기":
        is_my_waitlist = filter_name in [p['name'] for p in round_data['waitlist']]
        filtered_matches = []
        for c_idx, match in enumerate(round_data['matches']):
            a_names = [p['name'] for p in match['team_a']]
            b_names = [p['name'] for p in match['team_b']]
            if filter_name in a_names or filter_name in b_names:
                filtered_matches.append((c_idx, match))
        if not is_my_waitlist and not filtered_matches:
            return False
    else:
        filtered_matches = list(enumerate(round_data['matches']))

    c1, c2 = st.columns([0.8, 0.2])
    with c1: st.markdown(f"<span style='font-size:22px; font-weight:900; color:#d84315;'>🏆 {r_num} 라운드</span> <span style='font-size:12px; color:gray;'>({round_data['option']})</span>", unsafe_allow_html=True)
    with c2: 
        if is_admin and st.button("🔄", key=f"regen_{r_num}"): return True

    if round_data['waitlist']:
        if filter_name == "전체 보기":
            w_names = [f"{p['name']}(G)" if p.get('is_guest',0) else p['name'] for p in round_data['waitlist']]
            st.markdown(f"<div style='font-size:13px; color:#e65100; margin-bottom:10px;'>💤 대기: {', '.join(w_names)}</div>", unsafe_allow_html=True)
        elif is_my_waitlist:
            st.markdown(f"<div style='font-size:15px; font-weight:bold; color:#e65100; margin-bottom:10px; padding:10px; background-color:#fff3e0; border-radius:5px; text-align:center;'>💤 이번 라운드는 휴식(대기)입니다.</div>", unsafe_allow_html=True)

    rules = get_point_rules()
    m_date = st.session_state['match_date']

    for c_idx, match in filtered_matches:
        team_a, team_b = match['team_a'], match['team_b']
        current_winner = match['winner']
        
        a_r1, a_r2 = team_a[0]['eff_rating'], team_a[1]['eff_rating']
        b_r1, b_r2 = team_b[0]['eff_rating'], team_b[1]['eff_rating']
        a_total, b_total = a_r1 + a_r2, b_r1 + b_r2
        diff = abs(a_total - b_total)
        
        ta1_n = f"{team_a[0]['name']}(G)" if team_a[0].get('is_guest',0) else team_a[0]['name']
        ta2_n = f"{team_a[1]['name']}(G)" if team_a[1].get('is_guest',0) else team_a[1]['name']
        tb1_n = f"{team_b[0]['name']}(G)" if team_b[0].get('is_guest',0) else team_b[0]['name']
        tb2_n = f"{team_b[1]['name']}(G)" if team_b[1].get('is_guest',0) else team_b[1]['name']

        st.caption(f"**[{c_idx+1} 코트]**")
        
        conn = sqlite3.connect('hote_tennis.db')
        mh_info = pd.read_sql_query("SELECT team_a_pos, team_b_pos FROM match_history WHERE id=?", conn, params=(f"{m_date}_R{r_num}_C{c_idx}",))
        conn.close()
        
        sv_ta_pos = mh_info.iloc[0]['team_a_pos'] if not mh_info.empty else "🎾 포/백 선택"
        sv_tb_pos = mh_info.iloc[0]['team_b_pos'] if not mh_info.empty else "🎾 포/백 선택"
        if sv_ta_pos in ["미지정", "A팀 포-백 미지정"]: sv_ta_pos = "🎾 포/백 선택"
        if sv_tb_pos in ["미지정", "B팀 포-백 미지정"]: sv_tb_pos = "🎾 포/백 선택"

        pos_opts_a = ["🎾 포/백 선택", f"{ta1_n}(포) / {ta2_n}(백)", f"{ta2_n}(포) / {ta1_n}(백)"]
        pos_opts_b = ["🎾 포/백 선택", f"{tb1_n}(포) / {tb2_n}(백)", f"{tb2_n}(포) / {tb1_n}(백)"]
        idx_a = pos_opts_a.index(sv_ta_pos) if sv_ta_pos in pos_opts_a else 0
        idx_b = pos_opts_b.index(sv_tb_pos) if sv_tb_pos in pos_opts_b else 0

        col1, col2, col3 = st.columns([4, 1.5, 4])
        with col1: 
            st.markdown(f"<div class='team-a'><b style='color:#006064; font-size:11px;'>[A] {a_total:.1f}</b><br><span class='team-name'>{ta1_n} & {ta2_n}</span></div>", unsafe_allow_html=True)
            if not is_admin: st.selectbox("A", pos_opts_a, index=idx_a, key=f"pa_{r_num}_{c_idx}", label_visibility="collapsed")
        with col2: 
            st.markdown(f"<div class='vs-text'>VS<br><span style='font-size:10px;color:#c62828;'>차이<br>{diff:.1f}</span></div>", unsafe_allow_html=True)
        with col3: 
            st.markdown(f"<div class='team-b'><b style='color:#b71c1c; font-size:11px;'>[B] {b_total:.1f}</b><br><span class='team-name'>{tb1_n} & {tb2_n}</span></div>", unsafe_allow_html=True)
            if not is_admin: st.selectbox("B", pos_opts_b, index=idx_b, key=f"pb_{r_num}_{c_idx}", label_visibility="collapsed")
        
        if not is_admin:
            c_rad, c_btn = st.columns([3.5, 1])
            with c_rad:
                opts = ["입력 대기", "A팀 승리", "B팀 승리", "무승부", "취소"]
                sel_idx = opts.index(current_winner) if current_winner in opts else 0
                selected_win = st.radio("결과", opts, index=sel_idx, key=f"win_{r_num}_{c_idx}", horizontal=True, label_visibility="collapsed")
            with c_btn:
                if st.button("저장", key=f"btn_{r_num}_{c_idx}", use_container_width=True):
                    st.session_state['tournament_data'][r_num]['matches'][c_idx]['winner'] = selected_win
                    save_active_tournament(m_date, st.session_state['tournament_data'], st.session_state.get('gen_params'))
                    match_id = f"{m_date}_R{r_num}_C{c_idx}"
                    conn = sqlite3.connect('hote_tennis.db')
                    
                    if selected_win in ["입력 대기", "취소"]: 
                        conn.cursor().execute("DELETE FROM match_history WHERE id=?", (match_id,))
                    else:
                        a_str = ",".join([p['name'] for p in team_a])
                        b_str = ",".join([p['name'] for p in team_b])
                        pa_val = st.session_state[f"pa_{r_num}_{c_idx}"]
                        pb_val = st.session_state[f"pb_{r_num}_{c_idx}"]
                        conn.cursor().execute("INSERT OR REPLACE INTO match_history (id, game_date, team_a, team_b, winner, team_a_pos, team_b_pos) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                              (match_id, m_date, a_str, b_str, selected_win, pa_val, pb_val))
                    conn.commit(); conn.close()
                    assign_points(match_id, m_date, team_a, team_b, selected_win, rules)
                    
                    msg = "경기 취소됨" if selected_win == "취소" else "저장됨"
                    st.success(msg); st.rerun()
        else:
            st.markdown(f"<div style='text-align:center; font-size:12px; color:blue; font-weight:bold;'>결과: {current_winner}</div>", unsafe_allow_html=True)
            
        st.markdown("<hr style='margin:8px 0; border:0; border-top:1px dashed #ccc;'>", unsafe_allow_html=True)
    return False

# ==========================================
# 3단계: 메인 메뉴 UI
# ==========================================
st.markdown("<h2 style='text-align: center; color: #1976d2; font-weight: 800; font-size: 1.5rem; white-space: nowrap;'>🎾 핫테 테니스 매니저</h2>", unsafe_allow_html=True)
menu = st.radio("메뉴 이동", ["대진표", "랭킹", "전적", "관리자"], horizontal=True, label_visibility="collapsed")

# ----------------------------------------
# 1. 대진표 보기
# ----------------------------------------
if menu == "대진표":
    conn = sqlite3.connect('hote_tennis.db')
    mh_dates_df = pd.read_sql_query("SELECT DISTINCT game_date FROM match_history ORDER BY game_date DESC", conn)
    conn.close()
    
    active_date = st.session_state['match_date']
    all_dates = mh_dates_df['game_date'].tolist()
    
    options = []
    if st.session_state['tournament_data']: options.append(f"{active_date} (오늘/현재)")
    for d in all_dates:
        if d != active_date: options.append(d)
        elif not st.session_state['tournament_data']: options.append(d)
        
    if not options:
        st.warning("생성된 대진표나 과거 기록이 없습니다.")
    else:
        all_members_df = get_members()
        all_names = all_members_df['name'].tolist()
        
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1: sel_opt = st.selectbox("📅 날짜 선택", options)
        with col_opt2: filter_name = st.selectbox("👤 내 대진표 보기", ["전체 보기"] + all_names)
        
        st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
        
        if sel_opt.startswith(active_date) and st.session_state['tournament_data']:
            for r_num, round_data in st.session_state['tournament_data'].items():
                render_horizontal_bracket(r_num, round_data, is_admin=False, filter_name=filter_name)

            conn = sqlite3.connect('hote_tennis.db')
            manual_df = pd.read_sql_query("SELECT id, team_a, team_b, winner FROM match_history WHERE game_date=? AND id LIKE 'MANUAL_%'", conn, params=(active_date,))
            conn.close()
            
            if not manual_df.empty:
                st.markdown("#### 🏃‍♂️ 현장 추가 매치")
                for idx, row in manual_df.iterrows():
                    ta_str, tb_str = row['team_a'].replace(',', ' & '), row['team_b'].replace(',', ' & ')
                    if filter_name == "전체 보기" or filter_name in row['team_a'] or filter_name in row['team_b']:
                        st.success(f"**[추가 {idx+1}]** {ta_str} VS {tb_str} ➔ **{row['winner']}**")

            if filter_name == "전체 보기":
                with st.expander("➕ 현장 게임 추가 등록", expanded=False):
                    with st.form("manual_match_form"):
                        m_col1, m_col2 = st.columns(2)
                        with m_col1:
                            st.markdown("<div class='team-a'><b>[A팀]</b></div>", unsafe_allow_html=True)
                            ma_1 = st.selectbox("A포", ["선택"] + all_names, key="ma_1")
                            ma_2 = st.selectbox("A백", ["선택"] + all_names, key="ma_2")
                        with m_col2:
                            st.markdown("<div class='team-b'><b>[B팀]</b></div>", unsafe_allow_html=True)
                            mb_1 = st.selectbox("B포", ["선택"] + all_names, key="mb_1")
                            mb_2 = st.selectbox("B백", ["선택"] + all_names, key="mb_2")
                            
                        m_res = st.radio("결과", ["A팀 승리", "B팀 승리", "무승부"], horizontal=True)
                        if st.form_submit_button("현장 게임 저장", type="primary", use_container_width=True):
                            sel_list = [ma_1, ma_2, mb_1, mb_2]
                            if "선택" in sel_list: st.error("4명 모두 선택해주세요.")
                            elif len(set(sel_list)) != 4: st.error("선수가 중복되었습니다.")
                            else:
                                t1_sorted, t2_sorted = tuple(sorted([ma_1, ma_2])), tuple(sorted([mb_1, mb_2]))
                                conn = sqlite3.connect('hote_tennis.db')
                                existing = pd.read_sql_query("SELECT team_a, team_b FROM match_history WHERE game_date=?", conn, params=(active_date,))
                                is_dup = False
                                for _, erow in existing.iterrows():
                                    ea, eb = tuple(sorted(erow['team_a'].split(','))), tuple(sorted(erow['team_b'].split(',')))
                                    if sorted([ea, eb]) == sorted([t1_sorted, t2_sorted]): is_dup = True; break
                                if is_dup:
                                    st.error("🚨 이미 등록된 동일 조합입니다.")
                                    conn.close()
                                else:
                                    t_a = all_members_df[all_members_df['name'].isin([ma_1, ma_2])].to_dict('records')
                                    t_b = all_members_df[all_members_df['name'].isin([mb_1, mb_2])].to_dict('records')
                                    match_id = f"MANUAL_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                                    a_str, b_str = f"{ma_1},{ma_2}", f"{mb_1},{mb_2}"
                                    ta_pos = f"{ma_1}(포)/{ma_2}(백)"
                                    tb_pos = f"{mb_1}(포)/{mb_2}(백)"
                                    conn.cursor().execute("INSERT INTO match_history (id, game_date, team_a, team_b, winner, team_a_pos, team_b_pos) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                                          (match_id, active_date, a_str, b_str, m_res, ta_pos, tb_pos))
                                    conn.commit(); conn.close()
                                    assign_points(match_id, active_date, t_a, t_b, m_res, get_point_rules())
                                    st.success("등록 완료!"); st.rerun()
        else:
            view_date = sel_opt.split(" ")[0]
            st.info(f"🔒 {view_date} 과거 대진 기록 (수정 불가)")
            conn = sqlite3.connect('hote_tennis.db')
            past_matches = pd.read_sql_query("SELECT * FROM match_history WHERE game_date=?", conn, params=(view_date,))
            conn.close()
            if past_matches.empty: st.write("해당 날짜에 저장된 기록이 없습니다.")
            else:
                for idx, row in past_matches.iterrows():
                    if filter_name == "전체 보기" or filter_name in row['team_a'] or filter_name in row['team_b']:
                        ta_str, tb_str = row['team_a'].replace(',', ' & '), row['team_b'].replace(',', ' & ')
                        st.markdown(f"<div style='border:1px solid #ddd; padding:10px; border-radius:5px; margin-bottom:5px; background-color:#fafafa; font-size:13px; text-align:center;'>"
                                    f"<b>{ta_str}</b> VS <b>{tb_str}</b> <br>➔ <span style='color:#1976d2; font-weight:bold;'>{row['winner']}</span></div>", unsafe_allow_html=True)

# ----------------------------------------
# 2. 랭킹 조회
# ----------------------------------------
elif menu == "랭킹":
    conn = sqlite3.connect('hote_tennis.db')
    df = pd.read_sql_query("SELECT name, input_date, points, games FROM points_log", conn)
    mh_df = pd.read_sql_query("SELECT id, game_date, team_a, team_b, winner FROM match_history WHERE winner != '입력 대기'", conn)
    conn.close()
    
    if df.empty:
        st.info("데이터가 없습니다.")
    else:
        df['month'] = df['input_date'].str[:7]
        available_months = sorted(df['month'].unique(), reverse=True)
        curr_m = datetime.now().strftime("%Y-%m")
        if curr_m not in available_months: available_months.insert(0, curr_m)
        
        c_rm1, c_rm2 = st.columns(2)
        with c_rm1: sel_month = st.selectbox("📅 년/월 선택", available_months)
        with c_rm2: rank_type = st.radio("랭킹 기준", ["월간 랭킹", "누적 랭킹"], horizontal=True)
        
        df_curr = df[df['month'] == sel_month].copy()
        
        sorted_dates = sorted(df_curr['input_date'].unique())
        date_cols = []
        for d in sorted_dates:
            try:
                dt_obj = datetime.strptime(d, "%Y-%m-%d")
                c_name = f"{dt_obj.month}/{dt_obj.day}"
            except: c_name = str(d)[-5:]
            if c_name not in date_cols: date_cols.append(c_name)

        members_df = get_members(exclude_guest=True)
        tot_stats = {n: {'w':0, 'l':0, 'd':0} for n in members_df['name']}
        mon_stats = {n: {'w':0, 'l':0, 'd':0} for n in members_df['name']}
        
        for _, m in mh_df.iterrows():
            ta, tb, winner = m['team_a'].split(','), m['team_b'].split(','), m['winner']
            m_month = m['game_date'][:7]
            for u in ta + tb:
                if u not in tot_stats: continue
                is_win = (u in ta and winner == "A팀 승리") or (u in tb and winner == "B팀 승리")
                is_draw = (winner == "무승부")
                if is_win: tot_stats[u]['w'] += 1
                elif is_draw: tot_stats[u]['d'] += 1
                else: tot_stats[u]['l'] += 1
                if m_month == sel_month:
                    if is_win: mon_stats[u]['w'] += 1
                    elif is_draw: mon_stats[u]['d'] += 1
                    else: mon_stats[u]['l'] += 1

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
                "sort_score_mon": mon_p,
                "sort_score_tot": tot_p
            }
            
            for d, col_name in zip(sorted_dates, date_cols):
                daily_log = mon_df[mon_df['input_date'] == d]
                if not daily_log.empty:
                    pts = int(daily_log['points'].sum())
                    waits = len(daily_log[daily_log['games'] == 0])
                    wins, losses, draws = 0, 0, 0
                    for _, m in mh_df[mh_df['game_date'] == d].iterrows():
                        ta, tb = m['team_a'].split(','), m['team_b'].split(',')
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
            
        if not records:
            st.info("해당 월에 데이터가 없습니다.")
        else:
            if rank_type == "월간 랭킹":
                final_df = pd.DataFrame(records).sort_values(by="sort_score_mon", ascending=False).drop(columns=['sort_score_mon', 'sort_score_tot'])
            else:
                final_df = pd.DataFrame(records).sort_values(by="sort_score_tot", ascending=False).drop(columns=['sort_score_mon', 'sort_score_tot'])
                
            final_df.insert(0, '순위', range(1, len(final_df) + 1))
            cols_order = ['순위', '이름'] + date_cols + ['월', '누적']
            final_df = final_df[cols_order]
            
            html_table = final_df.to_html(escape=False, index=False, justify='center', classes="rank-table")
