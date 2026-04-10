import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'

# Keep integration tests deterministic by starting from a clean local DB file.
Path('test.db').unlink(missing_ok=True)
