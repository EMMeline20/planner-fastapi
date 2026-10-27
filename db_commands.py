import sqlite3

con = sqlite3.connect("planner.db")
cur = con.cursor()

print("ВСЕ ЗАПИСИ:", cur.execute("SELECT * FROM event").fetchall())

cur.execute(
    "INSERT INTO event (title, image, description, tags, location) "
    "VALUES ('Субботник', 'img.png', 'Весенняя уборка парка', '[\"eco\", \"volunteers\"]', 'Ufa')"
)
con.commit()
print("ДОБАВЛЕНА ЗАПИСЬ, id:", cur.lastrowid)

print("ПОСЛЕ INSERT:", cur.execute("SELECT id, title, location FROM event").fetchall())

cur.execute("UPDATE event SET location = 'Hybrid' WHERE title = 'Субботник'")
con.commit()
print("ОБНОВЛЕНО СТРОК:", cur.rowcount)

cur.execute("DELETE FROM event WHERE title = 'Субботник'")
con.commit()
print("УДАЛЕНО СТРОК:", cur.rowcount)

print("ИТОГ:", cur.execute("SELECT id, title, location FROM event").fetchall())
con.close()