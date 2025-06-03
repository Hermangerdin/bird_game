from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import qr

class CardGenerator:
    def __init__(self, save_path):
        # === Configuration ===
        self.CARD_WIDTH_PX, self.CARD_HEIGHT_PX = 223, 312  # ~2.5x3.5 inches at 90 DPI
        self.SCALE = 0.75  # px to PDF points
        self.CARD_WIDTH_PT = self.CARD_WIDTH_PX * self.SCALE
        self.CARD_HEIGHT_PT = self.CARD_HEIGHT_PX * self.SCALE
        self.CARDS_PER_ROW = 3
        self.CARDS_PER_COL = 3
        self.SPACING = 10
        self.X_OFFSET = 20
        self.Y_OFFSET = 20
        self.OUTPUT_DIR = "output_cards"
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        self._canvas = canvas.Canvas(save_path, pagesize=A4)
        # === Font Setup ===
        try:
            self.font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            self.font = ImageFont.load_default()
        
        try:
            self.font_latin = ImageFont.truetype("arial.ttf", 15)
        except IOError:
            self.font_latin = ImageFont.load_default()

        try:
            self.font_wingspan = ImageFont.truetype("arial.ttf", 30)
        except IOError:
            self.font_wingspan = ImageFont.load_default()    



    # === Card Creation ===
    def create_card_front(self,_card):
        card = Image.new("RGB", (self.CARD_WIDTH_PX, self.CARD_HEIGHT_PX), "lightgray")
        draw = ImageDraw.Draw(card)

        # Placeholder for image
        #draw.rectangle([0, 0, CARD_WIDTH_PX, int(CARD_HEIGHT_PX * 0.6)], fill="lightgray")
        # Text
        w = draw.textlength(_card._bird_name, self.font)
        draw.text(((self.CARD_WIDTH_PX // 2)-w//2,  20), _card._bird_name, fill="black", font=self.font)

        w = draw.textlength(_card._bird_name_latin, self.font_latin)
        draw.text(((self.CARD_WIDTH_PX // 2)-w//2,  40), _card._bird_name_latin, fill="black", font=self.font_latin)

        wingspan_text = 'Wingspan'
        w = draw.textlength(wingspan_text, self.font_latin)
        draw.text(((self.CARD_WIDTH_PX // 2)-w//2,  self.CARD_HEIGHT_PX-60), wingspan_text , fill="black", font=self.font_latin)
        
        w = draw.textlength(_card._wingspan, self.font_wingspan)
        draw.text(((self.CARD_WIDTH_PX // 2)-w//2,  self.CARD_HEIGHT_PX-40), _card._wingspan, fill="black", font=self.font_wingspan)

        return card

    def create_card_back(self,_card):
        qr_size = 120
        text = 'Birdster'
        card = Image.new("RGB", (self.CARD_WIDTH_PX, self.CARD_HEIGHT_PX), "lightgray")
        draw = ImageDraw.Draw(card)

        w = draw.textlength(text)
        draw.text(((self.CARD_WIDTH_PX // 2)-w, 20), text, fill="black", font=self.font)
        img = qr.create_qr_code(_card._default_URL + _card._mapping, qr_size)

        img_x = ((self.CARD_WIDTH_PX) // 2) - (qr_size//2)
        img_y = ((self.CARD_HEIGHT_PX ) // 2) - (qr_size//2)

        card.paste(img, (img_x,img_y))
        return card

    # === PDF Layout ===
    def draw_cards_on_pdf(self,front_images, back_images):
        #c = canvas.Canvas(pdf_path, pagesize=A4)
        _fronts = [self.create_card_front(front_images[i]) for i in range(len(front_images))]
        _backs = [self.create_card_back(back_images[i]) for i in range(len(front_images))]
        def draw_cards(card_images,is_front):
            for idx, card in enumerate(card_images):
                col = idx % self.CARDS_PER_ROW
                row = idx // self.CARDS_PER_ROW
                if row >= self.CARDS_PER_COL:
                    break
                # Save image temporarily
                if is_front:
                    img_path = os.path.join(self.OUTPUT_DIR, f"card_{idx}_f.jpg")
                else:
                    img_path = os.path.join(self.OUTPUT_DIR, f"card_{idx}_b.jpg")    
                card.save(img_path)
                x = self.X_OFFSET + col * (self.CARD_WIDTH_PT + self.SPACING)
                y = A4[1] - self.Y_OFFSET - (row + 1) * (self.CARD_HEIGHT_PT + self.SPACING)
                self._canvas.drawImage(img_path, x, y, self.CARD_WIDTH_PT, self.CARD_HEIGHT_PT)

        draw_cards(_fronts, True)
        self._canvas.showPage()
        draw_cards(_backs,False)
        self._canvas.showPage()
        #canvas.save()


    def save_canvas(self):
        self._canvas.save()

# === Generate and Save PDFs ===
#fronts = [create_card_front(f"Card {i+1}") for i in range(9)]
#backs = [create_card_back() for _ in range(9)]

#front_pdf = os.path.join(OUTPUT_DIR, "playing_cards_front.pdf")
#back_pdf = os.path.join(OUTPUT_DIR, "playing_cards_back.pdf")
#pdf = os.path.join(OUTPUT_DIR, "playing_cards.pdf")

#draw_cards_on_pdf(fronts, front_pdf)
#draw_cards_on_pdf(backs, back_pdf)

#draw_cards_on_pdf(fronts, backs, pdf)


#print("PDFs created:")
#print("Front:", front_pdf)
#print("Back:", back_pdf)