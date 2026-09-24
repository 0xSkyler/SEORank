from PyInstaller.utils.hooks import collect_data_files
a=Analysis(['src/serp_sentinel/app.py'],pathex=['.'],datas=collect_data_files('serp_sentinel'),hiddenimports=['qasync','pyqtgraph'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='SerpSentinel',console=False)
coll=COLLECT(exe,a.binaries,a.datas,name='SerpSentinel')
