import pandas as pd

class Card:
    def __init__(self):
        self._bird_name = ''
        self._bird_name_latin = ''
        self._wingspan = ''
        self._link = ''
        self._cat_nr = ''
        self._mapping = ''

        self._default_URL = r'https://hermangerdin.github.io/bird_game/?token=secretBirdSound123&sound='


    def card_is_valid(self):
        return (self._bird_name != '') and (self._bird_name_latin != '') and  (self._wingspan != '') and (self._link != '') and (self._cat_nr != '') and (self._mapping != '')

    

def fill_cards(excel_path):
    excel_file = pd.read_excel(excel_path)
    excel_file.fillna('', inplace=True)
    cards = []    
    for index, row in excel_file.iterrows():
        card = Card()
        card._bird_name = str(excel_file['Namn'][index])
        card._bird_name_latin = str(excel_file['Namn latin'][index])
        card._wingspan= str(excel_file['Vingspann'][index])
        card._link = str(excel_file['Länk till inspelning'][index])
        card._cat_nr = str(excel_file['Cat.nr'][index])
        card._mapping = str(excel_file['Mappning'][index])
        if card.card_is_valid():
            cards.append(card)
        else:
            print(f"{excel_path}: Invalid row {index}")

    return cards       



'''
        card._bird_name = str(row[0])
        card._bird_name_latin = str(row[1]) 
        card._wingspan= str(row[2])
        card._link = str(row[3])
        card._cat_nr = str(row[4])
        card._mapping = str(row[5])




'''

