"""Release only the anonymous groups created by the busy demo scenario.

Preserves dossiers and all allocations as an audit trail. Does not touch teachers' dossiers.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'.python-deps')]
from backend.database import initialize,app_db
if __name__=='__main__':
    initialize()
    with app_db() as conn:
        cursor=conn.execute("UPDATE dossiers SET status='released' WHERE owner='demo' AND id LIKE 'demo-busy-%' AND status='confirmed'")
        conn.commit()
        print(f'{cursor.rowcount} groupe(s) fictif(s) libéré(s). Dossiers des enseignants préservés.')
