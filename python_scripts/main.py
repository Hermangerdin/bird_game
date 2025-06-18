import Card
import cardGenerator
import qr
import os

OUTPUT_DIR = "..\\output"


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    cards = Card.fill_cards(r"..\\Fågelinfo.xlsx")
    
    pdf_path = r"..\\output\\playing_cards.pdf"
    
    i = 0
    fronts = []
    backs = []
    card_generator = cardGenerator.CardGenerator(pdf_path)
    for card in cards:
        if (i%9 == 0 and i != 0) or i == len(cards)-1:
            card_generator.draw_cards_on_pdf(fronts, backs, [])
            fronts = []
            backs = []

        fronts.append(card)
        backs.append(card)
        i +=1
    card_generator.draw_cards_on_pdf(fronts,backs,[Card.Card(), Card.Card(), Card.Card(), Card.Card(), Card.Card(),Card.Card(),Card.Card(),Card.Card(),Card.Card()])
    print("PDFs created:")     
    card_generator.save_canvas()




