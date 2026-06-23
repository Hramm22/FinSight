import requests


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


if __name__ == "__main__":
    url = "https://finance.naver.com/sise/sise_amount.naver?sosok=0&page=1"

    response = requests.get(url, headers=HEADERS, timeout=10)
    response.encoding = "euc-kr"

    print("상태코드:", response.status_code)
    print("최종 URL:", response.url)
    print("응답 길이:", len(response.text))
    print(response.text[:1000])