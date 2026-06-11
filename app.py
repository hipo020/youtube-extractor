import streamlit as st
import requests
import re
import json
import pandas as pd
import time
from io import BytesIO

# --- 1. 페이지 설정 (중앙 정렬) ---
st.set_page_config(page_title="유튜브 재생목록 추출기", page_icon="✨", layout="centered")

# --- 2. 귀여운 UI 디자인 (가독성 개선 CSS) ---
st.markdown("""
    <style>
    /* 부드러운 배경색 */
    .stApp { background-color: #FFFDFD; }
    
    /* 💡 전체 기본 글자색을 진한 짙은 회색으로 고정 (가독성 향상) */
    html, body, p, div, span, label, li {
        color: #333333 !important;
    }

    /* 💡 제목 색상을 좀 더 진하고 선명한 핑크로 변경 */
    h1 { color: #FF6B8B !important; font-weight: 800; }
    
    /* 동글동글한 입력창 */
    .stTextInput input {
        border-radius: 15px !important;
        border: 2px solid #FFE4E8 !important;
        padding: 10px 15px !important;
        color: #333333 !important; /* 입력하는 글자도 진하게 */
        background-color: #FFFFFF !important;
    }
    .stTextInput input::placeholder {
        color: #999999 !important; /* 안내 문구는 적당한 회색으로 */
    }
    .stTextInput input:focus {
        border-color: #FFB7C5 !important;
        box-shadow: 0 0 0 0.2rem rgba(255, 183, 197, 0.4) !important;
    }

    /* 파스텔톤 둥근 버튼 (가독성을 위해 글자를 초코 브라운으로 변경) */
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        background-color: #FFB7C5;
        color: #5D4037 !important; /* 💡 하얀색 대신 진한 초코색으로 눈에 띄게! */
        font-weight: 900 !important;
        font-size: 16px;
        border: none;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px rgba(255, 183, 197, 0.3);
    }
    .stButton>button:hover {
        background-color: #FFA5B5;
        color: #5D4037 !important;
        transform: translateY(-2px);
    }

    /* 입력창을 감싸는 하얀색 예쁜 박스 */
    .cute-box {
        background-color: white;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 8px 20px rgba(255, 183, 197, 0.2);
        border: 1px solid #FFF0F2;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 메인 화면 구성 ---
st.title("✨ 유튜브 재생목록 추출기")
st.write("유튜브 링크를 입력하면 제목, URL, 설명란을 깔끔하게 엑셀로 정리해 드립니다.")

# 입력 섹션 (중앙 집중형 둥근 박스)
st.markdown('<div class="cute-box">', unsafe_allow_html=True)
url_input = st.text_input("분석할 유튜브 재생목록 URL을 입력하세요", placeholder="https://www.youtube.com/playlist?list=...")
extract_btn = st.button("데이터 분석 시작")
st.markdown('</div>', unsafe_allow_html=True)

# --- 4. 로직 처리 섹션 ---
if extract_btn:
    if not url_input or "list=" not in url_input:
        st.error("올바른 재생목록 URL을 입력해주세요.")
    else:
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url_input, headers=headers)
            video_ids = list(dict.fromkeys(re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', res.text)))
            
            if not video_ids:
                st.warning("영상을 찾을 수 없습니다. 재생목록 상태를 확인해주세요.")
            else:
                results = []
                for idx, v_id in enumerate(video_ids):
                    percent = (idx + 1) / len(video_ids)
                    progress_bar.progress(percent)
                    status_placeholder.markdown(f"🔍 **데이터 추출 중:** {idx+1} / {len(video_ids)} 완료")
                    
                    v_url = f"https://www.youtube.com/watch?v={v_id}"
                    v_res = requests.get(v_url, headers=headers)
                    
                    title, desc = f"영상 {idx+1}", ""
                    player_match = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.*?\});", v_res.text)
                    if player_match:
                        pj = json.loads(player_match.group(1))
                        title = pj.get("videoDetails", {}).get("title", title)
                        desc = pj.get("videoDetails", {}).get("shortDescription", "")
                    
                    # 규칙 적용 (차명 제거, 별표 문장 제거, 해시태그 제거)
                    title = re.split(r'｜|\|', title)[0].strip()
                    desc = re.sub(r'^\*.*$', '', desc, flags=re.MULTILINE)
                    desc = re.sub(r'#\S+', '', desc).strip()
                    
                    if not desc: desc = "(설명 없음)"
                    
                    results.append({"영상 제목": title, "영상 URL": v_url, "영상 설명": desc})
                    time.sleep(0.3)

                status_placeholder.success(f"✅ 총 {len(results)}개의 데이터 추출이 완료되었습니다!")
                df = pd.DataFrame(results)

                # --- 5. 결과 전시 및 다운로드 섹션 ---
                st.divider()
                tab1, tab2 = st.tabs(["📊 분석 결과 미리보기", "💾 저장 및 내보내기"])
                
                with tab1:
                    st.dataframe(df, use_container_width=True, hide_index=True,
                                 column_config={"영상 URL": st.column_config.LinkColumn()})
                
                with tab2:
                    st.write("원하시는 방식을 선택하여 데이터를 저장하세요.")
                    col_save1, col_save2 = st.columns(2)
                    
                    # 1. 엑셀 다운로드
                    with col_save1:
                        excel_df = df.copy()
                        excel_df["영상 URL"] = excel_df["영상 URL"].apply(lambda x: f'=HYPERLINK("{x}", "링크 열기")')
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            excel_df.to_excel(writer, index=False, sheet_name='YouTube_Data')
                        st.download_button("📥 엑셀 파일 다운로드", output.getvalue(), 
                                         file_name="유튜브_추출결과.xlsx", mime="application/vnd.ms-excel")
                    
                    # 2. 구글 시트로 열기
                    with col_save2:
                        st.link_button("📝 구글 시트로 열기", "https://sheets.new")
                        st.caption("💡 새 시트를 연 뒤, 다운로드한 엑셀 파일을 드래그해서 놓으면 즉시 불러와집니다.")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
