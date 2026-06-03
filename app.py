import streamlit as st
import pandas as pd
import time
import random
import io

# 1. 페이지 기본 설정 (에러 유발 CSS 스타일 제거)
st.set_page_config(page_title="랜선 집들이 이벤트 추첨", page_icon="🎁", layout="centered")

# 스트림릿 순정 기능인 Title과 Subheader로 깔끔하게 화면 구성
st.title("🏢 입주 후기 이벤트 실시간 추첨 시스템")
st.write("참관인 여러분 환영합니다! 공정하고 투명한 무작위 추첨을 진행합니다.")

# 경품 정보 안내판 (스트림릿 내장 경고/정보 박스를 활용해 가독성 업)
st.markdown("---")
st.subheader("🎁 이번 이벤트 시상 내역")
st.error("🥇 **1등** : LG전자 오브제컬렉션 워시콤보 (1명)")
st.warning("🥈 **2등** : LG전자 오브제컬렉션 스타일러 (2명)")
st.success("🥉 **3등** : 로보락 로봇청소기 (3명)")
st.info("🏅 **4등** : LG전자 퓨리케어 360도 공기청정기 (5명)")
st.markdown("---")

# 2. 관리자 사이드바 설정
st.sidebar.header("⚙️ 추첨 시스템 관리")
uploaded_file = st.sidebar.file_uploader("입주자 신청 리스트(.xlsx) 업로드", type=["xlsx"])

# 등수별 상품 정보 및 인원 세팅
prize_settings = {
    "4등": {"name": "LG전자 퓨리케어 360도 공기청정기", "count": 5},
    "3등": {"name": "로보락 로봇청소기", "count": 3},
    "2등": {"name": "LG전자 오브제컬렉션 스타일러", "count": 2},
    "1등": {"name": "LG전자 오브제컬렉션 워시콤보", "count": 1}
}

# 세션 상태 초기화 (중복 당첨 방지 및 당첨자 누적 보관)
if "all_winners" not in st.session_state:
    st.session_state.all_winners = pd.DataFrame(columns=['등수', '상품명', '신청자명', '연락처', '게시글 URL', '연락처_뒷자리'])
if "current_round_winners" not in st.session_state:
    st.session_state.current_round_winners = []

if uploaded_file is not None:
    # 엑셀 데이터 로드 및 중복 연락처 필터링
    df_raw = pd.read_excel(uploaded_file)
    df_raw = df_raw.dropna(subset=['신청자명', '연락처'])
    df_raw = df_raw.drop_duplicates(subset=['연락처']) 
    
    # 성명 가림 해제, 연락처 뒷 4자리 추출
    df_raw['연락처_뒷자리'] = df_raw['연락처'].apply(lambda x: str(x).replace('-', '').strip()[-4:] if len(str(x)) >= 4 else "0000")
    
    # 이전 등수 당첨자 제외 처리 (중복 당첨 방지)
    drawn_phones = st.session_state.all_winners['연락처'].tolist()
    df_pool = df_raw[~df_raw['연락처'].isin(drawn_phones)].reset_index(drop=True)
    
    st.sidebar.success(f"✅ 데이터 동기화 완료! (총 참여자: {len(df_raw)}명 / 추첨 가능: {len(df_pool)}명)")
    
    # 등수 선택 컨트롤러
    st.subheader("🎬 등수별 실시간 추첨 진행")
    selected_rank = st.selectbox("추첨할 등수를 선택하세요", list(prize_settings.keys()))
    
    target_prize = prize_settings[selected_rank]["name"]
    target_count = prize_settings[selected_rank]["count"]
    
    st.info(f"📢 현재 추첨 경품: **[{selected_rank}] {target_prize} (총 {target_count}명)**")
    
    already_drawn = st.session_state.all_winners[st.session_state.all_winners['등수'] == selected_rank]
    
    if len(already_drawn) > 0:
        st.warning(f"⚠️ {selected_rank} 추첨은 이미 완료되었습니다!")
    
    # 실시간 추첨 실행 버튼
    if st.button(f"🔥 {selected_rank} 실시간 추첨 시작! 🔥", use_container_width=True, type="primary", disabled=len(already_drawn) > 0):
        if len(df_pool) < target_count:
            st.error("잔여 추첨 대기 인원이 뽑으려는 당첨자 수보다 부족합니다!")
        else:
            # 1. 셔플 애니메이션 연출 (오류 발생 가능성 없는 순정 텍스트 연출로 수정)
            status_text = st.empty()
            for i in range(15):
                random_pick = df_pool.sample(n=1).iloc[0]
                status_text.warning(f"🎲 시스템 무작위 추첨 매칭 중... ➡️ 당첨자 : {random_pick['신청자명']}님({random_pick['연락처_뒷자리']})")
                time.sleep(0.08)
            status_text.empty()
            
            # 2. 무작위 추첨 진행
