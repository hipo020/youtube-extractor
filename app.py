import streamlit as st
import requests
import re
import json
import pandas as pd
import time
from io import BytesIO

# 웹페이지 기본 설정
st.set_page_config(page_title="유튜브 재생목록 추출기", page_icon="📊", layout="centered")

st.title("📊 유튜브 재생목록 엑셀 추출 도구")
st.write("유튜브 재생목록 링크를 입력하면 제목, URL, 설명란을 깔끔하게 정리하여 엑셀로 뽑아줍니다.")
st.caption("⚠️ 필터링 적용 완료: 제목 뒤 차명 제거, 해시태그 제거, '*'로 시작하는 설명 문장 제거 (클릭 가능한 링크 적용)")

# URL 입력창
url_input = st.text_input("유튜브 재생목록 URL을 입력하세요:", placeholder="https://www.youtube.com/playlist?list=...")

# 추출 버튼 클릭 시 실행
if st.button("🚀 데이터 추출 및 엑셀 만들기", type="primary"):
    if not url_input:
        st.error("URL을 입력해주세요!")
    elif "list=" not in url_input:
        st.error("올바른 유튜브 재생목록 URL이 아닙니다. 주소에 'list='이 포함되어 있는지 확인해주세요.")
    else:
        with st.spinner("재생목록에서 영상 목록을 분석하는 중..."):
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
                }
                
                # 재생목록 페이지 소스 가져오기
                res = requests.get(url_input, headers=headers)
                html = res.text
                
                # 재생목록 내의 고유 영상 ID 추출
                video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
                video_ids = list(dict.fromkeys(video_ids))  # 중복 제거
                
                if not video_ids:
                    st.error("재생목록에서 영상을 찾지 못했습니다. 공개 또는 일부공개 상태인지 확인해주세요.")
                else:
                    st.info(f"총 {len(video_ids)}개의 영상을 찾았습니다. 데이터 수집을 시작합니다.")
                    
                    # 진행 바 설정
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    results = []
                    
                    # 각 영상별로 돌면서 상세 정보 추출
                    for idx, v_id in enumerate(video_ids):
                        status_text.text(f"⏳ 데이터 수집 중... ({idx + 1} / {len(video_ids)})")
                        progress_bar.progress((idx + 1) / len(video_ids))
                        
                        v_url = f"https://www.youtube.com/watch?v={v_id}"
                        
                        try:
                            v_res = requests.get(v_url, headers=headers)
                            v_html = v_res.text
                            
                            title = f"영상 {idx+1}"
                            description = ""
                            
                            # 유튜브 내부 JSON 데이터 파싱
                            player_match = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.*?\});", v_html)
                            if player_match:
                                player_json = json.loads(player_match.group(1))
                                video_details = player_json.get("videoDetails", {})
                                title = video_details.get("title", title)
                                description = video_details.get("shortDescription", "")
                            
                            # 규칙 1: 제목에서 '｜' 또는 '|' 뒤의 내용(차명) 제거
                            title = re.split(r'｜|\|', title)[0].strip()
                            
                            # 규칙 2: 설명란 필터링
                            if description:
                                # '*' 기호로 시작하는 줄 통째로 삭제
                                description = re.sub(r'^\*.*$', '', description, flags=re.MULTILINE)
                                # 해시태그(#태그) 제거
                                description = re.sub(r'#\S+', '', description)
                                # 불필요한 빈 줄 제거 및 양끝 공백 정리
                                description = re.sub(r'\n\s*\n', '\n', description).strip()
                            else:
                                description = "(설명 없음)"
                                
                            results.append({
                                "영상 제목": title,
                                "영상 URL": v_url,
                                "영상 설명": description
                            })
                            
                        except Exception as e:
                            results.append({
                                "영상 제목": "오류 발생",
                                "영상 URL": v_url,
                                "영상 설명": f"추출 실패: {str(e)}"
                            })
                        
                        # 차단 방지를 위한 짧은 휴식 (0.4초)
                        time.sleep(0.4)
                    
                    status_text.text("✨ 모든 데이터 추출 완료!")
                    
                    # 데이터프레임 생성
                    df = pd.DataFrame(results)
                    st.subheader("📊 추출 결과 미리보기")
                    
                    # 💡 변경 포인트 1: 웹 화면 표에서도 URL을 클릭하면 바로 이동하도록 설정 (LinkColumn)
                    st.dataframe(
                        df, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "영상 URL": st.column_config.LinkColumn("영상 URL")
                        }
                    )
                    
                    # 💡 변경 포인트 2: 엑셀 전용 데이터프레임을 복사해 URL 컬럼에 엑셀 하이퍼링크 공식 적용
                    excel_df = df.copy()
                    excel_df["영상 URL"] = excel_df["영상 URL"].apply(lambda url: f'=HYPERLINK("{url}", "{url}")')
                    
                    # 메모리상에 엑셀 파일 생성
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        excel_df.to_excel(writer, index=False, sheet_name='유튜브 추출 데이터')
                    excel_data = output.getvalue()
                    
                    # 📥 엑셀 다운로드 버튼 등장
                    st.download_button(
                        label="📥 엑셀 파일(.xlsx) 다운로드",
                        data=excel_data,
                        file_name="유튜브_재생목록_추출결과.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
            except Exception as e:
                st.error(f"프로그램 실행 중 오류가 발생했습니다: {str(e)}")
