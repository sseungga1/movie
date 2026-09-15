```python
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# ============================================================
# 1. 기본 페이지 설정
# ============================================================

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)


# ============================================================
# 2. 제목과 간단한 설명
# ============================================================

st.title("🎬 어제의 박스오피스")
st.caption("영화관입장권통합전산망(KOBIS) 일일 박스오피스 기준")


# ============================================================
# 3. 한국 시간 기준으로 '어제' 날짜 계산
# ============================================================
# Streamlit Cloud 서버가 한국 시간이 아닐 수 있기 때문에
# 서버의 현재 시간(datetime.now())을 그대로 사용하지 않는다.
#
# ZoneInfo("Asia/Seoul")을 이용해서 현재 시각을 한국 시간으로
# 바꾼 뒤 하루를 빼서 '어제'를 계산한다.

try:
    korea_now = datetime.now(ZoneInfo("Asia/Seoul"))
    target_date = korea_now.date() - timedelta(days=1)

except Exception:
    # 혹시 시간대 정보를 사용할 수 없는 환경이라면
    # 사용자에게 문제를 알려준다.
    st.error(
        "한국 시간대를 계산하지 못했습니다. "
        "배포 환경의 시간대 설정을 확인해 주세요."
    )
    st.stop()


# KOBIS API가 요구하는 날짜 형식: YYYYMMDD
target_dt = target_date.strftime("%Y%m%d")

# 화면에 보여 줄 날짜 형식
display_date = target_date.strftime("%Y년 %m월 %d일")


st.subheader(f"📅 {display_date} 박스오피스")


# ============================================================
# 4. KOBIS 인증키 확인
# ============================================================
# 인증키는 코드에 직접 적지 않고
# Streamlit Cloud의 Secrets에서 KOBIS_KEY라는 이름으로 가져온다.
#
# Streamlit Cloud:
# Settings → Secrets
#
# 예:
# KOBIS_KEY = "발급받은_인증키"
#
# 실제 인증키는 아래 코드에 적으면 안 된다.

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]

except Exception:
    st.error("⚠️ KOBIS 인증키를 찾을 수 없습니다.")

    st.info(
        """
        **확인할 내용**

        1. Streamlit Cloud의 앱 설정에서 **Settings → Secrets**로 들어갑니다.
        2. 다음과 같이 입력되어 있는지 확인합니다.

        `KOBIS_KEY = "발급받은 인증키"`

        3. 인증키 이름이 정확히 `KOBIS_KEY`인지 확인합니다.
        4. 저장한 뒤 앱을 다시 실행해 주세요.
        """
    )

    st.stop()


# ============================================================
# 5. KOBIS API 요청
# ============================================================

API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/boxoffice/"
    "searchDailyBoxOfficeList.json"
)

# API에 보낼 요청 변수
params = {
    "key": KOBIS_KEY,
    "targetDt": target_dt
}


try:
    # KOBIS 서버에 요청을 보낸다.
    response = requests.get(
        API_URL,
        params=params,
        timeout=10
    )

    # HTTP 오류가 있으면 예외를 발생시킨다.
    response.raise_for_status()

    # JSON 데이터를 파이썬 딕셔너리로 변환한다.
    data = response.json()


except requests.exceptions.Timeout:
    st.error("⏱️ KOBIS API 요청 시간이 초과되었습니다.")

    st.info(
        """
        **확인할 내용**

        - 인터넷 연결 상태를 확인해 주세요.
        - KOBIS 서버가 일시적으로 응답하지 않는지 확인해 주세요.
        - 잠시 후 앱을 다시 실행해 주세요.
        """
    )

    st.stop()


except requests.exceptions.RequestException as e:
    st.error("🌐 KOBIS API에 접속하지 못했습니다.")

    st.info(
        f"""
        **확인할 내용**

        - 인터넷 연결 상태를 확인해 주세요.
        - KOBIS API 주소가 정상인지 확인해 주세요.
        - KOBIS 서버의 일시적인 장애 여부를 확인해 주세요.

        오류 내용: `{e}`
        """
    )

    st.stop()


except ValueError:
    st.error("📦 KOBIS에서 올바른 JSON 데이터를 받지 못했습니다.")

    st.info(
        """
        **확인할 내용**

        - KOBIS API 서버의 응답 상태를 확인해 주세요.
        - 잠시 후 다시 실행해 주세요.
        """
    )

    st.stop()


# ============================================================
# 6. 인증키 오류 확인
# ============================================================
# KOBIS API는 인증키가 틀려도 HTTP 상태 코드가 200일 수 있다.
# 따라서 response.raise_for_status()만으로는 인증키 오류를
# 잡을 수 없다.
#
# KOBIS 응답 안에 faultInfo가 있는지 직접 확인한다.

if "faultInfo" in data:
    fault_info = data.get("faultInfo", {})

    error_code = fault_info.get("errorCode", "")
    error_message = fault_info.get("message", "알 수 없는 오류")

    st.error("🔑 KOBIS API 인증 또는 요청에 문제가 있습니다.")

    st.info(
        f"""
        **확인할 내용**

        - Streamlit Secrets에 저장한 `KOBIS_KEY`가 정확한지 확인해 주세요.
        - 인증키 앞뒤에 불필요한 공백이 없는지 확인해 주세요.
        - KOBIS에서 발급받은 API 인증키가 정상적으로 사용 가능한지 확인해 주세요.
        - 요청 날짜가 `YYYYMMDD` 형식으로 전달되었는지도 확인해 주세요.

        **KOBIS 오류 코드:** `{error_code}`

        **KOBIS 오류 메시지:** `{error_message}`
        """
    )

    st.stop()


# ============================================================
# 7. 박스오피스 목록 가져오기
# ============================================================

try:
    boxoffice_result = data["boxOfficeResult"]
    movie_list = boxoffice_result["dailyBoxOfficeList"]

except (KeyError, TypeError):
    st.error("📭 KOBIS 응답에서 영화 목록을 찾지 못했습니다.")

    st.info(
        """
        **확인할 내용**

        - KOBIS API가 정상적으로 응답했는지 확인해 주세요.
        - 인증키가 정상인지 확인해 주세요.
        - 조회 날짜에 대한 일일 박스오피스 데이터가 제공되는지 확인해 주세요.
        """
    )

    st.stop()


# 영화 목록이 비어 있는 경우
if not movie_list:
    st.warning("📭 해당 날짜의 박스오피스 영화 목록이 없습니다.")

    st.info(
        """
        **확인할 내용**

        - 조회 날짜가 올바른지 확인해 주세요.
        - KOBIS에서 해당 날짜의 일일 박스오피스 집계가 완료되었는지 확인해 주세요.
        - 잠시 후 다시 실행해 주세요.
        """
    )

    st.stop()


# ============================================================
# 8. 필요한 데이터만 추출해서 DataFrame 만들기
# ============================================================

rows = []

for movie in movie_list:
    rows.append(
        {
            "순위": movie.get("rank", ""),
            "영화명": movie.get("movieNm", ""),
            "개봉일": movie.get("openDt", ""),
            "관객수": movie.get("audiCnt", "0"),
            "누적관객": movie.get("audiAcc", "0"),
            "스크린수": movie.get("scrnCnt", "0"),
        }
    )


df = pd.DataFrame(rows)


# ============================================================
# 9. 숫자 데이터 변환
# ============================================================
# KOBIS API에서는 숫자도 문자열로 전달될 수 있기 때문에
# 화면에 숫자처럼 표시하고 그래프에서 계산할 수 있도록
# 정수형으로 변환한다.

number_columns = [
    "순위",
    "관객수",
    "누적관객",
    "스크린수"
]

for column in number_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0).astype(int)


# 개봉일은 YYYYMMDD → YYYY.MM.DD 형식으로 보기 좋게 변경
def format_open_date(value):
    value = str(value)

    if len(value) == 8:
        return (
            f"{value[:4]}.{value[4:6]}.{value[6:8]}"
        )

    return value


df["개봉일"] = df["개봉일"].apply(format_open_date)


# ============================================================
# 10. 1위 영화 찾기
# ============================================================

df = df.sort_values("순위").reset_index(drop=True)

first_movie = df.iloc[0]


# ============================================================
# 11. 1위 영화 정보 - 지표 카드 3개
# ============================================================

st.markdown("## 🥇 1위 영화")

st.markdown(
    f"### {first_movie['영화명']}"
)

card1, card2, card3 = st.columns(3)

with card1:
    st.metric(
        label="🎟️ 일일 관객수",
        value=f"{first_movie['관객수']:,}명"
    )

with card2:
    st.metric(
        label="👥 누적 관객수",
        value=f"{first_movie['누적관객']:,}명"
    )

with card3:
    st.metric(
        label="🎞️ 스크린수",
        value=f"{first_movie['스크린수']:,}개"
    )


# ============================================================
# 12. 관객수 상위 5편 막대그래프
# ============================================================

st.markdown("## 📊 관객수 상위 5편")

top5 = (
    df.sort_values("관객수", ascending=False)
    .head(5)
    .copy()
)

# 영화명을 인덱스로 사용하면 Streamlit 기본 막대그래프에서
# 영화별 관객수를 쉽게 비교할 수 있다.
chart_data = top5.set_index("영화명")[["관객수"]]

st.bar_chart(
    chart_data,
    x_label="영화",
    y_label="관객수"
)


# ============================================================
# 13. 전체 박스오피스 표
# ============================================================

st.markdown("## 🎬 전체 박스오피스")

# 숫자에 천 단위 쉼표를 넣어 표에서 읽기 쉽게 만든다.
display_df = df.copy()

display_df["순위"] = display_df["순위"].map(
    lambda x: f"{x:,}"
)

display_df["관객수"] = display_df["관객수"].map(
    lambda x: f"{x:,}명"
)

display_df["누적관객"] = display_df["누적관객"].map(
    lambda x: f"{x:,}명"
)

display_df["스크린수"] = display_df["스크린수"].map(
    lambda x: f"{x:,}개"
)


st.dataframe(
    display_df[
        [
            "순위",
            "영화명",
            "개봉일",
            "관객수",
            "누적관객",
            "스크린수"
        ]
    ],
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 14. 데이터 출처
# ============================================================

st.caption(
    "데이터 출처: 영화관입장권통합전산망(KOBIS) 일일 박스오피스 API"
)
```
