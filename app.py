import streamlit as st
import requests
import re
import json
import pandas as pd
import time
from io import BytesIO

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="유튜브 재생목록 추출기",
    page_icon="✨",
    layout="centered"
)

# --- 2. 디자인 CSS ---
st.markdown("""
    <style>
    /* 전체 배경을 밝은 톤으로 고정 */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"] {
        background-color: #FFFDFD !important;
    }

    /* 상단 헤더 배경 고정 */
    [data-testid="stHeader"] {
        background-color: #FFFDFD !important;
    }

    /* ✅ 다크모드에서도 오른쪽 상단 Streamlit 아이콘 보이게 고정 */
    [data-testid="stToolbar"],
    [data-testid="stToolbar"] *,
    [data-testid="stHeader"] button,
    [data-testid="stHeader"] button *,
    [data-testid="stHeader"] a,
    [data-testid="stHeader"] a *,
    [data-testid="stHeader"] span,
    [data-testid="stHeader"] svg,
    [data-testid="stHeader"] svg *,
    [data-testid="stHeader"] path,
    [data-testid="stHeader"] rect,
    [data-testid="stHeader"] circle,
    [data-testid="stHeader"] line,
    [data-testid="stHeader"] polyline,
    [data-testid="stHeader"] polygon {
        color: #333333 !important;
        fill: #333333 !important;
        stroke: #333333 !important;
        opacity: 1 !important;
    }

    /* Deploy / GitHub / 메뉴 버튼 보정 */
    .stAppDeployButton,
    .stAppDeployButton *,
    .stAppViewerButton,
    .stAppViewerButton *,
    [data-testid="stBaseButton-header"],
    [data-testid="stBaseButton-header"] *,
    [data-testid="stMainMenu"],
    [data-testid="stMainMenu"] *,
    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] * {
        color: #333333 !important;
        fill: #333333 !important;
        stroke: #333333 !important;
        opacity: 1 !important;
    }

    /* 상단 아이콘 hover 시에도 보이게 */
    [data-testid="stHeader"] button:hover,
    [data-testid="stHeader"] button:hover *,
    [data-testid="stToolbar"] button:hover,
    [data-testid="stToolbar"] button:hover * {
        color: #111111 !important;
        fill: #111111 !important;
        stroke: #111111 !important;
        opacity: 1 !important;
    }

    /* 우측 상단 점 세 개 메뉴 내부 스타일은 기본값 유지 */
    div[data-baseweb="popover"] *,
    div[data-testid="main-menu-popover"] *,
    .stPopover * {
        color: inherit !important;
        fill: currentColor !important;
        stroke: currentColor !important;
    }

    /* 메인 뷰포트 내부 텍스트 컬러 지정 */
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] li,
    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3,
    [data-testid="stAppViewContainer"] h4 {
        color: #333333 !important;
    }

    /* 제목 색상 */
    h1 {
        color: #FF6B8B !important;
        font-weight: 800 !important;
    }

    /* 다크모드 검정 모서리 튀어나옴 제거 */
    .stTextInput [data-baseweb="input"],
    .stTextInput [data-baseweb="base-input"] {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 실제 입력창 디자인 */
    .stTextInput input {
        border-radius: 15px !important;
        border: 2px solid #FFE4E8 !important;
        padding: 10px 15px !important;
        color: #333333 !important;
        background-color: #FFFFFF !important;
        box-shadow: none !important;
    }

    /* 입력창 안의 예시 텍스트 */
    .stTextInput input::placeholder {
        color: #888888 !important;
        -webkit-text-fill-color: #888888 !important;
        opacity: 1 !important;
    }

    .stTextInput input:focus {
        border-color: #FFB7C5 !important;
        outline: none !important;
        box-shadow: 0 0 0 0.2rem rgba(255, 183, 197, 0.4) !important;
    }

    /* 버튼 스타일 */
    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        width: 100% !important;
        border-radius: 15px !important;
        height: 3.2em !important;
        background-color: #FFB7C5 !important;
        color: #5D4037 !important;
        font-weight: 900 !important;
        font-size: 16px !important;
        border: none !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 6px rgba(255, 183, 197, 0.3) !important;
    }

    div[data-testid="stButton"] > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #FF9EAE !important;
        color: #333333 !important;
        transform: translateY(-2px) !important;
    }

    div[data-testid="stButton"] > button:active,
    div[data-testid="stDownloadButton"] > button:active {
        transform: translateY(0px) !important;
    }

    /* 데이터프레임 주변 여백 */
    [data-testid="stDataFrame"] {
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 메인 화면 구성 ---
st.title("✨ 유튜브 재생목록 추출기")
st.write("유튜브 링크를 입력하면 제목, URL, 설명란을 깔끔하게 엑셀로 정리해 드립니다.")
st.write("")

# 입력 섹션
url_input = st.text_input(
    "분석할 유튜브 재생목록 URL을 입력하세요",
    placeholder="https://www.youtube.com/playlist?list=..."
)

extract_btn = st.button("데이터 분석 시작")

# --- 4. 로직 처리 섹션 ---
if extract_btn:
    if not url_input or "list=" not in url_input:
        st.error("올바른 재생목록 URL을 입력해주세요.")
    else:
        status_placeholder = st.empty()
        progress_bar = st.progress(0)

        try:
            headers = {
                "User-Agent": "Mozilla/5.0"
            }

            res = requests.get(url_input, headers=headers)
            res.raise_for_status()

            video_ids = list(
                dict.fromkeys(
                    re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', res.text)
                )
            )

            if not video_ids:
                st.warning("영상을 찾을 수 없습니다. 재생목록 상태를 확인해주세요.")
            else:
                results = []

                for idx, v_id in enumerate(video_ids):
                    percent = (idx + 1) / len(video_ids)
                    progress_bar.progress(percent)
                    status_placeholder.markdown(
                        f"🔍 **데이터 추출 중:** {idx + 1} / {len(video_ids)} 완료"
                    )

                    v_url = f"https://www.youtube.com/watch?v={v_id}"
                    v_res = requests.get(v_url, headers=headers)
                    v_res.raise_for_status()

                    title = f"영상 {idx + 1}"
                    desc = ""

                    player_match = re.search(
                        r"ytInitialPlayerResponse\\s*=\\s*(\\{.*?\\});",
                        v_res.text
                    )

                    if player_match:
                        try:
                            player_json = json.loads(player_match.group(1))
                            title = player_json.get("videoDetails", {}).get("title", title)
                            desc = player_json.get("videoDetails", {}).get("shortDescription", "")
                        except json.JSONDecodeError:
                            pass

                    # 제목 정리
                    title = re.split(r'｜|\\|', title)[0].strip()

                    # 설명 정리
                    desc = re.sub(r'^\\*.*$', '', desc, flags=re.MULTILINE)
                    desc = re.sub(r'#\\S+', '', desc)
                    desc = desc.strip()

                    if not desc:
                        desc = "(설명 없음)"

                    results.append({
                        "영상 제목": title,
                        "영상 URL": v_url,
                        "영상 설명": desc
                    })

                    time.sleep(0.3)

                status_placeholder.success(
                    f"✅ 총 {len(results)}개의 데이터 추출이 완료되었습니다!"
                )

                df = pd.DataFrame(results)

                # --- 5. 결과 전시 및 다운로드 섹션 ---
                st.divider()

                header_col1, header_col2 = st.columns([2.5, 1.5])

                with header_col1:
                    st.subheader("📊 분석 결과 미리보기")

                with header_col2:
                    excel_df = df.copy()

                    excel_df["영상 URL"] = excel_df["영상 URL"].apply(
                        lambda x: f'=HYPERLINK("{x}", "링크 열기")'
                    )

                    output = BytesIO()

                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        excel_df.to_excel(
                            writer,
                            index=False,
                            sheet_name="YouTube_Data"
                        )

                    st.download_button(
                        label="📥 엑셀 파일 다운로드",
                        data=output.getvalue(),
                        file_name="유튜브_추출결과.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "영상 URL": st.column_config.LinkColumn("영상 URL")
                    }
                )

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
