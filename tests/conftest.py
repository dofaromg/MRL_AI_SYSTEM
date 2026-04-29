"""
Shared pytest fixtures for MRL AI System tests.
"""
import pathlib
import sys

# Make all source directories importable
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _subdir in ("09_workflow", "03_memory/merkle", "03_memory/vector"):
    _p = _REPO_ROOT / _subdir
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
