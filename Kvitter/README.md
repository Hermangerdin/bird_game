# Kvitter

Fristående Windows-mapp för att granska, klippa och valfritt separera fågelljud.

## Krav

- Windows 10 eller 11.
- Python 3.10 installerat, inklusive Python Launcher (`py`).
- Internetanslutning första gången programmet startas för att installera Python-paketen.

## Starta programmet

1. Öppna projektmappen `Kvitter`.
2. Dubbelklicka på `start.bat`.
3. Vänta medan den virtuella miljön och paketen installeras första gången.
4. Öppna adressen som visas i konsolfönstret, normalt `http://127.0.0.1:8501`.

Låt konsolfönstret vara öppet medan programmet används. Stäng fönstret för att avsluta servern. Nästa start använder samma miljö och går snabbare.

## Klippningsläge

Välj testljudet eller ladda upp en egen ljudfil. WAV, FLAC, MP3, OGG, AIFF, AU och CAF stöds. Granska vågform och spektrogram, ändra detektionsinställningar, välj **Hitta klipp**, redigera start/slut och lyssna innan export. Godkända klipp och en CSV-lista sparas i `output/`. Originalinspelningen ändras inte.

Klippningsläget hittar ljudaktivitet, inte fågelarter eller individer. Inställningen för tystnadssammanfogning avgör om närliggande händelser blir ett längre klipp.

## Bird-MixIT-separering (valfritt)

Separeringen kör i en separat Python-miljö så att den inte påverkar klippningsläget.

1. Dubbelklicka på `setup_separation.bat`. Det skapar `.venv-separation` och installerar den separata TensorFlow-miljön. Det kräver internet och kan ta en stund; klippningsläget påverkas inte.
2. Starta appen med `start.bat` och välj **Bird-MixIT-separering**.
3. Välj **Hämta Bird-MixIT-modellen**. Appen hämtar de officiella vikterna (cirka 108 MiB), kontrollerar dem och sparar dem i `.models/bird_mixit/output_sources4/`.
4. Välj **Separera inspelningen** och lyssna på eller hämta de fyra spåren.

Modellvikterna ingår inte i projektmappen och ignoreras av Git via `.gitignore`. Du behöver bara ladda ner dem en gång per projektkopia.

Bird-MixIT-modellen använder mono och 22,05 kHz och körs på CPU i standardkonfigurationen. Spåren är uppskattningar, inte säkert ett spår per fågel. En källa kan innehålla flera fåglar, bakgrundsljud eller artefakter. Originalet lämnas orört.

Modellen och vikterna tillhandahålls av [Google Research Sound Separation](https://github.com/google-research/sound-separation/tree/master/models/bird_mixit) under Apache-2.0-licensen. Modellen hämtas inte med programfilerna.

## Filer och resultat

- `XC1047941 - nötskrika - Garrulus glandarius.wav`: medföljande testinspelning.
- `output/`: skapade klipp, separerade ljudspår och CSV-listor.
- `.venv/`, `.venv-separation/` och `.models/bird_mixit/`: skapas lokalt vid behov och ignoreras av Git.

## Kör tester

Öppna PowerShell i mappen och kör:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
