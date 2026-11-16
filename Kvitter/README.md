# Kvitter

Fristående Windows-mapp för att separera fågelljud med Bird-MixIT och redigera
ett sammanhängande ljudurval.

## Krav

- Windows 10 eller 11.
- Python 3.10 installerat, inklusive Python Launcher (`py`).
- Internetanslutning första gången programmet startas för att installera Python-paketen.

## Starta programmet

1. Öppna projektmappen `Kvitter`.
2. Dubbelklicka på `start.bat`.
3. Vänta medan den virtuella miljön och paketen installeras första gången.
4. Öppna adressen som visas i konsolfönstret, normalt `http://127.0.0.1:8501`.

Låt konsolfönstret vara öppet medan programmet används. Stäng fönstret för att
avsluta servern. Nästa start använder samma miljö och går snabbare.

## Arbetsflöde

1. Välj medföljande testinspelning eller ladda upp en egen ljudfil.
2. Spela upp originalet och kör **Separera inspelningen**. Första gången behöver
   du hämta Bird-MixIT-modellen.
3. Välj ett av de fyra uppskattade modellspåren och spela upp det.
4. Välj **Normalisera** för att ta bort DC-offset och ställa toppnivån till
   -1 dBFS, med länkad förstärkning så att kanalbalansen bevaras.
5. Dra över vågformen för att markera en sammanhängande del. Använd verktygsfältet
   för att zooma och panorera, eller ange exakta start- och sluttider.
6. Spela upp originalet och det valda modellspåret bredvid varandra. Båda
   förhandsvisningarna använder samma tidsgränser. Hämta det redigerade ljudet
   som WAV.

Originalinspelningen ändras inte. Waveform-editorn arbetar på det valda
Bird-MixIT-spåret. Markeringen begränsas till den tid som finns i både originalet
och modellspåret.

## Bird-MixIT-separering

Separeringen kör i en separat Python-miljö för att hålla TensorFlow:s
versionskrav åtskilda från Streamlit-appen.

1. Dubbelklicka på `setup_separation.bat`. Det skapar `.venv-separation` och
   installerar TensorFlow-miljön. Det kräver internet och kan ta en stund.
2. Starta appen med `start.bat` och välj testinspelning eller ladda upp ett ljud.
3. Välj **Hämta Bird-MixIT-modellen**. Appen hämtar de officiella vikterna
   (cirka 108 MiB), kontrollerar dem och sparar dem i
   `.models/bird_mixit/output_sources4/`.
4. Välj **Separera inspelningen**. Separeringen kan ta en stund på CPU.

Modellvikterna ingår inte i projektmappen och ignoreras av Git via `.gitignore`.
Du behöver bara ladda ner dem en gång per projektkopia.

Bird-MixIT-modellen använder mono och 22,05 kHz. De fyra spåren är uppskattningar,
inte säkert ett spår per fågel. En källa kan innehålla flera fåglar,
bakgrundsljud eller artefakter.

Modellen och vikterna tillhandahålls av
[Google Research Sound Separation](https://github.com/google-research/sound-separation/tree/master/models/bird_mixit)
under Apache-2.0-licensen. Modellen hämtas inte med programfilerna.

## Filer och resultat

- `XC1047941 - nötskrika - Garrulus glandarius.wav`: medföljande testinspelning.
- `output/bird_mixit/`: separerade modellspår.
- `.venv/`, `.venv-separation/` och `.models/bird_mixit/`: skapas lokalt vid behov
  och ignoreras av Git.

## Kör tester

Öppna PowerShell i mappen och kör:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
