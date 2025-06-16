from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import qr
from datetime import datetime
import time


class CardGenerator:
    def __init__(self, save_path):
        # === Configuration ===
        self.CARD_WIDTH_PX, self.CARD_HEIGHT_PX = 190, 270  # ~2.5x3.5 inches at 90 DPI
        self.DPI = 1 # px to PDF points
        self.CARD_WIDTH_PT = self.CARD_WIDTH_PX * self.scale        self.CARD_HEIGHT_PT = self.CARD_HEIGHT_PX * self.scale
        self.CARDS_PER_ROW = 3
        self.CARDS_PER_COL = 3
        self.XSPACING = (A4[0] -  (self.CARD_WIDTH_PX * 3)) / 4
        self.YSPACING = (A4[1] -  (self.CARD_HEIGHT_PX * 3)) / 4

        #self.X_OFFSET = 20
        #self.Y_OFFSET = 20
        self.OUTPUT_DIR = "output_cards"
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        self._canvas = canvas.Canvas(save_path, pagesize=A4)
        # === Font Setup ===
        try:
            
            print(os.path.exists(""))
            #self.font = ImageFont.truetype("montserrat.ttf", 20)
            self.font = ImageFont.truetype(r"fonts\\Static\\Montserrat-Regular.ttf", 20)
        except IOError:
            self.font = ImageFont.load_default()
        
        try:
            self.font_latin = ImageFont.truetype(r"fonts\\Static\\Montserrat-Italic.ttf", 13)
        except IOError:
            self.font_latin = ImageFont.load_default()

        try:
            self.font_vingspann = ImageFont.truetype(r"fonts\\Static\\Montserrat-Regular.ttf",     13)
        except IOError:
            self.font_vingspann = ImageFont.load_default()

        try:
            self.font_wingspan = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            self.font_wingspan = ImageFont.load_default()    

        try:
            self.font_birdster = ImageFont.truetype(r"fonts\\Static\\Montserrat-Bold.ttf", 20)
        except IOError:
            self.font_birdster = ImageFont.load_default()   



    # === Card Creation ===
    def create_card_front(self,_card):
        card = Image.new("RGB", (self.CARD_WIDTH_PX, self.CARD_HEIGHT_PX), "white")
        #card = Image.new("RGBA", (self.CARD_WIDTH_PX, self.CARD_HEIGHT_PX), (255, 255, 255, 0))
        draw = ImageDraw.Draw(card)
        

        #card.paste(img_bird, (0,0))


        # Placeholder for image
        #draw.rectangle([0, 0, CARD_WIDTH_PX, int(CARD_HEIGHT_PX * 0.6)], fill="lightgray")
        # Text


        w = draw.textlength(_card._bird_name, self.font)
        draw.text(((self.CARD_WIDTH_PX // 2)-w//2,  80), _card._bird_name, fill="black", font=self.font)

        w = draw.textlength(_card._bird_name_latin, self.font_latin)
        draw.text(((self.CARD_WIDTH_PX // 2)-w//2,  110), _card._bird_name_latin, fill="black", font=self.font_latin)

        wingspan_text = 'Vingspann'
        w = draw.textlength(wingspan_text, self.font_vingspann)
        draw.text(((self.CARD_WIDTH_PX // 2)-w//2,  170), wingspan_text , fill="black", font=self.font_vingspann)
        
        w = draw.textlength(_card._wingspan, self.font_wingspan)
        draw.text(((self.CARD_WIDTH_PX // 2)-w//2,  190), _card._wingspan, fill="black", font=self.font_wingspan)
        #draw.rectangle([0, 0, self.CARD_WIDTH_PX - 1, self.CARD_HEIGHT_PX - 1], outline="black", width=1)
        #draw.line([(0, 0), (self.CARD_WIDTH_PX - 1, 0)], fill="black")  # Top
        #draw.line([(0, 0), (0, self.CARD_HEIGHT_PX - 1)], fill="black")  # Left
        #draw.line([(self.CARD_WIDTH_PX - 1, 0), (self.CARD_WIDTH_PX - 1, self.CARD_HEIGHT_PX - 1)], fill="black")  # Right
        #draw.line([(0, self.CARD_HEIGHT_PX - 1), (self.CARD_WIDTH_PX - 1, self.CARD_HEIGHT_PX - 1)], fill="black")  # Bottom
        
        draw.line([(0, 0), (self.CARD_WIDTH_PX - 2, 0)], fill="black")  # Top
        draw.line([(0, 0), (0, self.CARD_HEIGHT_PX - 2)], fill="black")  # Left
        draw.line([(self.CARD_WIDTH_PX - 1, 0), (self.CARD_WIDTH_PX - 1, self.CARD_HEIGHT_PX - 1)], fill="black")  # Right
        draw.line([(0, self.CARD_HEIGHT_PX - 1), (self.CARD_WIDTH_PX - 1, self.CARD_HEIGHT_PX - 1)], fill="black")  # Bottom
        
        bird_x = 40
        bird_y = 50
        img_bird = Image.open(r"images\\bird2.png").resize((bird_x, bird_y))
        card.paste(img_bird, (self.CARD_WIDTH_PT//2 - bird_x//2 , 15), img_bird)

        vinge_x = 70
        vinge_y = 40
        img_wingspan= Image.open(r"images\\wingspan2.png").resize((vinge_x, vinge_y))
        card.paste(img_wingspan, (self.CARD_WIDTH_PT//2 - vinge_x//2 , self.CARD_HEIGHT_PX-50), img_wingspan) #170


        #card.paste(img_bird, (0,0), img_bird)
        return card

    def create_card_back(self,_card):
        qr_size = 120
        text = 'Birdster'
        card = Image.new("RGB", (self.CARD_WIDTH_PX, self.CARD_HEIGHT_PX), "white")
        draw = ImageDraw.Draw(card)

        w = draw.textlength(text, self.font_birdster)
        draw.text(((self.CARD_WIDTH_PX // 2)-w//2, 30), text, fill="black", font=self.font_birdster)
        img = qr.create_qr_code(_card._default_URL + _card._mapping, qr_size)

        img_x = ((self.CARD_WIDTH_PX) // 2) - (qr_size//2)
        img_y = ((self.CARD_HEIGHT_PX ) // 2) - (qr_size//2)
        
        card.paste(img, (img_x,img_y))
        draw.line([(0, 0), (self.CARD_WIDTH_PX - 2, 0)], fill="black")  # Top
        draw.line([(0, 0), (0, self.CARD_HEIGHT_PX - 2)], fill="black")  # Left
        draw.line([(self.CARD_WIDTH_PX - 1, 0), (self.CARD_WIDTH_PX - 1, self.CARD_HEIGHT_PX - 1)], fill="black")  # Right
        draw.line([(0, self.CARD_HEIGHT_PX - 1), (self.CARD_WIDTH_PX - 1, self.CARD_HEIGHT_PX - 1)], fill="black")  # Bottom

        #draw.rectangle([0, 0, self.CARD_WIDTH_PX - 1, self.CARD_HEIGHT_PX - 1], outline="black", width=2)
        return card

    # === PDF Layout ===
    def draw_cards_on_pdf(self,front_images, back_images):
        #c = canvas.Canvas(pdf_path, pagesize=A4)
        #_fronts = [self.create_card_front(front_images[i]) for i in range(len(front_images))]
        #_backs = [self.create_card_back(back_images[i]) for i in range(len(back_images))]
        _fronts = [self.create_card_front(img) for img in front_images]
        _backs = [self.create_card_back(img) for img in back_images]
        _backs = self.reorder_cards(_backs)
        
        def draw_cards(card_images,is_front):
            for idx, card in enumerate(card_images):
                col = idx % self.CARDS_PER_ROW
                row = idx // self.CARDS_PER_ROW
                if row >= self.CARDS_PER_COL:
                    break
                # Save image temporarily
                if is_front:
                    img_path = os.path.join(self.OUTPUT_DIR, f"card_{idx}_f_{time.time()}.png")
                else:
                    img_path = os.path.join(self.OUTPUT_DIR, f"card_{idx}_b_{time.time()}.png")    
                card.save(img_path)

                #total_row_width = self.CARDS_PER_ROW * self.CARD_WIDTH_PT + (self.CARDS_PER_ROW - 1) * self.SPACING
                #x_offset = (A4[0] - total_row_width) / 2
                #x = x_offset + col * (self.CARD_WIDTH_PT + self.SPACING)
                
                x = self.XSPACING + (col * (self.XSPACING + self.CARD_WIDTH_PT))
                y = self.YSPACING + (row * (self.YSPACING + self.CARD_HEIGHT_PT))


                #total_col_height = self.CARDS_PER_COL * self.CARD_HEIGHT_PT + (self.CARDS_PER_COL - 1) * self.SPACING
                #y_offset = (A4[1] - total_col_height) / 2
                #y = A4[1] - y_offset - (row + 1) * (self.CARD_HEIGHT_PT + self.SPACING)
                #x = self.X_OFFSET + col * (self.CARD_WIDTH_PT + self.SPACING)
                #y = A4[1] - self.Y_OFFSET - (row + 1) * (self.CARD_HEIGHT_PT + self.SPACING)
                self._canvas.drawImage(img_path, x, y, self.CARD_WIDTH_PT, self.CARD_HEIGHT_PT)

        draw_cards(_fronts, True)
        self._canvas.showPage()
        draw_cards(_backs,False)
        self._canvas.showPage()
        #canvas.save()

    def reorder_cards(self, cards):
        new_lst = []
        if len(cards) > 2:
            new_lst.append(cards[2])
        if len(cards) > 1:
            new_lst.append(cards[1])
        if len(cards) > 0:
            new_lst.append(cards[0])
        if len(cards) > 5:
            new_lst.append(cards[5])
        if len(cards) > 4:
            new_lst.append(cards[4])
        if len(cards) > 3:
            new_lst.append(cards[3])
        if len(cards) > 8:
            new_lst.append(cards[8])
        if len(cards) > 7:
            new_lst.append(cards[7])
        if len(cards) > 6:
            new_lst.append(cards[6])
        return new_lst

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