import os
import shutil
import sqlite3
import glob

folders = [
    'output_final',
    'output_final_boss',
    'output_final_boss_cached',
    'output_test',
    'output_test_cached',
    'run_test_output',
    'test_output',
    'test_run_live',
    'unilog_sample',
    'output'
]

for f in folders:
    if os.path.exists(f):
        shutil.rmtree(f, ignore_errors=True)

for log_file in glob.glob('logs/*.log'):
    try:
        os.remove(log_file)
    except Exception:
        pass

try:
    conn = sqlite3.connect('backend/history.db')
    conn.execute('DELETE FROM runs_history')
    conn.commit()
    conn.close()
except Exception as e:
    print(f"DB reset note: {e}")

print("Workspace cleaned successfully!")
