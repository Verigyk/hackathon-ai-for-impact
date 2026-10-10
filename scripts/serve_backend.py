import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'.python-deps'))
if __name__=='__main__':
    import uvicorn
    uvicorn.run('backend.main:app',host='127.0.0.1',port=8000,log_level='info')
