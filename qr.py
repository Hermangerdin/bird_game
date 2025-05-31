import qrcode
from PIL import Image

def create_qr_code(data, filename='qrcode.png', size=300):
    # Create a basic QR Code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Generate the QR code image
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    # Resize image to specified size using modern resampling
    img = img.resize((size, size), resample=Image.Resampling.LANCZOS)

    # Save image to file
    img.save(filename)
    print(f"QR code saved as '{filename}' with size {size}x{size}.")

# Example usage
if __name__ == '__main__':
    create_qr_code("https://hermangerdin.github.io/bird_game/?token=secretBirdSound123&sound=sound1.mp3", filename="example_qr.png", size=400)