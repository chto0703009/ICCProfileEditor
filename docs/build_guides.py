# Copyright (c) 2026 Christer Törnkvist.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the two one-page user guides with ReportLab."""
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parent
REPO = 'https://github.com/chto0703009/ICCProfileEditor'
VERSION = '1.0.3'
ICON = ROOT.parent / 'resources/editor-header.png'
GUIDES = {
    'SV': (
        'Användarguide',
        'Ändra profilnamn och copyright i ICC v2 och v4 på macOS.',
        (
            ('Installera', 'Öppna DMG-filen för Apple Silicon och dra ICC Profile Editor till Program. Mata ut skivavbilden och öppna appen från Program.'),
            ('Välj profil', 'Klicka på <b>Open ICC…</b> eller tryck på Kommando-O. Välj en fil med ändelsen .icc eller .icm.'),
            ('Redigera och spara', 'Ändra <b>Internal profile name</b> eller <b>Copyright</b>. Det interna namnet visas i många profillistor och är oberoende av filnamnet. Klicka på <b>Save Copy…</b> och välj ett nytt filnamn. Appen skapar en kopia och bevarar originalet, färgtabellerna och övriga ICC-taggar.'),
            ('Senast använda mappar', 'Filväljaren börjar på skrivbordet. Appen minns senaste profilmapp och sparmapp mellan starter. Första kopian föreslås i profilmappen.'),
            ('Text i ICC v2 och v4', 'Ny copyrighttext i ICC v2 måste använda ASCII. Skriv till exempel (C) i stället för ©. Befintlig copyright bevaras när du lämnar fältet oförändrat. I ICC v4 uppdateras profilnamnets språkposter till det namn du anger.'),
        ),
        'Ladda ned appen', 'Teknisk dokumentation',
    ),
    'EN': (
        'User guide',
        'Edit profile names and copyright in ICC v2 and v4 profiles on macOS.',
        (
            ('Install', 'Open the Apple Silicon disk image and drag ICC Profile Editor to Applications. Eject the disk image and open the app from Applications.'),
            ('Choose a profile', 'Click <b>Open ICC…</b> or press Command-O. Choose an .icc or .icm file.'),
            ('Edit and save', 'Change <b>Internal profile name</b> or <b>Copyright</b>. The internal name appears in many profile lists and is independent of the filename. Click <b>Save Copy…</b> and choose a new filename. The app creates a copy and preserves the source file, colour tables and other ICC tags.'),
            ('Recent folders', 'The file picker starts on the Desktop. The app remembers your last profile folder and your last save folder between launches. The first copy defaults to the profile folder.'),
            ('Text in ICC v2 and v4', 'New copyright text in ICC v2 must use ASCII. For example, use (C) instead of ©. Existing copyright is preserved when you leave the field unchanged. In ICC v4, all language entries for the profile name are updated to the name you enter.'),
        ),
        'Download the app', 'Technical documentation (Swedish)',
    ),
}

INK = HexColor('#172b3a')
ACCENT = HexColor('#00665e')
STYLES = {
    'tag': ParagraphStyle('tag', fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=ACCENT, keepWithNext=True),
    'title': ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=32, leading=37, textColor=INK, spaceAfter=8, keepWithNext=True),
    'lead': ParagraphStyle('lead', fontName='Helvetica', fontSize=13, leading=19, textColor=INK, spaceAfter=22),
    'heading': ParagraphStyle('heading', fontName='Helvetica-Bold', fontSize=14, leading=19, textColor=ACCENT, spaceAfter=5, keepWithNext=True),
    'body': ParagraphStyle('body', fontName='Helvetica', fontSize=11, leading=17, textColor=INK, spaceAfter=16, alignment=TA_LEFT),
}


def paragraph(text, style):
    return Paragraph(text, STYLES[style])


def build():
    for lang, (label, lead, sections, download, details) in GUIDES.items():
        path = ROOT / f'ICC-Profile-Editor-{lang}.pdf'
        document = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=23*mm, rightMargin=23*mm,
                                     topMargin=23*mm, bottomMargin=23*mm,
                                     title=f'ICC Profile Editor | {label}', author='Christer Törnkvist')
        story = [Image(str(ICON), width=13*mm, height=13*mm, hAlign='LEFT'), Spacer(1, 3*mm),
                 paragraph(f'{label.upper()} &nbsp; · &nbsp; {VERSION}', 'tag'), Spacer(1, 5*mm),
                 paragraph('ICC Profile Editor', 'title'), paragraph(lead, 'lead')]
        for name, content in sections:
            story.extend((paragraph(name, 'heading'), paragraph(content, 'body')))
        story.append(paragraph(f'<link href="{REPO}/releases/tag/v{VERSION}" color="#00665e">{download}</link>'
                               f' &nbsp; · &nbsp; <link href="{REPO}/blob/v{VERSION}/DOKUMENTATION.md" color="#00665e">{details}</link>', 'body'))
        document.build(story)


if __name__ == '__main__':
    build()
