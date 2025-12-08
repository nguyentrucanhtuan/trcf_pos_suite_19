import qrcode
import base64
from io import BytesIO

# Tạo QR code mẫu cho MOMO
def generate_momo_qr():
    # Data mẫu cho QR code MOMO
    momo_data = "2|99|0123456789|MOMO MERCHANT|merchant@momo.vn|0|0|100000|MOMO Payment Test|transfer|"
    
    # Tạo QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(momo_data)
    qr.make(fit=True)
    
    # Tạo image
    img = qr.make_image(fill_color="#b0006d", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    # Save to file
    with open('static/img/momo_qr_sample.txt', 'w') as f:
        f.write(img_str)
    
    print("QR code generated successfully!")
    print(f"Base64 string saved to static/img/momo_qr_sample.txt")
    print(f"You can use this base64 string in the momo_qr_image field")

if __name__ == "__main__":
    try:
        generate_momo_qr()
    except ImportError:
        print("Please install qrcode library: pip install qrcode[pil]")
        print("For now, you can use any image as QR code placeholder")
