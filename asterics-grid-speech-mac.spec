# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['speech/start.py'],
    pathex=[],
    binaries=[],
    datas=[('speech/temp', 'temp')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['azure', 'google', 'boto3', 'botocore', 'wit', 'elevenlabs', 'sherpa_onnx'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='asterics-grid-speech-mac',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='asterics-grid-speech-mac.app',
    icon=None,
    bundle_identifier=None,
)
