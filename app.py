import streamlit as st, sqlite3, pandas as pd, random, json, re
from datetime import datetime

# ==========================================
# 모바일 UI 최적화 및 홈화면 아이콘 세팅
# ==========================================
st.set_page_config(page_title="핫테 매니저", page_icon="🎾", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 1.5rem; padding-left: 0.5rem; padding-right: 0.5rem; max-width: 100%; overflow-x: hidden; }
    [data-testid="collapsedControl"] { display: none; }
    h1, h2, h3, h4, h5 { margin-bottom: 0.4rem !important; margin-top: 0.4rem !important; }
    div[role="radiogroup"] { justify-content: space-around; background-color: #f0f2f6; padding: 5px; border-radius: 8px; margin-bottom: 8px;}
    .stRadio label { font-size: 14px !important; font-weight: bold; cursor: pointer; padding: 5px; }
    
    .table-wrapper { overflow-x: auto; width: 100%; max-height: 65vh; margin-bottom: 1rem; border: 1px solid #ddd; }
    table.rank-table { border-collapse: separate; border-spacing: 0; width: 100%; text-align: center; font-size: 12px; white-space: nowrap; }
    table.rank-table td, table.rank-table th { padding: 8px 5px; border-bottom: 1px solid #ddd; border-right: 1px solid #ddd; text-align: center; }
    table.rank-table th { position: sticky; top: 0; background-color: #f0f2f6; z-index: 4; }
    
    .podium-box { border-radius: 10px; padding: 12px 5px; text-align: center; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .gold { background: linear-gradient(135deg, #FFD700 0%, #FDB931 100%); color: #4A3A00; }
    .silver { background: linear-gradient(135deg, #e2ebf0 0%, #cfd9df 100%); color: #333; }
    .bronze { background: linear-gradient(135deg, #d4af37 0%, #aa6c39 100%); color: #FFF; }
    
    .acc-card { padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; font-weight: bold; }
    .acc-balance { background-color: #f1f8e9; border: 2px solid #2e7d32; color: #1b5e20; font-size: 20px; }

    .pulse-bg { animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1단계: DB 연결 및 초기화 (회계 테이블 추가)
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
        c.execute('''CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, gender TEXT, base_rating REAL, is_active INTEGER, is_guest INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, category TEXT, description TEXT, income INTEGER DEFAULT 0, expense INTEGER DEFAULT 0, member_name TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS points_log (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, input_date TEXT, points INTEGER, games INTEGER, source_id TEXT, score_won INTEGER DEFAULT 0, score_lost INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS match_history (id TEXT PRIMARY KEY, game_date TEXT, team_a TEXT, team_b TEXT, winner TEXT, score_a INTEGER, score_b INTEGER, team_a_pos TEXT, team_b_pos TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, event_date TEXT, event_name TEXT, event_type TEXT, team_1_name TEXT, team_2_name TEXT, team_1_members TEXT, team_2_members TEXT, participants TEXT, bracket_json TEXT, gen_params_json TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS event_matches (id TEXT PRIMARY KEY, event_id INTEGER, round INTEGER, court INTEGER, team_a TEXT, team_b TEXT, winner TEXT, score_a INTEGER, score_b INTEGER, team_a_pos TEXT, team_b_pos TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS event_points_log (id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER, name TEXT, points INTEGER, games INTEGER, match_id TEXT, result TEXT, score_won INTEGER DEFAULT 0, score_lost INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS point_rules (category TEXT PRIMARY KEY, win INTEGER, lose INTEGER, draw INTEGER)''')
        
        c.execute("SELECT COUNT(*) FROM point_rules")
        if c.fetchone()[0] == 0:
            default_rules = [("남남 대 남남", 3, 0, 1), ("여여 대 여여", 3, 0, 1), ("남녀 대 남녀", 3, 0, 1), ("남남 (혼복과 대결)", 3, 1, 1), ("남녀 (남남과 대결)", 5, 0, 2), ("단식", 3, 0, 1), ("대기자", 2, 0, 0), ("최소 게임수 (이벤트용)", 2, 0, 0)]
            c.executemany("INSERT INTO point_rules VALUES (?, ?, ?, ?)", default_rules)
        conn.commit()
    finally: conn.close()

init_db()

# 세션 상태 관리
if 'admin_logged_in' not in st.session_state: st.session_state['admin_logged_in'] = False

# 공용 함수들
def strip_gender(s): return s.replace('(여)','').replace('(남)','').replace('(G)','').strip() if isinstance(s, str) else s

def get_members(exclude_guest=False):
    conn = get_db_conn()
    try:
        q = "SELECT * FROM members WHERE is_active=1"
        if exclude_guest: q += " AND is_guest=0"
        df = pd.read_sql_query(q + " ORDER BY name ASC", conn)
        # 평점 보정 로직 (생략 - 기존 로직 유지 가능)
        df['eff_rating'] = df['base_rating']
        return df
    finally: conn.close()

def get_point_rules():
    conn = get_db_conn()
    try: return pd.read_sql_query("SELECT * FROM point_rules", conn).set_index('category').to_dict('index')
    finally: conn.close()

# ==========================================
# 2단계: 핵심 로직 (AI 매칭 & 분석)
# ==========================================
def calculate_earned_points(team_a, team_b, winner):
    rules = get_point_rules()
    if not team_a or not team_b: return 0, 0
    # (룰에 따른 승점 계산 로직...)
    return 3, 0 # 예시 반환

def generate_single_round(players_df, court_count, play_mode, match_option, special_data_list, sub_option, current_r_num, all_rounds_data, team_rosters=None):
    player_dicts = players_df.to_dict('records')
    for p in player_dicts: p['rand'] = random.random()
    needed_players = court_count * (2 if play_mode == "단식" else 4)
    needed_waitlist = max(0, len(player_dicts) - needed_players)
    
    play_counts = {p['name']: 0 for p in player_dicts}
    rounds_present = {p['name']: 0 for p in player_dicts}
    
    for r_num, r_data in all_rounds_data.items():
        for match in r_data.get('matches', []):
            if match['winner'] == '취소': continue
            for p in match['team_a'] + match['team_b']:
                if p['name'] in play_counts: play_counts[p['name']] += 1
                if p['name'] in rounds_present: rounds_present[p['name']] += 1
        for w in r_data.get('waitlist', []):
            if w['name'] in rounds_present: rounds_present[w['name']] += 1
            
    def waitlist_sort_key(x):
        avail = rounds_present.get(x['name'], 0)
        played = play_counts.get(x['name'], 0)
        ratio = played / max(1, avail) # 참가 라운드 대비 출전 비율 (지각자 보정)
        return (ratio, played, x['rand'])

    sorted_players = sorted(player_dicts, key=waitlist_sort_key, reverse=True)
    waitlist = sorted_players[:needed_waitlist]
    playing_now = [p for p in player_dicts if p not in waitlist]
    # (이후 매칭 로직...)
    return {"matches": [], "waitlist": waitlist, "option": match_option}

# ==========================================
# 3단계: 메인 메뉴 UI
# ==========================================
st.markdown("<h2 style='text-align: center; color: #d32f2f; font-weight: 900; font-size: 1.8rem;'>🎾 핫테 매니저</h2>", unsafe_allow_html=True)
menu = st.radio("메인메뉴", ["정규리그", "이벤트", "관리자"], horizontal=True, label_visibility="collapsed")

# ----------------------------------------
# 1. 정규리그 메뉴
# ----------------------------------------
if menu == "정규리그":
    reg_sub = st.radio("정규메뉴", ["📅 대진표/순위", "📊 랭킹", "👤 개인분석"], horizontal=True, label_visibility="collapsed")
    
    if "대진표" in reg_sub:
        st.info("정규 대진표 및 실시간 순위 화면")
        # (기존 정규 대진표 렌더링 로직...)
        
    elif "랭킹" in reg_sub:
        st.info("월간/누적 랭킹 화면")
        # (기존 랭킹 렌더링 로직...)
        
    elif "개인분석" in reg_sub:
        st.subheader("👤 개인별 상세 전적 분석")
        members = get_members()['name'].tolist()
        target = st.selectbox("분석할 회원 선택", members)
        
        if target:
            conn = get_db_conn()
            # 정규 + 이벤트 전적 합산
            m1 = pd.read_sql_query("SELECT team_a, team_b, winner, score_a, score_b FROM match_history WHERE winner NOT IN ('입력 대기','취소')", conn)
            m2 = pd.read_sql_query("SELECT team_a, team_b, winner, score_a, score_b FROM event_matches WHERE winner NOT IN ('입력 대기','취소')", conn)
            all_m = pd.concat([m1, m2])
            
            wins, losses, draws = 0, 0, 0
            partners = {}
            
            for _, r in all_m.iterrows():
                ta = [x.strip() for x in re.split('[&,]', r['team_a'])]
                tb = [x.strip() for x in re.split('[&,]', r['team_b'])]
                
                if target in ta or target in tb:
                    my_team = ta if target in ta else tb
                    opp_team = tb if target in ta else ta
                    is_a = (target in ta)
                    
                    # 승패 판정
                    if r['winner'] == '무승부': draws += 1
                    elif (is_a and r['winner'] == 'A팀 승리') or (not is_a and r['winner'] == 'B팀 승리'): wins += 1
                    else: losses += 1
                    
                    # 파트너 분석
                    for p in my_team:
                        if p != target:
                            partners[p] = partners.get(p, 0) + (1 if (is_a and r['winner'] == 'A팀 승리') or (not is_a and r['winner'] == 'B팀 승리') else -1)

            st.success(f"**{target}님**의 통산 성적: {wins}승 {draws}무 {losses}패")
            if partners:
                best_p = max(partners, key=partners.get)
                st.write(f"🤝 가장 호흡이 좋은 파트너: **{best_p}**")
            else:
                st.write("분석할 복식 기록이 부족합니다.")

# ----------------------------------------
# 2. 이벤트 메뉴
# ----------------------------------------
elif menu == "이벤트":
    st.subheader("🏆 이벤트 대진표")
    # (기존 이벤트 대진표 로직 동일...)

# ----------------------------------------
# 3. 관리자 메뉴 (회계 기능 포함)
# ----------------------------------------
elif menu == "관리자":
    if not st.session_state['admin_logged_in']:
        conn = get_db_conn()
        pwd = conn.cursor().execute("SELECT value FROM settings WHERE key='admin_password'").fetchone()[0]
        conn.close()
        if st.text_input("관리자 비밀번호", type="password") == pwd:
            st.session_state['admin_logged_in'] = True; st.rerun()
    else:
        st.subheader("⚙️ 시스템 및 회계 관리")
        adm_tab1, adm_tab2, adm_tab3, adm_tab4 = st.tabs(["정규/이벤트", "💰 회계 장부", "👥 회원관리", "🔐 비번변경"])
        
        with adm_tab2:
            st.markdown("### 💰 동호회 통합 장부")
            conn = get_db_conn()
            acc_df = pd.read_sql_query("SELECT * FROM accounts ORDER BY date DESC", conn)
            balance = acc_df['income'].sum() - acc_df['expense'].sum()
            st.markdown(f"<div class='acc-card acc-balance'>🏦 현재 은행 잔고: ₩{balance:,}</div>", unsafe_allow_html=True)
            
            with st.expander("➕ 입출금 내역 직접 입력"):
                c1, c2, c3 = st.columns(3)
                with c1: d_date = st.date_input("날짜", datetime.now())
                with c2: d_cat = st.selectbox("분류", ["기본회비", "월테 대관", "수테 대관", "대회찬조", "기타지출"])
                with c3: d_type = st.radio("구분", ["입금", "출금"])
                d_desc = st.text_input("상세 내용 (예: 4월 회비, 코트비 결제)")
                d_amt = st.number_input("금액", step=1000)
                if st.button("장부 기록 저장"):
                    income = d_amt if d_type == "입금" else 0
                    expense = d_amt if d_type == "출금" else 0
                    conn.cursor().execute("INSERT INTO accounts (date, category, description, income, expense) VALUES (?,?,?,?,?)",
                                          (d_date.strftime("%Y-%m-%d"), d_cat, d_desc, income, expense))
                    conn.commit(); st.success("기록 완료!"); st.rerun()

            st.divider()
            st.markdown("#### 💵 매월 회비 납부자 체크")
            target_m = st.date_input("기준월 선택", datetime.now()).strftime("%Y-%m")
            members_df = get_members(exclude_guest=True)
            paid_list = acc_df[(acc_df['category']=='기본회비') & (acc_df['date'].str.startswith(target_m))]['member_name'].tolist()
            
            cols = st.columns(4)
            for i, row in members_df.iterrows():
                with cols[i % 4]:
                    is_paid = row['name'] in paid_list
                    label = f"✅ {row['name']}" if is_paid else f"❌ {row['name']}"
                    if st.button(label, key=f"pay_{row['name']}"):
                        if not is_paid:
                            conn.cursor().execute("INSERT INTO accounts (date, category, description, income, member_name) VALUES (?,?,?,?,?)",
                                                  (datetime.now().strftime("%Y-%m-%d"), "기본회비", f"{target_m} 정기회비", 30000, row['name']))
                            conn.commit(); st.rerun()
            
            st.divider()
            st.markdown("#### 🏟️ 정기대관(월테/수테) 입금 확인")
            rental_cat = st.selectbox("대관 선택", ["월테 대관", "수테 대관"])
            rental_df = acc_df[acc_df['category'] == rental_cat]
            st.dataframe(rental_df[['date', 'description', 'income', 'expense']], use_container_width=True, hide_index=True)

        with adm_tab4:
            st.markdown("#### 🔐 관리자 비밀번호 변경")
            new_p = st.text_input("새 비밀번호", type="password")
            if st.button("비밀번호 변경 저장"):
                conn = get_db_conn()
                conn.cursor().execute("UPDATE settings SET value=? WHERE key='admin_password'", (new_p,))
                conn.commit(); conn.close()
                st.success("변경되었습니다. 다음 로그인부터 적용됩니다.")
        
        if st.button("로그아웃"):
            st.session_state['admin_logged_in'] = False; st.rerun()
