# Copyright (c) 2026 Christer Törnkvist.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Remember successful file dialog locations across app launches."""
import json
from pathlib import Path
from tempfile import NamedTemporaryFile


class DialogLocations:
    def __init__(self, app_name):
        self.file = Path.home() / 'Library' / 'Application Support' / app_name / 'dialog-locations.json'
        self.folders = self.read()

    def read(self):
        try:
            value = json.loads(self.file.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return {}
        return value if isinstance(value, dict) else {}

    def directory(self, key, fallback=None):
        for candidate in (self.folders.get(key), fallback, Path.home() / 'Desktop', Path.home()):
            if candidate and isinstance(candidate, (str, Path)):
                path = Path(candidate)
                try:
                    if path.is_absolute() and path.is_dir():
                        return path
                except (OSError, ValueError):
                    continue
        return Path.home()

    def remember(self, key, filename, *, opened=False):
        folder = str(Path(filename).absolute().parent)
        updates = {key: folder}
        if opened:
            updates['last_input'] = folder
        self.folders.update(updates)
        temporary = None
        try:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.file.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(self.read() | updates, stream)
            temporary.replace(self.file)
        except OSError:
            # Location preferences are optional. The current session still remembers the folder.
            pass
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass

    def save_directory(self):
        return self.directory('save', self.folders.get('last_input'))
