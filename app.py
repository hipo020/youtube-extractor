import streamlit as st
import requests
import re
import json
import pandas as pd
import time
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 CSS (귀여움 한스푼 추가!) ---
st.set_page_config(page_title="유튜브 요정 뚠뚠", page_icon="✨", layout="wide")

# 커스텀 CSS 주입 (아기자기한 디자인)
st.markdown("""
    <style>
    /* 전체 배경색을 부드러운 크림색으로 */
    .main { background-color: #fdfbf6; }
    
    /* 폰트를 둥글둥글한 느낌으로 (브라우저 기본 둥근 폰트 우선) */
    html, body, [class*="css"]  {
        font-family: 'Inter', 'NanumGothic', sans-serif;
    }

    /* 사이드바 스타일 */
    .css-163rgbv { background-color: #fff5f8; }

    /* 모든 버튼을 동글동글하고 파스텔톤으로 */
    .stButton>button {
        width: 100%;
        border-radius: 20px; /* 아주 둥글게 */
        height: 3.5em;
        background-color: #ffb7c5; /* 파스텔 핑크 */
        color: white;
        font-weight: bold;
        border: 2px solid #ffb7c5;
        transition: all 0.3s ease;
        font-size: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); /* 부드러운 그림자 */
    }
    .stButton>button:hover {
        background-color: white;
        color: #ffb7c5;
        border: 2px solid #ffb7c5;
        transform: translateY(-2px); /* 살짝 떠오르는 효과 */
    }

    /* 입력창 스타일 */
    .stTextInput>div>div>input {
        border-radius: 15px;
        border: 2px solid #e0e0e0;
        background-color: white;
        padding: 10px;
    }
    .stTextInput>div>div>input:focus {
        border-color: #ffb7c5;
        box-shadow: 0 0 0 0.2rem rgba(255, 183, 197, 0.25);
    }

    /* 중앙 입력 섹션 박스 */
    .cute-box {
        padding: 30px;
        border-radius: 20px;
        background-color: #ffffff;
        box-shadow: 0 8px 16px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        border: 1px solid #f0f0f0;
    }

    /* 제목 스타일 */
    h1 { color: #ff8b94; font-family: 'Jua', sans-serif; } /* 핑크색 제목 */
    h2, h3 { color: #666666; }

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f0f0;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        color: #666666;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffb7c5;
        color: white;
    }

    /* 성공 메시지 박스 */
    .stAlert {
        border-radius: 15px;
    }
    </style>
    
    <link href="https://fonts.googleapis.com/css2?family=Jua&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

# --- 2. 사이드바 (도움말 및 설정) ---
with st.sidebar:
    st.markdown("## ⚙️ 요정의 안내소")
    st.markdown("""
    **사용 방법:**
    1. 유튜브 재생목록 주소 복사!
    2. 아래 입력창에 **슝~** 붙여넣기
    3. **데이터 분석** 버튼 꾹!
    4. 완료되면 엑셀로 저장하기 💖
    """)
    st.divider()
    st.caption("✨ v2.1 뚠뚠 에디션")

# --- 3. 메인 화면 구성 ---
st.markdown("<h1>✨ 유튜브 데이터 추출 요정 뚠뚠</h1>", unsafe_allow_html=True)
st.markdown("### 팀원들과 함께 쓰는 아기자기한 유튜브 분석 도구에요! 🧸")

# 입력 섹션
with st.container():
    st.markdown('<div class="cute-box">', unsafe_allow_html=True)
    col1, col2 = st.columns([4, 1])
    with col1:
        url_input = st.text_input("분석할 유튜브 재생목록 주소를 알려주세요!", placeholder="https://www.youtube.com/playlist?list=...")
    with col2:
        st.write(" ") # 간격 맞추기
        st.write(" ")
        extract_btn = st.button("🌟 데이터 추출 시작!")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. 로직 처리 섹션 ---
if extract_btn:
    if not url_input or "list=" not in url_input:
        st.error("잉? 올바른 재생목록 주소가 아닌 것 같아요. 다시 확인해볼까요? 🥺")
    else:
        # 데이터 추출 시작
        status_placeholder = st.empty()
        status_placeholder.markdown("### 🧚‍♀️ 요정이 열심히 마법을 부리는 중... (기다려주세요!)")
        progress_bar = st.progress(0)
        
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url_input, headers=headers)
            # 영상 ID 추출 시 중복 제거를 위해 dict.fromkeys 사용
            video_ids = list(dict.fromkeys(re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', res.text)))
            
            if not video_ids:
                st.warning("어라? 영상을 찾을 수 없어요. 공개 상태인지 확인해주세요! 😭")
            else:
                results = []
                for idx, v_id in enumerate(video_ids):
                    # 진행 상태 업데이트
                    percent = (idx + 1) / len(video_ids)
                    progress_bar.progress(percent)
                    status_placeholder.markdown(f"### 🔍 **마법 발동 중:** {idx+1} / {len(video_ids)} 완료 ✨")
                    
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
                    
                    if not desc: desc = "(설명이 없어요!)"
                    
                    results.append({"영상 제목": title, "영상 URL": v_url, "영상 설명": desc})
                    # 차단 방지를 위한 약간의 대기
                    time.sleep(0.3)

                status_placeholder.success(f"🎉 짝짝짝! 총 {len(results)}개의 영상을 성공적으로 분석했어요! 🎉")
                df = pd.DataFrame(results)

                # --- 5. 결과 전시 및 다운로드 섹션 ---
                st.divider()
                tab1, tab2 = st.tabs(["📊 미리보기", "💾 저장하기"])
                
                with tab1:
                    st.dataframe(df, use_container_width=True, hide_index=True,
                                 column_config={"영상 URL": st.column_config.LinkColumn()})
                
                with tab2:
                    st.markdown("### 🎁 분석 결과를 저장할까요?")
                    col_save1, col_save2 = st.columns(2)
                    
                    # 1. 엑셀 다운로드 기능
                    with col_save1:
                        st.markdown("#### 📄 엑셀 파일로 컴퓨터에 저장!")
                        excel_df = df.copy()
                        # 엑셀 하이퍼링크 공식 적용
                        excel_df["영상 URL"] = excel_df["영상 URL"].apply(lambda x: f'=HYPERLINK("{x}", "링크 열기")')
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            excel_df.to_excel(writer, index=False, sheet_name='YouTube_Data')
                        st.download_button("📥 엑셀 파일 다운로드", output.getvalue(), 
                                         file_name="유튜브_분석결과.xlsx", mime="application/vnd.ms-excel")
                    
                    # 2. 구글 시트 바로가기 기능 (마법의 단축 주소 적용)
                    with col_save2:
                        st.markdown("#### 📝 내 구글 시트로 바로 가져가기!")
                        st.link_button("📝 구글 시트로 열기", "https://sheets.new")
                        st.caption("💡 팁: 버튼을 눌러 새 시트를 연 뒤, 다운로드한 엑셀 파일을 드래그해서 놓으면 쏙! 들어가요!")

        except Exception as e:
            st.error(f"으앙, 오류가 발생했어요! 나중에 다시 시도해주세요. 😭 (오류내용: {e})")
