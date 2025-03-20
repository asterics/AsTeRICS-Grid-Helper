# -*- mode: python ; coding: utf-8 -*-
import os
import site
from PyInstaller.utils.hooks import collect_dynamic_libs

block_cipher = None

# Get site-packages directory
site_packages = site.getsitepackages()[0]

# Collect Azure Speech SDK dynamic libraries
azure_binaries = collect_dynamic_libs('azure.cognitiveservices.speech')

a = Analysis(
    ['speech/start.py'],
    pathex=[],
    binaries=azure_binaries,  # Add Azure Speech SDK libraries
    datas=[
        ('speech/temp', 'speech/temp'),
        ('speech/cache', 'speech/cache'),
        ('speech/config.py', 'speech'),
        ('speech/speech_manager.py', 'speech'),
        ('speech/__init__.py', 'speech'),
        (os.path.join(site_packages, 'tts_wrapper'), 'tts_wrapper'),  # Include tts_wrapper from site-packages
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'flask_restx',
        'sherpa_onnx',
        'speech.config',
        'speech.speech_manager',
        'azure.cognitiveservices.speech',
        'tts_wrapper',
        'tts_wrapper.engines',
        'tts_wrapper.engines.microsoft',
        'tts_wrapper.engines.sherpaonnx',
    ],
    hookspath=['hooks'],  # Add hooks directory
    hooksconfig={},
    runtime_hooks=['hooks/hook-flask.py'],  # Add runtime hook
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='asterics-grid-speech',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep True for debugging
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='speech/assets/icon.icns' if os.path.exists('speech/assets/icon.icns') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='asterics-grid-speech',
) 