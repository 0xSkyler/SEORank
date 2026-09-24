from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("serp_sentinel")

a = Analysis(
    ["packaging/run_gui.py"],
    pathex=["src"],
    datas=datas,
    hiddenimports=["qasync", "pyqtgraph", "keyring.backends.Windows"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SerpSentinel",
    console=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="SerpSentinel")
