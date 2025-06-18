from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import qr
import time


class CardGenerator:
    def __init__(self, save_path):
        self.DPI = 300
        self.CARDS_PER_ROW = 3
        self.CARDS_PER_COL = 3
        self.MIN_SPACING_PT = 5

        self.CARD_WIDTH_PT = (A4[0] - (self.MIN_SPACING_PT * (self.CARDS_PER_ROW + 1))) / self.CARDS_PER_ROW
        self.CARD_HEIGHT_PT = (A4[1] - (self.MIN_SPACING_PT * (self.CARDS_PER_COL + 1))) / self.CARDS_PER_COL
        self.CARD_WIDTH_PX = round(self.CARD_WIDTH_PT * self.DPI / 72)
        self.CARD_HEIGHT_PX = round(self.CARD_HEIGHT_PT * self.DPI / 72)

        
        self.XSPACING = self.MIN_SPACING_PT + (A4[0]-((self.CARD_WIDTH_PT * self.CARDS_PER_ROW) + (self.MIN_SPACING_PT  * 4)))/4
        self.YSPACING = self.MIN_SPACING_PT + (A4[1]-((self.CARD_HEIGHT_PT * self.CARDS_PER_COL) + (self.MIN_SPACING_PT  * 4)))/4


        self.OUTPUT_DIR = "output_cards"
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        self._canvas = canvas.Canvas(save_path, pagesize=A4)

        # === Font Setup ===
        def load_font(path, size):
            try:
                return ImageFont.truetype(path, size)
            except IOError:
                return ImageFont.load_default()

        self.font = load_font(r"fonts\\Static\\Montserrat-Regular.ttf", 60)
        self.font_latin = load_font(r"fonts\\Static\\Montserrat-Italic.ttf", 40)
        self.font_vingspann = load_font(r"fonts\\Static\\Montserrat-Regular.ttf", 40)
        self.font_wingspan = load_font("arial.ttf",90)
        self.font_birdster = load_font(r"fonts\\Static\\Montserrat-Bold.ttf", 90)

    def draw_dual_border(self, draw):
        draw.rectangle([(0, 0), (self.CARD_WIDTH_PX - 1, self.CARD_HEIGHT_PX - 1)], outline="black", width=1)
        inset = 50
        draw.rectangle(
            [(inset, inset), (self.CARD_WIDTH_PX - 1 - inset, self.CARD_HEIGHT_PX - 1 - inset)],
            outline="black", width=1
        )

    def create_card_front(self, _card):
        card = Image.new("RGB", (self.CARD_WIDTH_PX, self.CARD_HEIGHT_PX), "white")
        draw = ImageDraw.Draw(card)

        self.draw_dual_border(draw)

        # Bird image
        img_bird = Image.open(r"images\\bird2.png").convert("RGBA").resize((200, 200), Image.LANCZOS)
        bird_x = self.CARD_WIDTH_PX // 2 - img_bird.width // 2
        bird_y = 100
        card.paste(img_bird, (bird_x, bird_y), img_bird)

        # Bird name
        bird_name = _card._bird_name
        bird_name_w = draw.textlength(bird_name, self.font)
        draw.text(((self.CARD_WIDTH_PX - bird_name_w) / 2, 320), bird_name, fill="black", font=self.font)

        # Latin name
        latin_name = _card._bird_name_latin
        latin_w = draw.textlength(latin_name, self.font_latin)
        latin_y = 400
        draw.text(((self.CARD_WIDTH_PX - latin_w) / 2, latin_y), latin_name, fill="black", font=self.font_latin)

        # Line under bird image (length of latin name)
        line_y = bird_y + img_bird.height + 10
        draw.line(
            [(self.CARD_WIDTH_PX // 2 - bird_name_w // 2, line_y),
             (self.CARD_WIDTH_PX // 2 + bird_name_w // 2, line_y)],
            fill="black", width=2
        )

        # Wingspan label and value
        wingspan_label = 'Vingspann'
        wingspan_label_w = draw.textlength(wingspan_label, self.font)
        draw.text(((self.CARD_WIDTH_PX - wingspan_label_w) / 2, 650), wingspan_label, fill="black", font=self.font)

        wingspan_val = _card._wingspan
        wingspan_val_w = draw.textlength(wingspan_val, self.font_wingspan)
        draw.text(((self.CARD_WIDTH_PX - wingspan_val_w) / 2, 800), wingspan_val, fill="black", font=self.font_wingspan)

        # Wingspan image
        img_wingspan = Image.open(r"images\\wingspan2.png").convert("RGBA").resize((300, 150), Image.LANCZOS)
        card.paste(img_wingspan, (self.CARD_WIDTH_PX // 2 - 150, self.CARD_HEIGHT_PX - 200), img_wingspan)

        return card

    def create_card_back(self, _card):
        card = Image.new("RGB", (self.CARD_WIDTH_PX, self.CARD_HEIGHT_PX), "white")
        draw = ImageDraw.Draw(card)

        self.draw_dual_border(draw)

        # Title
        text = "Birdster"
        text_w = draw.textlength(text, self.font_birdster)
        draw.text(((self.CARD_WIDTH_PX - text_w) / 2, 150), text, fill="black", font=self.font_birdster)

        line_y = ((self.CARD_WIDTH_PX - text_w) / 2) +100
        draw.line(
            [(self.CARD_WIDTH_PX // 2 - text_w // 2, line_y),
             (self.CARD_WIDTH_PX // 2 + text_w // 2, line_y)],
            fill="black", width=4
        )

        # QR code
        qr_size = 400
        img = qr.create_qr_code(_card._default_URL + _card._mapping, qr_size)
        img = img.resize((qr_size, qr_size), Image.LANCZOS)
        img_x = (self.CARD_WIDTH_PX - qr_size) // 2
        img_y = (self.CARD_HEIGHT_PX - qr_size) // 2 + 50




        card.paste(img, (img_x, img_y))

        return card

    def create_card_back_special(self, _card):
        card = Image.new("RGB", (self.CARD_WIDTH_PX, self.CARD_HEIGHT_PX), "white")
        draw = ImageDraw.Draw(card)

        self.draw_dual_border(draw)

                # Title
        text = "Birdster"
        text_w = draw.textlength(text, self.font_birdster)
        draw.text(((self.CARD_WIDTH_PX - text_w) / 2, 350), text, fill="black", font=self.font_birdster)

        line_y = ((self.CARD_WIDTH_PX - text_w) / 2) +280
        draw.line(
            [(self.CARD_WIDTH_PX // 2 - text_w // 2, line_y),
             (self.CARD_WIDTH_PX // 2 + text_w // 2, line_y)],
            fill="black", width=4
        )

        img_wingspan = Image.open(r"images\\wingspan2.png").convert("RGBA").resize((300, 150), Image.LANCZOS)
        card.paste(img_wingspan, (self.CARD_WIDTH_PX // 2 - 150, self.CARD_HEIGHT_PX - 200), img_wingspan)

        return card





    def draw_cards_on_pdf(self, front_images, back_images, special_cards):
        _fronts = [self.create_card_front(img) for img in front_images]
        _backs = self.reorder_cards([self.create_card_back(img) for img in back_images])

        _special = [self.create_card_back_special(img) for img in special_cards]
        
        def draw_cards(card_images, is_front):
            for idx, card in enumerate(card_images):
                col = idx % self.CARDS_PER_ROW
                row = idx // self.CARDS_PER_ROW
                if row >= self.CARDS_PER_COL:
                    break

                filename = f"card_{idx}_{'f' if is_front else 'b'}_{int(time.time())}.png"
                path = os.path.join(self.OUTPUT_DIR, filename)
                card.save(path, dpi=(self.DPI, self.DPI))
                
                
                x = self.XSPACING + col * (self.CARD_WIDTH_PT + self.XSPACING)
                y = self.YSPACING + row * (self.CARD_HEIGHT_PT + self.YSPACING)

                print(f"xspace:{self.XSPACING} y:space{self.YSPACING} x:{x} y:{y} rightX:{A4[0] - (x+self.CARD_WIDTH_PT)} downY:{A4[1]-(y + self.CARD_HEIGHT_PT)}")
                print(f"xspace:{self.XSPACING * self.DPI / 72:.2f}px "
                        f"yspace:{self.YSPACING * self.DPI / 72:.2f}px "
                        f"x:{x * self.DPI / 72:.2f}px "
                        f"y:{y * self.DPI / 72:.2f}px "
                        f"rightX:{(A4[0] - (x + self.CARD_WIDTH_PT)) * self.DPI / 72:.2f}px "
                        f"downY:{(A4[1] - (y + self.CARD_HEIGHT_PT)) * self.DPI / 72:.2f}px")

                self._canvas.drawImage(path, x, y, width=self.CARD_WIDTH_PT, height=self.CARD_HEIGHT_PT)
        if len(special_cards) == 9:
            draw_cards(_special, False)    
            self._canvas.showPage()
            _special_again = [self.create_card_back_special(img) for img in special_cards]
            draw_cards(_special_again,False)
            self._canvas.showPage()
        else:
            print()
            draw_cards(_fronts, True)
            self._canvas.showPage()
            draw_cards(_backs, False)
            self._canvas.showPage()





    def reorder_cards(self, cards):
        indices = [2, 1, 0, 5, 4, 3, 8, 7, 6]
        return [cards[i] for i in indices if i < len(cards)]

    def save_canvas(self):
        self._canvas.save()
