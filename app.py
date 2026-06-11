import streamlit as st
import requests
import re
import json
import pandas as pd
import time
from io import BytesIO

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="유튜브 재생목록 추출기", page_icon="✨", layout="centered")

# --- 2. 디자인 (CSS) 확실하게 고정 ---
st.markdown("""
    <style>
    /* 전체 배경색 */
    .stApp { background-color: #FFFDFD; }
    
    /* 전체 글자색을 짙은 회색으로 고정 (다크모드에서도 잘 보이게) */
    html, body, p, span, label, li, h2, h3, h4 {
        color: #333333 !important;
    }

    /* 제목 색상 */
    h1 { color: #FF6B8B !important; font-weight: 800; }
    
    /* 입력창 디자인 */
    .stTextInput input {
        border-radius: 15px !important;
        border: 2px solid #FFE4E8 !important;
        padding: 10px 15px !important;
        color: #333333 !important;
        background-color: #FFFFFF !important;
    }
    .stTextInput input::placeholder { color: #999999 !important; }
    .stTextInput input:focus {
        border-color: #FFB7C5 !important;
        box-shadow: 0 0 0 0.2rem rgba(255, 183, 197, 0.4) !important;
    }

    /* 💡 핵심: 모든 종류의 버튼(추출, 다운로드, 링크)을 동일하고 뚜렷하게 설정 */
    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button,
    a[data-testid="stLinkButton"] {
        width: 100% !important;
        border-radius: 15px !important;
        height: 3.2em !important;
        background-color: #FFB7C5 !important; /* 파스텔 핑크 배경 */
        color: #5D4037 !important; /* 🌟 진한 초코 브라운 글자 (절대 안 묻힘) */
        font-weight: 900 !important;
        font-size: 16px !important;
        border: none !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 6px rgba(255, 183, 197, 0.3) !important;
        text-decoration: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stDownloadButton"] > button:hover,
    a[data-testid="stLinkButton"]:hover {
        background-color: #FF9EAE !important;
        color: #333333 !important;
        transform: translateY(-2px) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 메인 화면 구성 ---
st.title("✨ 유튜브 재생목록 추출기")
st.write("유튜브 링크를 입력하면 제목, URL, 설명란을 깔끔하게 엑셀로 정리해 드립니다.")
st.write("") # 간격 띄우기

# 입력 섹션 (오류를 일으키던 HTML 빈 박스 제거)
url_input = st.text_input("분석할 유튜브 재생목록 URL을 입력하세요", placeholder="https://www.youtube.com/playlist?list=...")
extract_btn = st.button("데이터 분석 시작")

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
                    
                    # 규칙 적용
                    title = re.split(r'｜|\|', title)[0].strip()
                    desc = re.sub(r'^\*.*$', '', desc, flags=re.MULTILINE)
                    desc = re.sub(r'#\S+', '', desc).strip()
                    if not desc: desc = "(설명 없음)"
                    
                    results.append({"영상 제목": title, "영상 URL": v_url, "영상 설명": desc})
                    time.sleep(0.3)

                status_placeholder.success(f"✅ 총 {len(results)}개의 데이터 추출이 완료되었습니다!")
                df = pd.DataFrame(results)

                # --- 5. 탭 제거 후 한 화면에 모두 표시 ---
                st.divider()
                
                # 결과 미리보기 표
                st.subheader("📊 분석 결과 미리보기")
                st.dataframe(df, use_container_width=True, hide_index=True,
                             column_config={"영상 URL": st.column_config.LinkColumn()})
                
                st.write("") # 간격 띄우기
                
                # 저장 및 내보내기 버튼들
                st.subheader("💾 저장 및 내보내기")
                col_save1, col_save2 = st.columns(2)
                
                with col_save1:
                    excel_df = df.copy()
                    excel_df["영상 URL"] = excel_df["영상 URL"].apply(lambda x: f'=HYPERLINK("{x}", "링크 열기")')
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        excel_df.to_excel(writer, index=False, sheet_name='YouTube_Data')
                    st.download_button("📥 엑셀 파일 다운로드", output.getvalue(), 
                                     file_name="유튜브_추출결과.xlsx", mime="application/vnd.ms-excel")
                
                with col_save2:
                    st.link_button("📝 구글 시트로 열기", "https://sheets.new")
                
                # 하단 팁 안내
                st.caption("💡 **Tip:** [구글 시트로 열기] 버튼을 눌러 새 시트를 띄운 뒤, 다운로드한 엑셀 파일을 마우스로 끌어다 놓으면 즉시 불러와집니다.")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
