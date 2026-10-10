import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for filename in ('.env.local', '.env'):
    path = ROOT / filename
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

SNCF_DB = ROOT / 'data' / 'processed' / 'sncf.sqlite'
APP_DB = ROOT / 'data' / 'processed' / 'app.sqlite'
DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'
TTL_MINUTES = int(os.getenv('OPTION_TTL_MINUTES', '30'))
MIN_CONFIDENCE = max(0,min(100,int(os.getenv('MIN_CONFIDENCE','70'))))
