# Copyright (c) 2026 Christer Törnkvist.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read and edit ICC v2/v4 descriptions and copyright without replacing files."""
import hashlib
import os
from pathlib import Path
import re
import struct
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def uint32(data, offset):
    return struct.unpack_from(">I", data, offset)[0]


def profile_tags(data):
    if len(data) < 132 or data[36:40] != b"acsp" or not 132 <= uint32(data, 0) <= len(data):
        raise ValueError("Filen har ett ogiltigt ICC-huvud eller fel filstorlek.")
    # Some writers pad the file beyond the declared profile size; ignore the padding.
    data = data[:uint32(data, 0)]
    if data[8] not in (2, 4):
        raise ValueError("Appen stöder ICC version 2 och 4.")
    count = uint32(data, 128)
    end = 132 + 12 * count
    if end > len(data):
        raise ValueError("ICC-filens taggtabell är ofullständig.")
    tags = {}
    for index in range(count):
        tag, offset, size = struct.unpack_from(">4sII", data, 132 + 12 * index)
        if tag in tags or offset < end or size < 8 or offset + size > len(data):
            raise ValueError("ICC-filen har en ogiltig tagg.")
        tags[tag] = data[offset:offset + size]
    return tags


def translations(block):
    if len(block) < 16:
        raise ValueError("Ofullständig flerspråkig ICC-text.")
    count, stride = struct.unpack_from(">II", block, 8)
    end = 16 + count * stride
    if stride < 12 or end > len(block):
        raise ValueError("Ogiltig tabell för flerspråkig ICC-text.")
    records = []
    for index in range(count):
        locale, length, offset = struct.unpack_from(">4sII", block, 16 + index * stride)
        if length % 2 or offset < end or offset + length > len(block):
            raise ValueError("Ogiltig position för ICC-text.")
        records.append((locale, block[offset:offset + length]))
    return records


def legacy_text(raw):
    # ICC v2 text is nominally ASCII, but © and ® are common in practice.
    raw = raw.rstrip(b"\0")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def read_text(block):
    kind = block[:4]
    if not kind:
        return ""
    if kind == b"mluc":
        records = translations(block)
        if not records:
            return ""
        text = next((text for locale, text in records if locale == b"enUS"), records[0][1])
        return text.decode("utf-16-be").rstrip("\0")
    if kind == b"text":
        return legacy_text(block[8:])
    if kind == b"desc" and len(block) >= 12:
        end = 12 + uint32(block, 8)
        if end > len(block):
            raise ValueError("Profilnamnet är ofullständigt.")
        if end + 8 <= len(block):
            count = uint32(block, end + 4)
            start = end + 8
            if count and start + 2 * count <= len(block):
                # An empty or broken Unicode name falls back to the ASCII name.
                try:
                    text = block[start:start + 2 * count].decode("utf-16-be").rstrip("\0")
                except UnicodeDecodeError:
                    text = ""
                if text:
                    return text
        return legacy_text(block[12:end])
    raise ValueError("ICC-filen har ett textformat som appen inte stöder.")


def multilingual_text(old, value):
    # Every existing locale gets the new text, so no language keeps showing the old one.
    locales = [locale for locale, _ in translations(old)] if old[:4] == b"mluc" else []
    locales = list(dict.fromkeys(locales)) or [b"enUS"]
    text = value.encode("utf-16-be")
    start = 16 + 12 * len(locales)
    table = struct.pack(">4s4xII", b"mluc", len(locales), 12)
    for locale in locales:
        table += struct.pack(">4sII", locale, len(text), start)
    return table + text


def edit_profile(data, name, copyright_text):
    name = name.strip()
    if not name or "\0" in name or "\0" in copyright_text:
        raise ValueError("Ange ett profilnamn. Texten får inte innehålla nolltecken.")
    tags = profile_tags(data)
    for tag, value in ((b"desc", name), (b"cprt", copyright_text)):
        old = tags.get(tag, b"")
        if data[8] == 4 and tag == b"desc" and old[:4] == b"mluc":
            records = translations(old)
            encoded_name = value.encode("utf-16-be")
            if records and all(text == encoded_name for _, text in records):
                continue
        elif old and value == read_text(old):
            continue
        if data[8] == 4:
            tags[tag] = multilingual_text(old, value)
        elif tag == b"desc":
            ascii_name = value.encode("ascii", errors="replace") + b"\0"
            unicode_name = value.encode("utf-16-be") + b"\0\0"
            tags[tag] = (struct.pack(">4s4xI", b"desc", len(ascii_name)) + ascii_name
                         + struct.pack(">4sI", b"enUS", len(unicode_name) // 2)
                         + unicode_name + bytes(70))
        else:
            try:
                encoded = value.encode("ascii")
            except UnicodeEncodeError as error:
                raise ValueError(
                    f"ICC v2 kräver ASCII i copyright. Byt ut tecknet ”{value[error.start]}” (t.ex. © mot (C))."
                ) from None
            tags[tag] = b"text" + bytes(4) + encoded + b"\0"

    output = bytearray(data[:128])
    output.extend(struct.pack(">I", len(tags)))
    output.extend(bytes(12 * len(tags)))
    offsets = {}
    for index, (tag, block) in enumerate(tags.items()):
        if block not in offsets:
            output.extend(bytes(-len(output) % 4))
            offsets[block] = len(output)
            output.extend(block)
        struct.pack_into(">4sII", output, 132 + 12 * index, tag, offsets[block], len(block))
    output.extend(bytes(-len(output) % 4))
    struct.pack_into(">I", output, 0, len(output))
    # v4 always carries a profile ID; a v2 profile that has one must not keep a stale one.
    if data[8] == 4 or any(data[84:100]):
        digest_input = bytearray(output)
        for start, stop in ((44, 48), (64, 68), (84, 100)):
            digest_input[start:stop] = bytes(stop - start)
        output[84:100] = hashlib.md5(digest_input, usedforsecurity=False).digest()
    return bytes(output)


def write_new(destination, content):
    with open(destination, "xb") as stream:
        try:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        except OSError:
            destination.unlink(missing_ok=True)
            raise


def save_copy(destination, content):
    # Publish a complete file atomically. The link fails if the name already exists.
    umask = os.umask(0)
    os.umask(umask)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(content)
            stream.flush()
            os.fchmod(stream.fileno(), 0o666 & ~umask)  # temporary files default to 0600
            os.fsync(stream.fileno())
            stream.close()
            if temporary.read_bytes() != content:
                raise OSError("Den sparade filen kunde inte verifieras.")
            try:
                os.link(temporary, destination)
            except FileExistsError:
                raise
            except OSError:
                # No hard links here (exFAT, FAT, some network shares): create exclusively.
                write_new(destination, content)
        finally:
            temporary.unlink()


class Editor:
    def __init__(self, root):
        self.root = root
        self.source = None
        self.original = b""
        self.name = tk.StringVar()
        self.source_label = tk.StringVar(value="Ingen profil vald")
        self.status = tk.StringVar()
        root.title("ICC Profile Editor")
        root.minsize(550, 340)
        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(4, weight=1)
        ttk.Label(frame, textvariable=self.source_label, wraplength=435).grid(row=0, column=0, sticky="w")
        ttk.Button(frame, text="Öppna ICC…", command=self.open_profile).grid(row=0, column=1, padx=(10, 0))
        ttk.Label(frame, text="Internt profilnamn").grid(row=1, column=0, sticky="w", pady=(18, 4))
        self.name_entry = ttk.Entry(frame, textvariable=self.name, state="disabled")
        self.name_entry.grid(row=2, column=0, columnspan=2, sticky="ew")
        ttk.Label(frame, text="Copyright").grid(row=3, column=0, sticky="w", pady=(14, 4))
        self.copyright = tk.Text(frame, height=4, width=55, wrap="word", state="disabled")
        self.copyright.grid(row=4, column=0, columnspan=2, sticky="nsew")
        ttk.Label(frame, textvariable=self.status, wraplength=500).grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.save_button = ttk.Button(frame, text="Spara kopia…", command=self.save_profile, state="disabled")
        self.save_button.grid(row=6, column=0, columnspan=2, sticky="e", pady=(12, 0))
        root.bind("<Command-o>", lambda _: self.open_profile())

    def open_profile(self):
        path = filedialog.askopenfilename(parent=self.root, filetypes=[("ICC-profiler", ("*.icc", "*.icm"))])
        if not path:
            return
        try:
            source = Path(path).resolve(strict=True)
            data = source.read_bytes()
            tags = profile_tags(data)
            name = read_text(tags.get(b"desc", b""))
            copyright_text = read_text(tags.get(b"cprt", b""))
        except (OSError, ValueError) as error:
            messagebox.showerror("Kunde inte öppna profilen", str(error), parent=self.root)
            return
        self.source, self.original = source, data
        self.source_label.set(f"{source.name}  •  ICC v{data[8]}")
        self.name_entry.configure(state="normal")
        self.name.set(name)
        self.copyright.configure(state="normal")
        self.copyright.delete("1.0", "end")
        self.copyright.insert("1.0", copyright_text)
        self.save_button.configure(state="normal")
        self.status.set("")
        self.name_entry.focus_set()

    def save_profile(self):
        try:
            name = self.name.get().strip()
            content = edit_profile(self.original, name, self.copyright.get("1.0", "end-1c"))
            stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(". ") or "ICC-profil"
            extension = self.source.suffix
            suggested = self.source.with_name(stem + extension)
            suffix = 1
            while suggested.exists():
                suggested = self.source.with_name(f"{stem}_{suffix}{extension}")
                suffix += 1
            path = filedialog.asksaveasfilename(
                parent=self.root, initialdir=self.source.parent, initialfile=suggested.name,
                defaultextension=extension, filetypes=[("ICC-profiler", ("*.icc", "*.icm"))],
                confirmoverwrite=False,  # existing files are never replaced, so do not offer it
            )
            if not path:
                return
            destination = Path(path)
            if destination.suffix.lower() not in (".icc", ".icm"):
                raise ValueError("Använd filändelsen .icc eller .icm.")
            save_copy(destination, content)
        except FileExistsError:
            messagebox.showerror("Filen finns redan", "Välj ett nytt filnamn för kopian.", parent=self.root)
        except (OSError, ValueError) as error:
            messagebox.showerror("Kunde inte spara profilen", str(error), parent=self.root)
        else:
            self.status.set(f"Sparad som {destination.name}")


def main():
    root = tk.Tk()
    Editor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
