from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qasync import QEventLoop, asyncSlot

from .core.browser.backend import PlaywrightBackend
from .core.profiles.manager import ProfileManager
from .core.scheduler import check_keyword

APPDIR = Path.home() / "AppData/Roaming/SerpSentinel"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Serp Sentinel")
        self.resize(1100, 760)

        self._stop_event: asyncio.Event | None = None
        self._backend: PlaywrightBackend | None = None

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.target = QLineEdit("example.com")
        self.keywords = QPlainTextEdit()
        self.keywords.setPlaceholderText("one keyword per line")

        self.profiles = QSpinBox()
        self.profiles.setRange(1, 100)
        self.profiles.setValue(1)

        self.depth = QComboBox()
        self.depth.addItems(["10", "20", "30", "50", "100"])

        self.repeat = QSpinBox()
        self.repeat.setRange(0, 1_000_000)
        self.repeat.setValue(1)
        self.repeat.setSpecialValueText("Until stopped")

        self.delay = QSpinBox()
        self.delay.setRange(1, 3600)
        self.delay.setValue(30)
        self.delay.setSuffix(" s")

        self.browser_mode = QComboBox()
        self.browser_mode.addItem("Background (no browser pop-ups)", True)
        self.browser_mode.addItem("Visible browser (one window per profile)", False)

        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        for label, widget in [
            ("Target", self.target),
            ("Keywords", self.keywords),
            ("Profiles", self.profiles),
            ("Depth", self.depth),
            ("Number of searches (0 = until Stop)", self.repeat),
            ("Delay between searches", self.delay),
            ("Browser mode", self.browser_mode),
        ]:
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

        buttons = QHBoxLayout()
        self.start = QPushButton("Start")
        self.start.clicked.connect(self.run_checks)
        self.stop = QPushButton("Stop")
        self.stop.setEnabled(False)
        self.stop.clicked.connect(self.stop_checks)
        buttons.addWidget(self.start)
        buttons.addWidget(self.stop)
        layout.addLayout(buttons)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        self.tabs.addTab(dashboard, "Dashboard")

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Keyword", "Position", "URL", "Status", "Profile", "Run"]
        )
        self.tabs.addTab(self.table, "Results")

        note = QLabel(
            "Profiles keep one persistent Chrome session. Background mode avoids "
            "browser pop-ups. The app never clicks search results and never "
            "navigates to target sites. If Google presents a block/CAPTCHA, the "
            "run stops rather than attempting to bypass it."
        )
        note.setWordWrap(True)
        self.tabs.addTab(note, "Profiles")

    def stop_checks(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()
        self.status_label.setText("Stopping…")
        self.stop.setEnabled(False)

    async def _sleep_or_stop(self, seconds: int) -> bool:
        if self._stop_event is None:
            return False
        try:
            await asyncio.wait_for(self._stop_event.wait(), timeout=seconds)
            return True
        except TimeoutError:
            return False

    def _append_result(self, result: object, run_number: int) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        values = [
            result.keyword,
            str(result.position or ""),
            result.ranking_url or "",
            result.status,
            result.profile,
            str(run_number),
        ]
        for column, value in enumerate(values):
            self.table.setItem(row, column, QTableWidgetItem(value))

    @asyncSlot()
    async def run_checks(self) -> None:
        keywords = [
            line.strip()
            for line in self.keywords.toPlainText().splitlines()
            if line.strip()
        ]
        profile_count = self.profiles.value()

        if not keywords:
            QMessageBox.information(
                self,
                "No keywords",
                "Add at least one keyword.",
            )
            return

        manager = ProfileManager(APPDIR / "profiles")
        manager.create(profile_count)

        repeat_count = self.repeat.value()
        unlimited = repeat_count == 0
        total_jobs = 0 if unlimited else repeat_count * len(keywords)

        if unlimited:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, max(1, total_jobs))
            self.progress.setValue(0)

        self._stop_event = asyncio.Event()
        self.start.setEnabled(False)
        self.stop.setEnabled(True)
        self.status_label.setText("Running")

        headless = bool(self.browser_mode.currentData())
        self._backend = PlaywrightBackend(headless=headless)

        completed = 0
        run_number = 0
        blocked = False

        try:
            while unlimited or run_number < repeat_count:
                run_number += 1

                for keyword in keywords:
                    if self._stop_event.is_set():
                        break

                    completed += 1
                    profile_number = ((completed - 1) % profile_count) + 1
                    profile = (
                        APPDIR
                        / "profiles"
                        / f"profile_{profile_number:03d}"
                    )

                    result = await check_keyword(
                        self._backend,
                        keyword,
                        self.target.text().strip(),
                        profile,
                        int(self.depth.currentText()),
                        hover=not headless,
                    )
                    self._append_result(result, run_number)

                    if not unlimited:
                        self.progress.setValue(completed)

                    self.status_label.setText(
                        f"Run {run_number} · {keyword} · {result.status}"
                    )

                    if result.status == "blocked":
                        blocked = True
                        self._stop_event.set()
                        QMessageBox.warning(
                            self,
                            "Google blocked this session",
                            "Google returned a CAPTCHA, unusual-traffic page, "
                            "or rate limit. The run has stopped. Serp Sentinel "
                            "does not bypass Google challenges.",
                        )
                        break

                    if self._stop_event.is_set():
                        break

                    if await self._sleep_or_stop(self.delay.value()):
                        break

                if self._stop_event.is_set():
                    break

        except Exception as exc:
            QMessageBox.critical(self, "Run failed", str(exc))
        finally:
            if self._backend is not None:
                await self._backend.close_all()

            self._backend = None
            self.start.setEnabled(True)
            self.stop.setEnabled(False)

            if blocked:
                self.status_label.setText("Blocked by Google")
            elif self._stop_event is not None and self._stop_event.is_set():
                self.status_label.setText("Stopped")
            else:
                self.status_label.setText("Completed")

            if unlimited:
                self.progress.setRange(0, 1)
                self.progress.setValue(0)


def main() -> None:
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
