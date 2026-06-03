import streamlit as st
import pandas as pd
import time
import random
import io

# 1. 페이지 기본 설정
st.set_page_config(page_title="랜선 집들이 이벤트 추첨", page_icon="🎁", layout="centered")

# [수정] 에러를 유발하는 <style> 태그를 완전히 제거!
# 대신 스트림릿 순정 '빈 줄 바꿈' 기능을 사용하여 상단 제목이 잘리지 않도록 공간을 넉넉히 확보합니다.
st.markdown("#") 
st.markdown("#") 

st.title("🏢 입주 후기 이벤트 실시간 추첨 시스템")
st.write("참관인 여러분 환영합니다! 공정하고 투명한 무작위 추첨을 진행합니다.")

# 경품 정보 안내판
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

# 세션 상태 초기화 (누적 당첨자 보관용)
if "all_winners" not in st.session_state:
    st.session_state.all_winners = pd.DataFrame(columns=['등수', '상품명', '신청자명', '연락처', '게시글 URL', '연락처_뒷자리'])

if uploaded_file is not None:
    # 엑셀 데이터 로드 및 중복 연락처 필터링
    df_raw = pd.read_excel(uploaded_file)
    df_raw = df_raw.dropna(subset=['신청자명', '연락처'])
    df_raw = df_raw.drop_duplicates(subset=['연락처']) 
    
    # 이름 전체 공개, 연락처 뒷 4자리 추출
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
            # 1. 셔플 애니메이션 연출
            status_text = st.empty()
            for i in range(12):
                random_pick = df_pool.sample(n=1).iloc[0]
                status_text.warning(f"🎲 시스템 무작위 추첨 매칭 중... ➡️ 당첨자 : {random_pick['신청자명']}님({random_pick['연락처_뒷자리']})")
                time.sleep(0.08)
            status_text.empty() # 연출창 비우기
            
            # 2. 진짜 무작위 추첨 진행
            winners_pick = df_pool.sample(n=target_count).copy()
            winners_pick['등수'] = selected_rank
            winners_pick['상품명'] = target_prize
            
            # 세션에 누적 저장
            st.session_state.all_winners = pd.concat([st.session_state.all_winners, winners_pick], ignore_index=True)
            
            # 3. 당첨자 순차 연출 영역
            st.write("---")
            st.success(f"🎊 🎉 {selected_rank} 당첨자가 선발되었습니다! 순차적으로 공개합니다! 🎉 🎊")
            
            # [수정 사항 반영] 풍선 효과는 리스트 출력 시작 전에 딱 '한 번만' 터집니다.
            st.balloons()
            
            # 스트림릿 내장 바둑판 레이아웃 설정
            cols = st.columns(min(target_count, 3))
            
            # 리스트 변환 후 1.3초 딜레이 연출 적용 (내부 풍선 효과 제거)
            winners_list = winners_pick.to_dict('records')
            for idx, row in enumerate(winners_list):
                time.sleep(1.3) # 1.3초 긴장감 딜레이 유지
                
                # 순정 카드 컨테이너 출력
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.write(f"🏆 **{row['등수']} 당첨**")
                        st.subheader(f"{row['신청자명']}님")
                        st.write(f"({row['연락처_뒷자리']})")

    # 4. 실시간 통합 공식 전광판 (현재까지 누적된 모든 당첨자 명단)
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
        
        # 5. [관리자용 엔딩 비밀 무기] 원본 데이터 복원 백업본 다운로드
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
            st.rerun()

else:
    st.info("👈 실시간 참관인 방송 송출 전, 왼쪽 사이드바 메뉴에서 [입주자 신청 리스트 엑셀(.xlsx)]을 업로드해 주세요.")
