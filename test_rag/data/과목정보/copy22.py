import requests

r = requests.get("https://app.kangnam.ac.kr/knumis/sbr/sbr1010T.jsp")
print(r.status_code)
print(r.text)
