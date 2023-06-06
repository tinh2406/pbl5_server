import sqlite3
def getIdWithNameAndPhone(name,phone):
        conn = sqlite3.connect('./test.db')
        # cursor = conn.execute("SELECT * from faces")
        cursor = conn.execute(f"SELECT * from faces where phone='{phone}' and name='{name}'")
        id = 0
        for row in cursor:
            id=row[0]
        conn.close()
        return id