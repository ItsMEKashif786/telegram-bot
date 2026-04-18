import qrcode
import io
from config import UPI_ID

def generate_upi_qr(amount):
    """Generate a UPI QR code for the given amount."""
    upi_url = f"upi://pay?pa={UPI_ID}&pn=Dawateislami%20India&am={amount}&cu=INR&tn=Donation%20to%20Dawateislami%20India%20Bot"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    bio.name = 'upi_qr.png'
    
    return bio
