"""Background worker for a single QuietWriter backup."""
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from ..automatic_backups import create_backup

class BackupWorker(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, library, book, destination, parent=None, *, automatic=False):
        super().__init__(parent)
        self.library = library
        self.book = book
        self.destination = Path(destination)
        self.automatic = automatic

    def run(self):
        try:
            result = create_backup(self.library, self.book, self.destination, automatic=self.automatic)
        except Exception as exc:
            self.failed.emit(str(exc) if exc.__class__.__name__ == 'BackupError' else 'De back-up is niet gelukt. Probeer het opnieuw.')
        else:
            self.succeeded.emit(str(result))
