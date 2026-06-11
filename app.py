import streamlit as st
import requests
import re
import json
import pandas as pd
import time
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 CSS ---
st.set_page_config(page_title="YouTube Data Intelligence", page_icon="📈", layout="wide")

# 커스텀 CSS 주입 (디자인 개선)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #004085;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover { background-color: #0056b3; color: white; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    h1 { color: #1a1a1a; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .status-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 사이드바 (도움말 및 설정) ---
with st.sidebar:
    st.title("⚙️ 설정 및 도움말")
    st.info("""
    **사용 방법:**
    1. 유튜브 재생목록 URL 입력
    2. 데이터 추출 버튼 클릭
    3. 미리보기 확인 후 엑셀 다운로드
    """)
    st.divider()
    st.caption("v2.0 | Developed for Team Sharing")

# --- 3. 메인 화면 구성 ---
st.title("🎥 YouTube Playlist Intelligence")
st.write("전문적인 업무 효율을 위한 유튜브 재생목록 데이터 분석 도구입니다.")

# 입력 섹션
with st.container():
    st.markdown('<div class="status-box">', unsafe_allow_html=True)
    col1, col2 = st.columns([4, 1])
    with col1:
        url_input = st.text_input("분석할 유튜브 재생목록 URL을 입력하세요", placeholder="https://www.youtube.com/playlist?list=...")
    with col2:
        st.write(" ") # 간격 맞추기
        st.write(" ")
        extract_btn = st.button("데이터 분석 시작")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. 로직 처리 섹션 ---
if extract_btn:
    if not url_input or "list=" not in url_input:
        st.error("올바른 재생목록 URL을 입력해주세요.")
    else:
        # 데이터 추출 시작
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url_input, headers=headers)
            video_ids = list(dict.fromkeys(re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', res.text)))
            
            if not video_ids:
                st.warning("영상을 찾을 수 없습니다.")
            else:
                results = []
                for idx, v_id in enumerate(video_ids):
                    # 진행 상태 업데이트
                    percent = (idx + 1) / len(video_ids)
                    progress_bar.progress(percent)
                    status_placeholder.markdown(f"🔍 **데이터 분석 중:** {idx+1} / {len(video_ids)} 완료")
                    
                    v_url = f"https://www.youtube.com/watch?v={v_id}"
                    v_res = requests.get(v_url, headers=headers)
                    
                    title, desc = f"영상 {idx+1}", ""
                    player_match = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.*?\});", v_res.text)
                    if player_match:
                        pj = json.loads(player_match.group(1))
                        title = pj.get("videoDetails", {}).get("title", title)
                        desc = pj.get("videoDetails", {}).get("shortDescription", "")
                    
                    # 규칙 적용 (차명, 별표 문자, 해시태그 제거)
                    title = re.split(r'｜|\|', title)[0].strip()
                    desc = re.sub(r'^\*.*$', '', desc, flags=re.MULTILINE)
                    desc = re.sub(r'#\S+', '', desc).strip()
                    
                    results.append({"영상 제목": title, "영상 URL": v_url, "영상 설명": desc})
                    time.sleep(0.3)

                status_placeholder.success(f"✅ 총 {len(results)}개의 데이터 분석이 완료되었습니다!")
                df = pd.DataFrame(results)

                # --- 5. 결과 전시 및 다운로드 섹션 ---
                st.divider()
                tab1, tab2 = st.tabs(["📊 분석 결과 미리보기", "💾 데이터 내보내기"])
                
                with tab1:
                    st.dataframe(df, use_container_width=True, hide_index=True,
                                 column_config={"영상 URL": st.column_config.LinkColumn()})
                
                with tab2:
                    c1, c2 = st.columns(2)
                    
                    # 1. 엑셀 다운로드 기능
                    with c1:
                        excel_df = df.copy()
                        excel_df["영상 URL"] = excel_df["영상 URL"].apply(lambda x: f'=HYPERLINK("{x}", "링크 열기")')
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            excel_df.to_excel(writer, index=False, sheet_name='YouTube_Data')
                        st.download_button("📥 엑셀 파일 다운로드", output.getvalue(), 
                                         file_name="youtube_analysis.xlsx", mime="application/vnd.ms-excel")
                    
                    # 2. 구글 시트 바로가기 기능 (마법의 단축 주소 적용)
                    with c2:
                        st.link_button("📝 구글 시트로 열기", "https://sheets.new")
                        st.caption("💡 팁: 위 버튼을 눌러 빈 시트를 연 뒤, 다운로드한 엑셀 파일을 화면에 드래그하면 즉시 불러와집니다!")

        except Exception as e:
            st.error(f"오류 발생: {e}")
