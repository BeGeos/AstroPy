import sqlite3
from datetime import datetime
import time

"""Routine check for expired keys, security codes or password recovery links in the database.
It directly checks in the database, with the sqlite3 module, however other dbs, such as 
mysql or Postgres etc, require different routines. In this case the check happens every hour

To be activated this routines need to be started separately from the main app"""

conn = sqlite3.connect('../astropy/astropy.db')
cur = conn.cursor()

while True:
    date = datetime.utcnow()
    now = int(date.timestamp())

    # Delete expired AuthKeys
    cur.execute('DELETE FROM auth_keys WHERE expiration_date < ?', (now,))
    # Delete expired security codes
    cur.execute('DELETE FROM security_codes WHERE expiration < ?', (now,))
    # Delete expired recovery codes
    cur.execute('DELETE FROM recovery WHERE exp_date < ?', (now,))
    conn.commit()
    time.sleep(3600)
