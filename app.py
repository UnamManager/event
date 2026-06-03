import streamlit as st
import pandas as pd
import time
import random
import io

# 1. 페이지 기본 설정 및 디자인 스타일링
st.set_page_config(page_title="입주 후기 이벤트 실시간 추첨", page_icon="🎁", layout="centered")

st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #cf142b;
        font-size: 34px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .sub-title {
        text-align: center;
        font-size: 16px;
        color: #666;
        margin-bottom: 25px;
    }
    .prize-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        margin-bottom: 30px;
    }
    .prize-item {
        font-size: 16px;
        margin: 5px 0;
        color: #333;
    }
    .prize-highlight {
        font-weight: bold;
        color: #cf142b;
    }
    .winner-card {
        background: linear-gradient(135deg, #ffffff 0%, #fdf2f4 100%);
        padding: 25px;
        border-radius: 15px;
        border: 2px solid #cf142b;
        text-align: center;
        box-shadow: 0px 6px 15px rgba(0,0,0,0.05);
        margin: 15px 0;
    }
    .winner-text {
        font-size: 24px;
        font-weight: 900;
        color: #111;
        margin: 10px 0 0 0;
    }
    </style>
""", unsafe_allow_url=True)

st.markdown('<div class="main-title">🏢 입주 후기 이벤트 실시간 추첨 시스템</div>', unsafe_allow_url=True)
st.markdown('<div class="sub-title">참관인 여러분 환영합니다! 공정하고 투명한 무작위 추첨을 진행합니다.</div>', unsafe_allow_url=True)

# 경품 정보 안내판
st.markdown("""
<div class="prize-container">
    <h4 style="margin-top:0; color:#333;">🎁 이번 이벤트 시상 내역</h4>
    <div class="prize-item"><span class="prize-highlight">🥇 1등 :</span> LG전자 오브제컬렉션 워시콤보 (1명)</div>
    <div class="prize-item"><span class="prize-highlight">🥈 2등 :</span> LG전자 오브제컬렉션 스타일러 (2명)</div>
    <div class="prize-item"><span class="prize-highlight">🥉 3등 :</span> 로보락 로봇청소기 (3명)</div>
    <div class="prize-item"><span class="prize-highlight">🏅 4등 :</span> LG전자 퓨리케어 360도 공기청정기 (5명)</div>
</div>
""", unsafe_allow_url=True)

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
    
    # 변경사항 1: 이름 가림 해제, 연락처는 뒷 4자리 추출
    df_raw['연락처_뒷자리'] = df_raw['연락처'].apply(lambda x: str(x).replace('-', '').strip()[-4:] if len(str(x)) >= 4 else "0000")
    
    # 이전 등수 당첨자 제외 처리
    drawn_phones = st.session_state.all_winners['연락처'].tolist()
    df_pool = df_raw[~df_raw['연락처'].isin(drawn_phones)].reset_index(drop=True)
    
    st.sidebar.success(f"✅ 데이터 동기화 완료! (총 참여자: {len(df_raw)}명 / 추첨 가능: {len(df_pool)}명)")
    
    # 등수 선택 컨트롤러
    st.subheader("🎬 등수별 실시간 추첨 진행")
    selected_rank = st.selectbox("추첨할 등수를 선택하세요", list(prize_settings.keys()))
    
    target_prize = prize_settings[selected_rank]["name"]
    target_count = prize_settings[selected_rank]["count"]
    
    st.info(f"📢 현재 추첨 항목: **[{selected_rank}] {target_prize} (총 {target_count}명)**")
    
    already_drawn = st.session_state.all_winners[st.session_state.all_winners['등수'] == selected_rank]
    
    if len(already_drawn) > 0:
        st.warning(f"⚠️ {selected_rank} 추첨은 이미 완료되었습니다!")
    
    # 실시간 추첨 실행 버튼
    if st.button(f"🔥 {selected_rank} 실시간 추첨 시작! 🔥", use_container_width=True, type="primary", disabled=len(already_drawn) > 0):
        if len(df_pool) < target_count:
            st.error("잔여 추첨 대기 인원이 뽑으려는 당첨자 수보다 부족합니다!")
        else:
            # 1. 셔플 애니메이션 (이름 전체 오픈 적용)
            status_text = st.empty()
            for i in range(15):
                random_pick = df_pool.sample(n=1).iloc[0]
                status_text.markdown(f"""
                    <div style="text-align:center; padding:15px; background-color:#1e1e24; color:#fff; border-radius:10px;">
                        <p style="margin:0; font-size:14px; color:#aaa;">🎲 시스템 무작위 난수 코드 매칭 중...</p>
                        <p style="margin:5px 0 0 0; font-size:24px; font-weight:bold; color:#00ff66;">
                            당첨자 : {random_pick['신청자명']}님({random_pick['연락처_뒷자리']})
                        </p>
                    </div>
                """, unsafe_allow_url=True)
                time.sleep(0.08)
            status_text.empty()
            
            # 2. 무작위 추첨 진행
            winners_pick = df_pool.sample(n=target_count).copy()
            winners_pick['등수'] = selected_rank
            winners_pick['상품명'] = target_prize
            
            # 현재 라운드 실시간 애니메이션 연출을 위해 임시 저장 및 최종 세션 등록
            st.session_state.current_round_winners = winners_pick.to_dict('records')
            st.session_state.all_winners = pd.concat([st.session_state.all_winners, winners_pick], ignore_index=True)
            st.rerun() # 화면 리프레시 후 순차 출력 단계로 진입

    # 변경사항 2: 당첨자가 한 명씩 차례차례 쌓이면서 나타나는 실시간 연출 영역
    if st.session_state.current_round_winners:
        st.success(f"🎊 🎉 {selected_rank} 당첨자가 선발되었습니다! 순차적으로 공개합니다! 🎉 🎊")
        
        # 바둑판 배열 슬롯 준비
        cols = st.columns(min(target_count, 3))
        
        # 루프를 돌며 타임 딜레이를 주어 한 명씩 카드가 나타나게 만듦
        for idx, row in enumerate(st.session_state.current_round_winners):
            # 라이브 방송 맛을 내기 위한 1.2~1.5초 딜레이와 폭죽 연출
            time.sleep(1.3)
            st.balloons() 
            
            with cols[idx % 3]:
                st.markdown(f"""
                    <div class="winner-card">
                        <span style="background-color:#cf142b; color:white; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:bold;">{row['등수']}</span>
                        <div class="winner-text">당첨자 : {row['신청자명']}님({row['연락처_뒷자리']})</div>
                    </div>
                """, unsafe_allow_url=True)
        
        # 출고가 끝났으므로 임시 라운드 버퍼 비우기 (다음 등수 추첨을 위해)
        st.session_state.current_round_winners = []

    # 3. 실시간 통합 공식 전광판 (현재까지 누적된 모든 당첨자 명단)
    if len(st.session_state.all_winners) > 0:
        st.markdown("---")
        st.subheader("📊 실시간 당첨 현황 공식 전광판 (누적)")
        
        rank_order = ["4등", "3등", "2등", "1등"]
        display_df = st.session_state.all_winners.copy()
        display_df['sort_idx'] = display_df['등수'].apply(lambda x: rank_order.index(x))
        display_df = display_df.sort_values(by='sort_idx').drop(columns=['sort_idx'])
        
        display_table = display_df[['등수', '상품명', '신청자명', '연락처_뒷자리']].copy()
        display_table.columns = ['등수', '당첨 경품', '성명', '휴대폰 뒷번호']
        st.dataframe(display_table, use_container_width=True, hide_index=True)
        
        # 4. [관리자용 엔딩 비밀 무기] 원본 데이터 복원 백업본 다운로드
        st.markdown("###")
        st.subheader("💾 [관리자용] 최종 당첨자 원본 명단 다운로드")
        st.caption("참관인 방송 종료 후, 아래 버튼을 눌러 실제 성명, 연락처, 후기 URL 원본 리스트를 다운로드하세요.")
        
        raw_output = display_df[['등수', '상품명', '신청자명', '연락처', '게시글 URL']].copy()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            raw_output.to_excel(writer, index=False)
            
        st.download_button(
            label="📥 전체 당첨자 원본 리스트 다운로드 (보고 및 경품 발송용)",
            data=buffer.getvalue(),
            file_name="final_event_winners.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        if st.sidebar.button("🔄 추첨 결과 초기화"):
            st.session_state.all_winners = pd.DataFrame(columns=['등수', '상품명', '신청자명', '연락처', '게시글 URL', '연락처_뒷자리'])
            st.session_state.current_round_winners = []
            st.rerun()

else:
    st.info("👈 실시간 참관인 방송 송출 전, 왼쪽 사이드바 메뉴에서 [입주자 신청 리스트 엑셀(.xlsx)]을 업로드해 주세요.")