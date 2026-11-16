# ICC Profile Editor – dokumentation

ICC Profile Editor ändrar det interna profilnamnet och copyrighttexten i en ICC-profil och sparar resultatet som en ny fil. Källfilen ändras aldrig, och färgdata och övriga taggar kopieras oförändrade.

Appen hanterar ICC-profiler (`.icc` och `.icm`) i version 2 och 4. Andra filtyper, till exempel QuadToneRIP-kurvor (`.qtr`, `.quad`), stöds inte.

## Använda appen

1. Välj **Open ICC…** (eller ⌘O) och välj en profil.
2. Ändra **Internal profile name** och/eller **Copyright**.
3. Välj **Save Copy…**. Dialogen föreslår ett filnamn som bygger på profilnamnet, i den senast använda sparmappen.

Det interna profilnamnet är det namn som program som Photoshop, Lightroom och ColorSync-verktyget visar. Det är oberoende av filnamnet.

## Vad som ändras och vad som bevaras

| Del av profilen | Vad som händer |
| --- | --- |
| Taggen `desc` (profilnamn) | I v4 skrivs taggen om när någon språkpost skiljer sig från det valda namnet. I v2 skrivs taggen om när namnet ändras. |
| Taggen `cprt` (copyright) | Skrivs om om texten har ändrats |
| Övriga taggar (färgtabeller, kurvor, vitpunkt m.m.) | Kopieras byte för byte |
| Huvudet | Bevaras, utom filstorlek och profil-ID |
| Taggarnas placering i filen | Läggs om; identiska taggar delar data |

När du bara byter namn bevaras befintlig copyright byte för byte.

## Hur text läses och skrivs

### ICC version 4

Text lagras som flerspråkig Unicode (`mluc`).

- **Läsning:** posten för `enUS` visas. Saknas den visas den första posten.
- **Skrivning:** alla språkposter som finns i taggen får den nya texten. Det gör att inget språk fortsätter visa det gamla namnet, men det betyder också att befintliga översättningar ersätts. Finns ingen post skapas `enUS`.

### ICC version 2

- **Profilnamn** (`desc`) innehåller både ett ASCII-namn och ett Unicode-namn. Unicode-namnet visas om det finns; är det tomt eller trasigt visas ASCII-namnet. Vid skrivning fylls båda i. Tecken utanför ASCII ersätts med `?` i ASCII-delen.
- **Copyright** (`text`) använder 7-bitars ASCII enligt ICC v2. Befintlig text läses ändå som UTF-8 och annars Windows-1252 för kompatibilitet med äldre filer. Om du lämnar copyright oförändrad bevaras taggens byte. Ny copyrighttext måste vara ASCII. Skriv till exempel (C) i stället för ©.

Äldre Mac-profiler som använder MacRoman kan visa andra specialtecken än © fel, eftersom formatet inte talar om vilken kodning som använts.

## Profil-ID

Profil-ID är en MD5-summa över profilen som lagras i huvudet.

- **Version 4:** räknas alltid om.
- **Version 2:** räknas om om profilen redan har ett ID. Är fältet tomt lämnas det tomt.

## Öppnings- och sparmappar

**Open ICC…** börjar på skrivbordet och minns därefter den senast öppnade profilmappen. **Save Copy…** börjar i källmappen första gången. Därefter öppnas den senast använda sparmappen. Appen minns mapparna när du startar om den.

## Spara

- Kopian skrivs först till en tillfällig fil, kontrolläses och får sedan sitt slutliga namn. På volymer med hårda länkar blir kopian synlig under sitt slutliga namn först efter att den skrivits och kontrollästs.
- En befintlig fil skrivs aldrig över. Välj ett nytt namn om filen redan finns.
- Filnamnet måste sluta på `.icc` eller `.icm`.
- Kopian får vanliga filrättigheter (normalt läsbar för alla, skrivbar för ägaren).
- Det går att spara även om källfilen har flyttats, bytt namn eller ligger på en utmatad volym, eftersom kopian byggs från det som lästes in när profilen öppnades.
- Volymer utan stöd för hårda länkar (exFAT, FAT, vissa nätverksvolymer) fungerar. Där skapas filen direkt i stället för via länk. Om programmet avslutas mitt under skrivningen kan en ofullständig kopia ligga kvar.

## Kontroller vid öppning

En fil avvisas om något av följande gäller:

- den saknar ICC-signaturen `acsp` eller är kortare än storleken som anges i huvudet
- versionen är en annan än 2 eller 4
- taggtabellen är ofullständig, en tagg pekar utanför filen eller samma tagg förekommer två gånger
- profilnamn eller copyright har en texttyp som appen inte kan läsa

En fil som är längre än den angivna storleken öppnas. De överskjutande byten räknas som utfyllnad och tas inte med i kopian.

## Begränsningar

- Endast profilnamn och copyright kan redigeras.
- Översättningar i version 4-profiler kan inte redigeras var för sig.
- I version 2-profiler bevaras inte ScriptCode-delen av `desc` när namnet skrivs om.
- ICC version 5 (iccMAX) stöds inte.
- Den universella macOS-appen stöder både Apple Silicon och Intel. Den inkluderar Python och Tcl/Tk.

## Kodens uppbyggnad

All kod ligger i `icc_profile_editor.py`.

| Funktion | Uppgift |
| --- | --- |
| `profile_tags` | Kontrollerar huvudet och taggtabellen och returnerar taggarna |
| `translations` | Läser språkposterna i en `mluc`-tagg |
| `legacy_text` | Avkodar v2-text (UTF-8, annars Windows-1252) |
| `read_text` | Läser text ur `mluc`, `text` eller `desc` |
| `multilingual_text` | Bygger en ny `mluc`-tagg |
| `edit_profile` | Byter ut text, lägger om taggarna och räknar om profil-ID |
| `save_copy`, `write_new` | Skriver kopian utan att ersätta befintliga filer |
| `Editor` | Fönstret (Tkinter) |

Funktionerna ovanför `Editor` är fristående från gränssnittet och kan användas från ett skript:

```python
from pathlib import Path
from icc_profile_editor import edit_profile, save_copy

data = Path("original.icc").read_bytes()
save_copy(Path("kopia.icc"), edit_profile(data, "Nytt namn", "Copyright 2026"))
```

## Bygga appen

Se [README.md](README.md). Bygget lägger appen i `dist/` och behöver göras om efter varje ändring i källkoden.
