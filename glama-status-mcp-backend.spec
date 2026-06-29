# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

# Force-include fastmcp.server.context before Analysis resolves deps
os.environ.setdefault("PYINSTALLER_IMPORT_OVERRIDE", "")

a = Analysis(
    ['run_server.py'], pathex=['src'],
    datas=[('src/glama_status_mcp', 'glama_status_mcp')],
    hiddenimports=[
        'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.asyncio',
        'uvicorn.protocols', 'uvicorn.protocols.http',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.lifespan', 'uvicorn.lifespan.on',
        'aiosqlite', 'fastmcp.server.context', 'fastmcp.server.server',
        'mcp.server.lowlevel.server',
    ],
    excludes=['tkinter', 'setuptools', 'pip', 'wheel', 'test', 'tests',
              'unittest', '_distutils_hack'],
    noarchive=True,
)
# Collect ALL fastmcp + pydantic submodules (lazy imports)
a.hiddenimports.extend(collect_submodules('fastmcp'))
a.hiddenimports.extend(collect_submodules('pydantic'))
_keep_dist = ['fastmcp-', 'mcp-', 'prefab_ui-', 'opentelemetry-',
              'email_validator-']
_saved = [e for e in a.datas
          if isinstance(e, tuple)
          and any(k in str(e[0]) for k in _keep_dist)
          and '.dist-info' in str(e[0])]
for _list in [a.datas, a.binaries, a.zipfiles, a.scripts]:
    _list[:] = [e for e in _list
                if not (isinstance(e, tuple)
                and '.dist-info' in str(e[0])
                and not any(k in str(e[0]) for k in _keep_dist))]
a.datas.extend(_saved)
SKIP = ['torch', 'playwright', 'bitsandbytes', 'llvmlite', 'pyarrow',
        'pymupdf', 'grpc', 'numba', 'Cython', 'google', 'azure', 'boto3',
        'botocore', 'matplotlib', 'PIL', 'pandas', 'scipy', 'sklearn',
        'onnxruntime']
a.binaries = [b for b in a.binaries
              if not any(s in b[0].lower() for s in SKIP)]
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    name='glama-status-mcp-backend',
    debug=False, strip=False, upx=False, upx_exclude=[],
    runtime_tmpdir=None, console=False,
)
