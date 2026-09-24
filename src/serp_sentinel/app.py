import sys,asyncio
from pathlib import Path
from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QLabel,QLineEdit,QPlainTextEdit,QSpinBox,QComboBox,QPushButton,QTableWidget,QTableWidgetItem,QTabWidget,QProgressBar,QMessageBox
from qasync import QEventLoop,asyncSlot
from .core.profiles.manager import ProfileManager
from .core.browser.backend import PlaywrightBackend
from .core.scheduler import check_keyword

APPDIR=Path.home()/"AppData/Roaming/SerpSentinel"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serp Sentinel")
        self.resize(1100,720)
        self.tabs=QTabWidget()
        self.setCentralWidget(self.tabs)

        self.target=QLineEdit("example.com")
        self.keywords=QPlainTextEdit()
        self.keywords.setPlaceholderText("one keyword per line")
        self.profiles=QSpinBox()
        self.profiles.setRange(1,100)
        self.profiles.setValue(1)
        self.depth=QComboBox()
        self.depth.addItems(["10","20","30","50","100"])
        self.repeat=QSpinBox()
        self.repeat.setRange(1,100)
        self.repeat.setValue(1)

        dashboard=QWidget()
        lay=QVBoxLayout(dashboard)
        for label,w in [
            ("Target",self.target),
            ("Keywords",self.keywords),
            ("Profiles",self.profiles),
            ("Depth",self.depth),
            ("Number of searches",self.repeat),
        ]:
            lay.addWidget(QLabel(label))
            lay.addWidget(w)
        self.start=QPushButton("Start")
        self.start.clicked.connect(self.run_checks)
        lay.addWidget(self.start)
        self.progress=QProgressBar()
        lay.addWidget(self.progress)
        self.tabs.addTab(dashboard,"Dashboard")

        self.table=QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels(["Keyword","Position","URL","Status","Profile","Run"])
        self.tabs.addTab(self.table,"Results")

        note=QLabel("Profiles are persistent Chrome identities. This build never clicks search results and never navigates to target sites.")
        note.setWordWrap(True)
        self.tabs.addTab(note,"Profiles")

    @asyncSlot()
    async def run_checks(self):
        kws=[x.strip() for x in self.keywords.toPlainText().splitlines() if x.strip()]
        count=self.profiles.value()
        if not kws:
            QMessageBox.information(self,"No keywords","Add at least one keyword.")
            return
        pm=ProfileManager(APPDIR/"profiles")
        pm.create(count)
        jobs=[(k,i) for i in range(self.repeat.value()) for k in kws]
        self.progress.setMaximum(max(1,len(jobs)))
        self.progress.setValue(0)
        self.start.setEnabled(False)
        try:
            backend=PlaywrightBackend()
            for n,(kw,ri) in enumerate(jobs,1):
                profile=APPDIR/"profiles"/f"profile_{((n-1)%count)+1:03d}"
                r=await check_keyword(
                    backend,kw,self.target.text().strip(),profile,
                    int(self.depth.currentText()),hover=True
                )
                row=self.table.rowCount()
                self.table.insertRow(row)
                vals=[kw,str(r.position or ""),r.ranking_url or "",r.status,r.profile,str(ri+1)]
                for c,v in enumerate(vals):
                    self.table.setItem(row,c,QTableWidgetItem(v))
                self.progress.setValue(n)
        except Exception as e:
            QMessageBox.critical(self,"Run failed",str(e))
        finally:
            self.start.setEnabled(True)

def main():
    app=QApplication(sys.argv)
    loop=QEventLoop(app)
    asyncio.set_event_loop(loop)
    w=MainWindow()
    w.show()
    with loop:
        loop.run_forever()

if __name__=="__main__":
    main()
