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

if 'pair_count' not in st.session_state: st.session_state['pair_count'] = 1
if 'team_count' not in st.session_state: st.session_state['team_count'] = 1

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
    
    st.session_state['sync_done'] = True

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
# 2단계: 승점 계산 및 강력한 다양성 매칭 알고리즘
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

# [핵심] 과거 파트너 및 상대방을 모두 추적하여 찢어놓는 "고인물 방지 알고리즘"
def generate_single_round(players_df, court_count, match_option, special_data_list, sub_option, current_r_num, all_rounds_data):
    player_dicts = players_df.to_dict('records')
    random.shuffle(player_dicts) 
    
    # 1. 예약자(고정) 명단 추출 (대기자 명단에서 제외시키기 위함)
    reserved_names = set()
    if match_option == "특정 페어 우선" and special_data_list:
        for pair in special_data_list: reserved_names.update(pair)
    elif match_option == "특정팀 대결 우선" and special_data_list:
        for matchup in special_data_list:
            reserved_names.update(matchup[0]); reserved_names.update(matchup[1])
            
    # 2. 과거 같은편/상대편 100% 추적 시스템
    past_partners = {p['name']: set() for p in player_dicts}
    past_opponents = {p['name']: set() for p in player_dicts}
    for r_num, r_data in all_rounds_data.items():
        if r_num >= current_r_num: continue
        for match in r_data['matches']:
            ta = [p['name'] for p in match['team_a']]
            tb = [p['name'] for p in match['team_b']]
            if len(ta) == 2:
                past_partners[ta[0]].add(ta[1]); past_partners[ta[1]].add(ta[0])
            if len(tb) == 2:
                past_partners[tb[0]].add(tb[1]); past_partners[tb[1]].add(tb[0])
            for pa in ta:
                for pb in tb:
                    past_opponents[pa].add(pb); past_opponents[pb].add(pa)
    
    needed_players = court_count * 4
    needed_waitlist = max(0, len(player_dicts) - needed_players)
    
    waitlist = []
    if needed_waitlist > 0:
        rest_counts = {p['name']: 0 for p in player_dicts}
        for r_num, r_data in all_rounds_data.items():
            if r_num != current_r_num:
                for w in r_data['waitlist']:
                    if w['name'] in rest_counts: rest_counts[w['name']] += 1
        
        # 예약자가 아닌 사람을 우선 대기자로 뽑음
        avail_for_wait = [p for p in player_dicts if p['name'] not in reserved_names]
        sorted_by_rest = sorted(avail_for_wait, key=lambda x: rest_counts[x['name']])
        waitlist = sorted_by_rest[:needed_waitlist]
        
        if len(waitlist) < needed_waitlist:
            rem = needed_waitlist - len(waitlist)
            avail_reserved = [p for p in player_dicts if p['name'] in reserved_names and p not in waitlist]
            waitlist.extend(sorted(avail_reserved, key=lambda x: rest_counts[x['name']])[:rem])
            
    playing_now = [p for p in player_dicts if p not in waitlist]
    matches = []
    formed_teams = []
    
    # [1단계] 특정팀 대결 우선 (아예 매치 자체를 픽스)
    if match_option == "특정팀 대결 우선" and special_data_list:
        for matchup in special_data_list:
            if len(matches) >= court_count: break
            ta_names, tb_names = matchup
            ta = [p for p in playing_now if p['name'] in ta_names]
            tb = [p for p in playing_now if p['name'] in tb_names]
            if len(ta) == 2 and len(tb) == 2:
                matches.append({"team_a": ta, "team_b": tb, "winner": "입력 대기"})
                for pp in ta + tb: playing_now.remove(pp)

    # [2단계] 특정 페어 우선 (팀만 묶어두고 나중에 다른 팀과 매칭)
    if match_option == "특정 페어 우선" and special_data_list:
        for pair in special_data_list:
            team = [p for p in playing_now if p['name'] in pair]
            if len(team) == 2:
                formed_teams.append(team)
                for pp in team: playing_now.remove(pp)

    rest_opt = sub_option if match_option in ["특정팀 대결 우선", "특정 페어 우선"] else match_option
    needed_teams = (court_count - len(matches)) * 2
    target_team_rating = (sum(p['eff_rating'] for p in playing_now) / (len(playing_now) / 2)) if len(playing_now) > 0 else 10.0

    # [3단계] 남은 사람들을 2차 기준에 맞춰 '새로운 팀'으로 묶어줌 (과거 파트너 회피 10000점 벌점)
    if rest_opt == "여복 우선":
        females = [p for p in playing_now if p['gender'] == '여']
        while len(females) >= 2 and len(formed_teams) < needed_teams:
            p1 = females.pop(0)
            best_p2 = None; best_p2_idx = -1; best_cost = float('inf')
            for i, p2 in enumerate(females):
                r_diff = abs((p1['eff_rating'] + p2['eff_rating']) - target_team_rating)
                cost = (10000 if p2['name'] in past_partners[p1['name']] else 0) + r_diff
                if cost < best_cost: best_cost = cost; best_p2 = p2; best_p2_idx = i
            if best_p2:
                formed_teams.append([p1, best_p2]); females.pop(best_p2_idx)
                playing_now.remove(p1); playing_now.remove(best_p2)

    if rest_opt == "혼복 우선":
        males = [p for p in playing_now if p['gender'] == '남']
        females = [p for p in playing_now if p['gender'] == '여']
        while len(males) >= 1 and len(females) >= 1 and len(formed_teams) < needed_teams:
            p1 = males.pop(0)
            best_p2 = None; best_p2_idx = -1; best_cost = float('inf')
            for i, p2 in enumerate(females):
                r_diff = abs((p1['eff_rating'] + p2['eff_rating']) - target_team_rating)
                cost = (10000 if p2['name'] in past_partners[p1['name']] else 0) + r_diff
                if cost < best_cost: best_cost = cost; best_p2 = p2; best_p2_idx = i
            if best_p2:
                formed_teams.append([p1, best_p2]); females.pop(best_p2_idx)
                playing_now.remove(p1); playing_now.remove(best_p2)

    while len(playing_now) >= 2 and len(formed_teams) < needed_teams:
        p1 = playing_now.pop(0)
        best_p2 = None; best_p2_idx = -1; best_cost = float('inf')
        for i, p2 in enumerate(playing_now):
            r_diff = abs((p1['eff_rating'] + p2['eff_rating']) - target_team_rating)
            cost = (10000 if p2['name'] in past_partners[p1['name']] else 0) + r_diff
            if cost < best_cost: best_cost = cost; best_p2 = p2; best_p2_idx = i
        if best_p2:
            formed_teams.append([p1, best_p2]); playing_now.pop(best_p2_idx)

    # [4단계] 만들어진 팀들(특정 페어 + 새 팀들)을 서로 코트에 매칭 (과거 상대팀 회피 10000점 벌점)
    while len(formed_teams) >= 2 and len(matches) < court_count:
        ta = formed_teams.pop(0)
        best_tb = None; best_tb_idx = -1; best_cost = float('inf')
        ta_rating = sum(p['eff_rating'] for p in ta)
        
        for i, tb in enumerate(formed_teams):
            tb_rating = sum(p['eff_rating'] for p in tb)
            diff = abs(ta_rating - tb_rating)
            penalty = 0
            for pa in ta:
                for pb in tb:
                    if pb['name'] in past_opponents[pa['name']]: penalty += 10000
            
            cost = diff + penalty
            if cost < best_cost:
                best_cost = cost; best_tb = tb; best_tb_idx = i
                
        if best_tb:
            matches.append({"team_a": ta, "team_b": best_tb, "winner": "입력 대기"})
            formed_teams.pop(best_tb_idx)

    waitlist.extend(playing_now)
    for t in formed_teams: waitlist.extend(t) # 남은 팀이 있으면 해체하여 대기로 보냄
    
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
            st.markdown(f"<div class='table-wrapper'>{html_table}</div>", unsafe_allow_html=True)
            
            st.divider()
            st.markdown("#### 🔍 날짜별 전적 확인")
            c_s1, c_s2 = st.columns(2)
            with c_s1: sel_name = st.selectbox("회원", ["선택"] + members_df['name'].tolist())
            with c_s2: sel_date = st.selectbox("날짜", ["선택"] + sorted_dates)
            
            if sel_date != "선택" and sel_name != "선택":
                day_matches = mh_df[mh_df['game_date'] == sel_date]
                conn = sqlite3.connect('hote_tennis.db')
                def is_in_match(row, n): return n in row['team_a'].split(',') or n in row['team_b'].split(',')
                user_matches = day_matches[day_matches.apply(lambda x: is_in_match(x, sel_name), axis=1)]
                pts_df = pd.read_sql_query("SELECT source_id, points, games FROM points_log WHERE input_date=? AND name=?", conn, params=(sel_date, sel_name))
                conn.close()
                
                if user_matches.empty and pts_df.empty:
                    st.info("기록이 없습니다.")
                else:
                    tot_pts_day = pts_df['points'].sum() if not pts_df.empty else 0
                    st.success(f"**🎾 {sel_name}님 ({sel_date}) : 총 획득 승점 {tot_pts_day}점**")
                    
                    for _, m in user_matches.iterrows():
                        ta_list, tb_list = m['team_a'].split(','), m['team_b'].split(',')
                        if sel_name in ta_list:
                            my_team, opp_team = " & ".join(ta_list), " & ".join(tb_list)
                            my_res = "무" if m['winner'] == '무승부' else "승" if m['winner'] == 'A팀 승리' else "패"
                            op_res = "무" if m['winner'] == '무승부' else "패" if m['winner'] == 'A팀 승리' else "승"
                        else:
                            my_team, opp_team = " & ".join(tb_list), " & ".join(ta_list)
                            my_res = "무" if m['winner'] == '무승부' else "승" if m['winner'] == 'B팀 승리' else "패"
                            op_res = "무" if m['winner'] == '무승부' else "패" if m['winner'] == 'B팀 승리' else "승"
                            
                        match_pts = pts_df[pts_df['source_id'] == m['id']]['points'].sum() if not pts_df.empty else 0
                        st.markdown(f"- **{my_team} ({my_res})** VS {opp_team} ({op_res}) : **+{match_pts}점**")
                        
                    try: wait_pts_row = pts_df[pd.to_numeric(pts_df['games']) == 0]
                    except: wait_pts_row = pd.DataFrame()
                        
                    if not wait_pts_row.empty:
                        w_pts = wait_pts_row['points'].sum()
                        w_cnt = len(wait_pts_row)
                        st.markdown(f"- 💤 **대기 ({w_cnt}회)** : **+{w_pts}점**")

# ----------------------------------------
# 3. 전적 조회
# ----------------------------------------
elif menu == "전적":
    st.subheader("📊 심층 전적 분석")
    regular_members_df = get_members(exclude_guest=True)
    if regular_members_df.empty: st.warning("등록된 정회원이 없습니다.")
    else:
        target_user = st.selectbox("분석할 회원 선택", regular_members_df['name'].tolist())
        if target_user:
            conn = sqlite3.connect('hote_tennis.db')
            history_df = pd.read_sql_query("SELECT * FROM match_history WHERE winner != '입력 대기'", conn)
            conn.close()
            
            if history_df.empty: st.info("저장된 기록이 없습니다.")
            else:
                my_wins, my_losses, my_draws = 0, 0, 0
                partner_stats, opponent_stats, opp_ind_stats = {}, {}, {}
                pos_stats = {'포': {'승':0, '패':0, '무':0}, '백': {'승':0, '패':0, '무':0}}
                
                for _, match in history_df.iterrows():
                    a_names, b_names, winner = match['team_a'].split(','), match['team_b'].split(','), match['winner']
                    pos_a = match.get('team_a_pos', '🎾 포/백 선택')
                    pos_b = match.get('team_b_pos', '🎾 포/백 선택')
                    
                    if target_user in a_names or target_user in b_names:
                        my_team = a_names if target_user in a_names else b_names
                        opp_team = b_names if target_user in a_names else a_names
                        partner = my_team[1] if len(my_team)>1 and my_team[0] == target_user else my_team[0]
                        opp_str = f"{opp_team[0]} & {opp_team[1]}" if len(opp_team)>1 else opp_team[0]
                        
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
                        
                        if partner not in partner_stats: partner_stats[partner] = {'승':0, '패':0, '무':0, 'list':[]}
                        if is_win: partner_stats[partner]['승'] += 1
                        elif is_draw: partner_stats[partner]['무'] += 1
                        else: partner_stats[partner]['패'] += 1
                        partner_stats[partner]['list'].append({"opp": opp_str, "res": res_text, "date": match['game_date']})
                            
                        if opp_str not in opponent_stats: opponent_stats[opp_str] = {'승':0, '패':0, '무':0, 'list':[]}
                        if is_win: opponent_stats[opp_str]['승'] += 1
                        elif is_draw: opponent_stats[opp_str]['무'] += 1
                        else: opponent_stats[opp_str]['패'] += 1
                        opponent_stats[opp_str]['list'].append({"partner": partner, "res": res_text, "date": match['game_date']})

                        for opp_p in opp_team:
                            if opp_p not in opp_ind_stats: opp_ind_stats[opp_p] = {'승':0, '패':0, '무':0}
                            if is_win: opp_ind_stats[opp_p]['승'] += 1
                            elif is_draw: opp_ind_stats[opp_p]['무'] += 1
                            else: opp_ind_stats[opp_p]['패'] += 1
                
                tot_games = my_wins + my_losses + my_draws
                if tot_games == 0: st.warning("경기 데이터가 없습니다.")
                else:
                    def get_best_worst(stats_dict):
                        rates = []
                        for k, v in stats_dict.items():
                            t = v['승'] + v['무'] + v['패']
                            if t > 0: rates.append({"name": k, "rate": round((v['승']/t)*100, 1), "tot": t, "w": v['승'], "d": v['무'], "l": v['패']})
                        if not rates: return None, None
                        rates.sort(key=lambda x: (x['rate'], x['tot']))
                        return rates[-1], rates[0] 

                    b_pt, w_pt = get_best_worst(partner_stats) 
                    b_op_tm, w_op_tm = get_best_worst(opponent_stats)
                    b_op_id, w_op_id = get_best_worst(opp_ind_stats)

                    st.success(f"**🥇 {target_user}님의 종합 전적: {tot_games}전 {my_wins}승 {my_draws}무 {my_losses}패 (승률 {round((my_wins/tot_games)*100,1)}%)**")
                    
                    st.markdown("#### 🎯 나의 상세 분석 리포트")
                    st.markdown("##### 🍯 베스트")
                    if b_pt:
                        with st.expander(f"🤝 찰떡 파트너: **{b_pt['name']}** ({b_pt['rate']}%)"):
                            st.write(f"└ 함께 **{b_pt['tot']}전 {b_pt['w']}승 {b_pt['d']}무 {b_pt['l']}패**를 기록했습니다.")
                    if b_op_tm:
                        with st.expander(f"💸 자판기(팀): **{b_op_tm['name']}** ({b_op_tm['rate']}%)"):
                            st.write(f"└ 해당 팀을 만나 **{b_op_tm['tot']}전 {b_op_tm['w']}승 {b_op_tm['d']}무 {b_op_tm['l']}패**를 기록했습니다.")
                    if b_op_id:
                        with st.expander(f"💸 자판기(개인): **{b_op_id['name']}** ({b_op_id['rate']}%)"):
                            st.write(f"└ 해당 선수를 상대로 **{b_op_id['tot']}전 {b_op_id['w']}승 {b_op_id['d']}무 {b_op_id['l']}패**를 기록했습니다.")

                    st.markdown("##### 👿 워스트")
                    if w_op_tm:
                        with st.expander(f"💢 천적(팀): **{w_op_tm['name']}** ({w_op_tm['rate']}%)"):
                            st.write(f"└ 해당 팀을 만나 **{w_op_tm['tot']}전 {w_op_tm['w']}승 {w_op_tm['d']}무 {w_op_tm['l']}패**를 기록했습니다.")
                    if w_op_id:
                        with st.expander(f"💢 천적(개인): **{w_op_id['name']}** ({w_op_id['rate']}%)"):
                            st.write(f"└ 해당 선수를 상대로 **{w_op_id['tot']}전 {w_op_id['w']}승 {w_op_id['d']}무 {w_op_id['l']}패**를 기록했습니다.")

                    st.divider()
                    st.markdown("#### 🏸 포지션별 승률")
                    pf, pb = pos_stats['포'], pos_stats['백']
                    ptot, btot = pf['승']+pf['패']+pf['무'], pb['승']+pb['패']+pb['무']
                    prate = round((pf['승']/ptot)*100, 1) if ptot > 0 else 0
                    brate = round((pb['승']/btot)*100, 1) if btot > 0 else 0
                    
                    st.info(f"**🔴 포(Fore):** {pf['승']}승 {pf['무']}무 {pf['패']}패 (승률 {prate}%)")
                    st.error(f"**🔵 백(Back):** {pb['승']}승 {pb['무']}무 {pb['패']}패 (승률 {brate}%)")

                    st.divider()
                    st.markdown("#### 🤝 파트너별 상세 승률")
                    sorted_pt = sorted(partner_stats.items(), key=lambda x: x[1]['승']/(x[1]['승']+x[1]['무']+x[1]['패']), reverse=True)
                    for p_name, data in sorted_pt:
                        tot = data['승'] + data['무'] + data['패']
                        with st.expander(f"**{p_name}** | {data['승']}승 {data['무']}무 {data['패']}패"):
                            for item in data['list']: st.write(f"📅 {item['date']} | vs **{item['opp']}** ➔ {item['res']}")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    st.markdown("#### ⚔️ 상대팀별 상세 승률")
                    sorted_op = sorted(opponent_stats.items(), key=lambda x: x[1]['승']/(x[1]['승']+x[1]['무']+x[1]['패']), reverse=True)
                    for o_name, data in sorted_op:
                        tot = data['승'] + data['무'] + data['패']
                        with st.expander(f"**{o_name}** | {data['승']}승 {data['무']}무 {data['패']}패"):
                            for item in data['list']: st.write(f"📅 {item['date']} | with **{item['partner']}** ➔ {item['res']}")

# ----------------------------------------
# 4. 관리자 메뉴
# ----------------------------------------
elif menu == "관리자":
    st.subheader("⚙️ 관리자 시스템")
    if not st.session_state['admin_logged_in']:
        if st.text_input("비밀번호 (초기: 1234)", type="password") == get_admin_pwd():
            st.session_state['admin_logged_in'] = True; st.rerun()
                
    if st.session_state['admin_logged_in']:
        if st.button("로그아웃"): st.session_state['admin_logged_in'] = False; st.rerun()
        
        with st.expander("⚠️ 데이터 초기화 (테스트 기록 삭제)", expanded=False):
            st.warning("지금까지 입력된 모든 대진표, 경기 결과, 승점(과거 엑셀 데이터 포함)이 영구적으로 삭제됩니다. (회원 명부와 승점 규칙은 유지됩니다)")
            confirm_reset = st.checkbox("네, 모든 데이터를 삭제하는 것에 동의합니다.")
            if confirm_reset:
                if st.button("🔥 전체 데이터 초기화 실행", type="primary", use_container_width=True):
                    conn = sqlite3.connect('hote_tennis.db')
                    c = conn.cursor()
                    c.execute("DELETE FROM match_history")
                    c.execute("DELETE FROM points_log")
                    c.execute("DELETE FROM settings WHERE key IN ('active_match_date', 'active_tournament_json', 'active_gen_params_json')")
                    conn.commit(); conn.close()
                    st.session_state['tournament_data'] = {}
                    st.session_state['gen_params'] = None
                    st.success("테스트 데이터가 완벽하게 삭제되었습니다! 이제 새로 시작할 수 있습니다.")
                    st.rerun()
                    
        with st.expander("🔄 현장 대진표 수정 (결원 대체)", expanded=False):
            if st.session_state['tournament_data']:
                round_opts = list(st.session_state['tournament_data'].keys())
                edit_r = st.selectbox("수정할 라운드 선택", round_opts)

                r_data = st.session_state['tournament_data'][edit_r]
                
                playing_names = []
                for m in r_data['matches']: 
                    playing_names.extend([p['name'] for p in m['team_a']] + [p['name'] for p in m['team_b']])
                wait_names = [p['name'] for p in r_data['waitlist']]
                
                st.markdown("##### 🔄 대체 선수 선택")
                out_p = st.selectbox("🔽 빠질 사람 (현재 코트 배정자만)", playing_names)
                
                valid_waitlisters = [w for w in wait_names if w != out_p]
                in_options = []
                if valid_waitlisters:
                    for w in valid_waitlisters:
                        in_options.append(f"🟢 [대기자] {w}")
                else:
                    gen_params = st.session_state.get('gen_params', {})
                    attending_names = gen_params.get('selected_names', playing_names + wait_names)
                    all_member_names = get_members()['name'].tolist()
                    non_attending = [n for n in all_member_names if n not in attending_names]
                    for n in non_attending:
                        in_options.append(f"⚪ [미참석] {n}")

                if not in_options: 
                    in_options = ["선택가능 대체자 없음"]

                in_p_label = st.selectbox("🔼 들어갈 사람 (대체자)", in_options)

                if st.button("해당 라운드 코트 교체", type="primary", use_container_width=True):
                    if in_p_label == "선택가능 대체자 없음": 
                        st.error("대체할 수 있는 선수가 없습니다.")
                    else:
                        in_p_name = in_p_label.replace("🟢 [대기자] ", "").replace("⚪ [미참석] ", "")
                        new_p_data = get_members()[get_members()['name'] == in_p_name].to_dict('records')[0]

                        if "대기자" in in_p_label:
                            r_data['waitlist'] = [w for w in r_data['waitlist'] if w['name'] != in_p_name]

                        for m_idx, m in enumerate(r_data['matches']):
                            for i, p in enumerate(m['team_a']):
                                if p['name'] == out_p: m['team_a'][i] = new_p_data; m['winner'] = "입력 대기"
                            for i, p in enumerate(m['team_b']):
                                if p['name'] == out_p: m['team_b'][i] = new_p_data; m['winner'] = "입력 대기"

                        conn = sqlite3.connect('hote_tennis.db')
                        wl_id = f"{st.session_state['match_date']}_R{edit_r}_Waitlist"
                        conn.cursor().execute("DELETE FROM points_log WHERE source_id=?", (wl_id,))
                        rules = get_point_rules()
                        for w in r_data['waitlist']:
                            if not w.get('is_guest', False):
                                conn.cursor().execute("INSERT INTO points_log (source_id, name, input_date, points, games) VALUES (?, ?, ?, ?, ?)",
                                                      (wl_id, w['name'], st.session_state['match_date'], rules['대기자']['win'], 0))
                        
                        for c_idx, m in enumerate(r_data['matches']):
                             if m['winner'] == "입력 대기":
                                 m_id = f"{st.session_state['match_date']}_R{edit_r}_C{c_idx}"
                                 conn.cursor().execute("DELETE FROM match_history WHERE id=?", (m_id,))
                                 conn.cursor().execute("DELETE FROM points_log WHERE source_id=?", (m_id,))

                        conn.commit(); conn.close()
                        st.session_state['tournament_data'][edit_r] = r_data
                        gen_params = st.session_state.get('gen_params')
                        save_active_tournament(st.session_state['match_date'], st.session_state['tournament_data'], gen_params)
                        
                        st.success(f"{edit_r}라운드 {out_p} ➔ {in_p_name} 교체 완료! 해당 코트 결과가 초기화되었습니다.")
                        st.rerun()
            else:
                st.info("현재 생성된 대진표가 없습니다.")

        with st.expander("📥 과거 데이터(엑셀) 일괄 업로드", expanded=False):
            st.info("이전에 사용하던 엑셀 데이터를 업로드하여 랭킹에 합산할 수 있습니다.")
            st.markdown("**[필수 엑셀 양식]** 첫 줄(헤더)에 아래 4개 항목을 정확히 적어주세요.\n"
                        "* `날짜` (예: 2025-12-01) | `이름` | `승점` | `게임수`")
            uploaded_file = st.file_uploader("엑셀 파일 첨부 (.xlsx, .xls)", type=["xlsx", "xls"])
            if uploaded_file is not None:
                if st.button("데이터 업로드 실행", type="primary", use_container_width=True):
                    try:
                        df_up = pd.read_excel(uploaded_file)
                        req_cols = ['날짜', '이름', '승점', '게임수']
                        if not all(c in df_up.columns for c in req_cols):
                            st.error("엑셀 양식이 맞지 않습니다. 열(Column) 이름을 확인해주세요.")
                        else:
                            conn = sqlite3.connect('hote_tennis.db')
                            c = conn.cursor()
                            c.execute("DELETE FROM points_log WHERE source_id='EXCEL_IMPORT'")
                            for _, row in df_up.iterrows():
                                if pd.notna(row['이름']) and pd.notna(row['승점']):
                                    date_str = str(row['날짜'])[:10]
                                    c.execute("INSERT INTO points_log (source_id, name, input_date, points, games) VALUES (?, ?, ?, ?, ?)", 
                                              ('EXCEL_IMPORT', row['이름'], date_str, int(row['승점']), int(row['게임수'])))
                            conn.commit(); conn.close()
                            st.success("🎉 과거 데이터가 성공적으로 병합되었습니다!")
                    except Exception as e:
                        st.error(f"엑셀을 읽는 중 에러가 발생했습니다: {e}\n(PC에 openpyxl 모듈이 설치되어 있어야 합니다)")

        with st.expander("🛠️ 승점 부여 방식 설정", expanded=False):
            conn = sqlite3.connect('hote_tennis.db')
            rules_df = pd.read_sql_query("SELECT category as '구분', win as '승', lose as '패', draw as '무승부' FROM point_rules", conn)
            edited_df = st.data_editor(rules_df, hide_index=True, use_container_width=True)
            if st.button("변경한 승점 저장"):
                c = conn.cursor()
                for _, row in edited_df.iterrows():
                    c.execute("UPDATE point_rules SET win=?, lose=?, draw=? WHERE category=?", (row['승'], row['패'], row['무승부'], row['구분']))
                conn.commit(); st.success("저장 완료!")
            conn.close()

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
            with c_reg1:
                new_n = st.text_input("이름")
                new_g = st.selectbox("성별", ["남", "여"])
            with c_reg2:
                new_r = st.number_input("초기 평점", value=5.0)
                is_guest = st.checkbox("게스트로 등록")
            if st.button("신규 회원 추가", type="primary", use_container_width=True):
                if new_n:
                    conn = sqlite3.connect('hote_tennis.db')
                    conn.cursor().execute("INSERT INTO members (name, gender, base_rating, is_active, is_guest) VALUES (?, ?, ?, 1, ?)", (new_n, new_g, new_r, 1 if is_guest else 0))
                    conn.commit(); conn.close(); st.rerun()
                    
            st.divider()
            st.markdown("##### 🔄 게스트 ➔ 정회원 승급 (전적 소급)")
            gst_names = gst_df['이름'].tolist()
            up_g = st.selectbox("승급할 게스트 선택", gst_names if gst_names else ["승급할 게스트 없음"])
            if st.button("정회원으로 승급", use_container_width=True):
                if up_g != "승급할 게스트 없음":
                    conn = sqlite3.connect('hote_tennis.db')
                    conn.cursor().execute("UPDATE members SET is_guest=0 WHERE name=?", (up_g,))
                    conn.commit(); conn.close()
                    retro_calculate_points_for_user(up_g)
                    st.success(f"🎉 {up_g}님이 정회원으로 승급되었습니다! 과거 전적이 랭킹에 완벽히 합산됩니다.")
                    st.rerun()
                    
            st.divider()
            st.markdown("##### ❌ 회원 삭제")
            del_n = st.selectbox("삭제할 사람", members_df['name'].tolist())
            if st.button("회원 삭제", use_container_width=True):
                conn = sqlite3.connect('hote_tennis.db')
                conn.cursor().execute("UPDATE members SET is_active=0 WHERE name=?", (del_n,))
                conn.commit(); conn.close(); st.rerun()

        st.divider()
        st.subheader("🎾 대진표 생성 및 관리")
        
        full_df = get_members()
        selected_names = []
        cols = st.columns(3)
        for idx, row in full_df.iterrows():
            with cols[idx % 3]:
                disp_name = f"{row['name']}(G)" if row['is_guest'] == 1 else row['name']
                if st.checkbox(disp_name, value=True, key=f"chk_{row['name']}"): selected_names.append(row['name'])
        
        st.info(f"✅ 선택된 참여 인원: **{len(selected_names)}명**")
                
        m_date = st.text_input("📅 대진표 적용 날짜", value=st.session_state['match_date'])
        
        c1, c2 = st.columns(2)
        with c1: r_cnt = st.number_input("라운드 수", 1, 10, 4)
        with c2: c_cnt = st.number_input("코트 수", 1, 5, 2)
        
        c3, c4 = st.columns(2)
        with c3: opt = st.selectbox("1차 기준", ["기본 (평점 우선)", "혼복 우선", "여복 우선", "특정 페어 우선", "특정팀 대결 우선"])
        with c4:
            sub_opt = "기본 (평점 우선)"
            if opt in ["특정 페어 우선", "특정팀 대결 우선"]:
                sub_opt = st.selectbox("2차 기준(나머지)", ["기본 (평점 우선)", "혼복 우선", "여복 우선"])

        special_data_list = []
        if opt == "특정 페어 우선":
            st.caption("고정할 페어(들)를 구성하세요.")
            for i in range(st.session_state['pair_count']):
                st.markdown(f"**[{i+1}번 페어]**")
                c_p1, c_p2 = st.columns(2)
                with c_p1: p1_a = st.selectbox(f"선수 1", ["선택"] + selected_names, key=f"p1_a_{i}")
                with c_p2: p1_b = st.selectbox(f"선수 2", ["선택"] + selected_names, key=f"p1_b_{i}")
                if p1_a != "선택" and p1_b != "선택":
                    special_data_list.append((p1_a, p1_b))
            
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("➕ 페어 추가하기"): st.session_state['pair_count'] += 1; st.rerun()
            with c_btn2:
                if st.session_state['pair_count'] > 1 and st.button("➖ 페어 줄이기"): st.session_state['pair_count'] -= 1; st.rerun()
                
        elif opt == "특정팀 대결 우선":
            st.caption("고정할 대결(들)을 구성하세요.")
            for i in range(st.session_state['team_count']):
                st.markdown(f"**[{i+1}번 매치]**")
                c_t1, c_t2 = st.columns(2)
                with c_t1: ta_1 = st.selectbox(f"A팀-1", ["선택"] + selected_names, key=f"ta_1_{i}")
                with c_t2: ta_2 = st.selectbox(f"A팀-2", ["선택"] + selected_names, key=f"ta_2_{i}")
                c_t3, c_t4 = st.columns(2)
                with c_t3: tb_1 = st.selectbox(f"B팀-1", ["선택"] + selected_names, key=f"tb_1_{i}")
                with c_t4: tb_2 = st.selectbox(f"B팀-2", ["선택"] + selected_names, key=f"tb_2_{i}")
                if "선택" not in [ta_1, ta_2, tb_1, tb_2]:
                    special_data_list.append(((ta_1, ta_2), (tb_1, tb_2)))

            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("➕ 대결 추가하기"): st.session_state['team_count'] += 1; st.rerun()
            with c_btn2:
                if st.session_state['team_count'] > 1 and st.button("➖ 대결 줄이기"): st.session_state['team_count'] -= 1; st.rerun()

        if st.button("🚀 대진표 생성 (기존 초기화)", type="primary", use_container_width=True):
            st.session_state['match_date'] = m_date 
            p_df = full_df[full_df['name'].isin(selected_names)]
            
            gen_params = {
                'r_cnt': r_cnt, 'c_cnt': c_cnt, 'opt': opt, 'sub_opt': sub_opt,
                'special_data': special_data_list, 'selected_names': selected_names
            }
            st.session_state['gen_params'] = gen_params
            
            st.session_state['tournament_data'] = {}
            for r in range(1, r_cnt + 1):
                round_result = generate_single_round(p_df, c_cnt, opt, special_data_list, sub_opt, r, st.session_state['tournament_data'])
                st.session_state['tournament_data'][r] = round_result
                
                rules = get_point_rules()
                wl_id = f"{m_date}_R{r}_Waitlist"
                conn = sqlite3.connect('hote_tennis.db')
                conn.cursor().execute("DELETE FROM points_log WHERE source_id=?", (wl_id,))
                for w in round_result['waitlist']:
                    if not w.get('is_guest', False):
                        conn.cursor().execute("INSERT INTO points_log (source_id, name, input_date, points, games) VALUES (?, ?, ?, ?, ?)", 
                                              (wl_id, w['name'], m_date, rules['대기자']['win'], 0))
                conn.commit(); conn.close()
            
            save_active_tournament(m_date, st.session_state['tournament_data'], gen_params)
            st.success("생성 완료!")

        if st.session_state['tournament_data']:
            st.markdown("<br><h3 style='color:#1976D2;'>👇 생성된 대진표 (평점 확인용)</h3>", unsafe_allow_html=True)
            for r_num, round_data in st.session_state['tournament_data'].items():
                if render_horizontal_bracket(r_num, round_data, is_admin=True, filter_name="전체 보기"):
                    p_df = full_df[full_df['name'].isin(selected_names)]
                    st.session_state['tournament_data'][r_num] = generate_single_round(p_df, c_cnt, opt, special_data_list, sub_opt, r_num, st.session_state['tournament_data'])
                    save_active_tournament(m_date, st.session_state['tournament_data'], st.session_state.get('gen_params'))
                    st.rerun()
