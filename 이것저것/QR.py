import qrcode
from PIL import Image

# URL
url = "https://y3vwfexxbf6gnvkekczahc.streamlit.app/"

# QR 생성기 설정
qr = qrcode.QRCode(
    version=4,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
qr.add_data(url)
qr.make(fit=True)

# QR 코드 이미지 생성
qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

# 로고 불러오기
logo = Image.open("Gangnaengbot.png")

# 로고 크기 조절
qr_width, qr_height = qr_img.size
logo_size = qr_width // 4
logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

# QR 코드 중앙에 로고 삽입
pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
qr_img.paste(logo, pos, mask=logo if logo.mode == 'RGBA' else None)

# 저장
qr_img.save("qr_with_logo.png")

print("QR 코드가 'qr_with_logo.png'로 저장되었습니다.")