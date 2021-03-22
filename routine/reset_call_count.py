import sqlite3
from datetime import datetime
import time

"""Routine for resetting the call count for each user and their relative verification
attempts. Since user are given 1000 calls per 24h, every 24h from UTC time, the function
update the calls back to 1000. The same goes for number of attempts, set as 5 originally.
This method might have its flaws but it's simple and coherent, and easy to maintain and 
run in the background. 

To be activated this routines need to be started separately from the main app"""

conn = sqlite3.connect('../astropy/astropy.db')
cur = conn.cursor()

while True:
    date = datetime.utcnow()
    now = int(date.timestamp())

    # Update user base config once every 24h
    cur.execute('UPDATE User SET calls = 1000 WHERE calls < 1000')
    cur.execute('UPDATE User SET attempts = 5 WHERE attempts < 5')
    conn.commit()

    time.sleep(86400)  # 24h check

