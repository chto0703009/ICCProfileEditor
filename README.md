# ICC Profile Editor

Fristående macOS-app för att ändra det interna profilnamnet och copyright i ICC v2- och v4-profiler. Öppna en profil, ändra fälten och välj **Spara kopia**. Dialogen föreslår ett filnamn utifrån profilnamnet. Appen bevarar källfilen, färgtabellerna och övriga ICC-taggar.

## Installera på macOS

Hämta DMG-filen från [Releases](https://github.com/chto0703009/ICCProfileEditor/releases/latest). Öppna den och dra **ICC Profile Editor** till **Program**. Appen är byggd för Apple Silicon och inkluderar Python och Tk.

Utförlig beskrivning av hur appen läser, skriver och sparar profiler finns i [DOKUMENTATION.md](DOKUMENTATION.md).

## Kör källkoden

Använd Python 3 med Tkinter.

```sh
python3 icc_profile_editor.py
```

## Bygg macOS-appen

Använd Python 3 med Tkinter. Skapa en separat virtuell miljö för bygget.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python -m PyInstaller --windowed --name 'ICC Profile Editor' \
  --osx-bundle-identifier se.borgasundsfotografiska.iccprofileeditor \
  icc_profile_editor.py
```

Appen byggs i `dist/`.

## Licens

Källkoden är licensierad under [GNU GPL v3 eller senare](LICENSE).
