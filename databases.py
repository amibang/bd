import psycopg2
from psycopg2.extras import RealDictCursor
def get_connection():
    return psycopg2.connect(
        dbname="school books",
        user="postgres",
        password="1",
        host="localhost",
        port="5434"
    )
def get_all_books(search=None):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    if search:
        cursor.execute("""
            SELECT b.book_id, b.book_title, b.author, b.publishing_house, b.publishing_date,
                   c.category_name
            FROM book b
            JOIN book_category c ON b.category = c.category_id
            WHERE b.book_title ILIKE %s OR b.author ILIKE %s OR CAST(b.publishing_date AS TEXT) ILIKE %s
            ORDER BY b.book_id ASC
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("""
            SELECT b.book_id, b.book_title, b.author, b.publishing_house, b.publishing_date,
                   c.category_name
            FROM book b
            JOIN book_category c ON b.category = c.category_id
            ORDER BY book_id ASC
        """)
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    return books
def get_book_by_id(book_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM book WHERE book_id = %s ORDER BY book_id ASC", (book_id,))
    book = cur.fetchone()
    cur.close()
    conn.close()
    return book
def get_book_categories():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT category_id, category_name FROM book_category")
    categories = cur.fetchall()
    cur.close()
    conn.close()
    return [{'category_id': c[0], 'category_name': c[1]} for c in categories]
def get_all_librarians():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT librarian_id, librarian_name FROM librarians")
    results = cursor.fetchall()
    conn.close()
    return results
def get_fine_categories():
    connection = get_connection()
    cursor = connection.cursor()
    query = "SELECT category_id, category_name FROM fine_category;"
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return [{'category_id': row[0], 'category_name': row[1]} for row in rows]
def add_book(title, author, publishing_house, publishing_date, category):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO book (book_title, author, publishing_house, publishing_date, category)
        VALUES (%s, %s, %s, %s, %s)
    """, (title, author, publishing_house, publishing_date, category))
    conn.commit()
    cur.close()
    conn.close()
def update_book(book_id, title, author, publishing_house, publishing_date, category):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE book
        SET book_title=%s, author=%s, publishing_house=%s, publishing_date=%s, category=%s
        WHERE book_id=%s
    """, (title, author, publishing_house, publishing_date, category, book_id))
    conn.commit()
    cur.close()
    conn.close()
def delete_book(book_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM issue_book WHERE book = %s;", (book_id,))
    cur.execute("DELETE FROM book WHERE book_id = %s;", (book_id,))
    conn.commit()
    cur.close()
    conn.close()
def search_books(filters):
    conn = get_connection()
    cur = conn.cursor()
    base_query = """
        SELECT book.book_id, book.book_title, book.author, 
               book.publishing_date, book.publishing_house, 
               book_category.category_name
        FROM book
        LEFT JOIN book_category ON book.category = book_category.category_id
        WHERE TRUE
    """
    params = []
    if filters.get("title"):
        base_query += " AND book.book_title ILIKE %s"
        params.append(f"%{filters['title']}%")
    if filters.get("author"):
        base_query += " AND book.author ILIKE %s"
        params.append(f"%{filters['author']}%")
    if filters.get("year"):
        base_query += " AND book.publishing_date = %s"
        params.append(filters["year"])
    if filters.get("publisher"):
        base_query += " AND book.publishing_house ILIKE %s"
        params.append(f"%{filters['publisher']}%")
    if filters.get("category_id"):
        base_query += " AND book.category = %s"
        params.append(filters["category_id"])
    cur.execute(base_query, tuple(params))
    rows = cur.fetchall()
    books = []
    for row in rows:
        books.append({
            'book_id': row[0],
            'book_title': row[1],
            'author': row[2],
            'publishing_date': row[3],
            'publishing_house': row[4],
            'category_name': row[5]
        })
    cur.close()
    conn.close()
    return books
def add_book_request(book_title, author, publishing_house, publishing_date, category_id, reader_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO book_requests (book_title, author, publishing_house, publishing_date, category_id, reader_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (book_title, author, publishing_house, publishing_date, category_id, reader_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
def get_or_create_reader(reader_name):
    conn = get_connection()
    cursor = conn.cursor()
    # Пытаемся найти читателя
    cursor.execute("SELECT reader_id FROM reader WHERE reader_name = %s", (reader_name,))
    result = cursor.fetchone()
    if result:
        reader_id = result[0]
    else:
        # Если читатель не найден, создаем нового
        cursor.execute("INSERT INTO reader (reader_name, student_or_teacher, reader_phonenumber) VALUES (%s, %s, %s) RETURNING reader_id",
                       (reader_name, 'student', 'не указан'))  # Можно уточнить значения по умолчанию
        reader_id = cursor.fetchone()[0]
        conn.commit()
    cursor.close()
    conn.close()
    return reader_id
# Получить все запросы
def get_all_book_requests():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT br.request_id, br.book_title, br.author, br.publishing_house, br.publishing_date,
               bc.category_name, br.status, r.reader_name, br.request_date
        FROM book_requests br
        JOIN book_category bc ON br.category_id = bc.category_id
        JOIN reader r ON br.reader_id = r.reader_id
        ORDER BY br.request_id ASC
    """)
    requests = cursor.fetchall()
    cursor.close()
    conn.close()
    return requests
def get_book_request_by_id(request_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT * FROM book_requests WHERE request_id = %s
    """, (request_id,))
    request = cursor.fetchone()
    cursor.close()
    conn.close()
    return request
def update_full_book_request(request_id, title, author, pub_house, pub_date, category_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE book_requests
        SET book_title = %s, author = %s, publishing_house = %s, publishing_date = %s,
            category_id = %s, status = %s
        WHERE request_id = %s
    """, (title, author, pub_house, pub_date, category_id, status, request_id))
    conn.commit()
    cursor.close()
    conn.close()
def delete_book_request(request_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM book_requests WHERE request_id = %s", (request_id,))
    conn.commit()
    cursor.close()
    conn.close()

def get_reader_history(reader_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.book_title, b.author, b.publishing_house, b.publishing_date
        FROM issue_book ib
        JOIN book b ON ib.book = b.book_id
        WHERE ib.reader = %s
    """, (reader_id,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def get_request_status_stats():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
        SELECT status, COUNT(*) as count 
        FROM book_requests 
        GROUP BY status
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        # Детальное логирование
        print("\n" + "=" * 50)
        print("DEBUG: Raw status stats from database:")
        for row in rows:
            print(f"Status: '{row[0]}' ({type(row[0])}), Count: {row[1]}")

        # Преобразуем в словарь
        result = {row[0]: row[1] for row in rows}
        print("Resulting dict:", result)
        print("=" * 50 + "\n")

        return result
    finally:
        cursor.close()
        conn.close()

#штрафы
def get_all_fines():
    connection = get_connection()
    cursor = connection.cursor()
    query = """
        SELECT f.fine_id, r.reader_name, l.librarian_name, fc.category_name, f.repayment_date
        FROM fine f
        JOIN reader r ON f.reader = r.reader_id
        JOIN librarians l ON f.librarian = l.librarian_id
        JOIN fine_category fc ON f.category = fc.category_id
        ORDER BY f.fine_id ASC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return [{'fine_id': row[0],
             'reader_name': row[1],
             'librarian_name': row[2],
             'category_name': row[3],
             'repayment_date': row[4]} for row in rows]
def add_fine(reader_id, librarian_id, category_id, repayment_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO fine (reader, librarian, category, repayment_date)
        VALUES (%s, %s, %s, %s);
    """, (reader_id, librarian_id, category_id, repayment_date))
    conn.commit()
    conn.close()
def get_fine_by_id(fine_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM fine WHERE fine_id = %s ORDER BY id_column ASC", (fine_id,))
    fine = cursor.fetchone()
    conn.close()
    return fine
def update_fine(fine_id, reader_id, librarian_id, category_id, repayment_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE fine
        SET reader = %s, librarian = %s, category = %s, repayment_date = %s
        WHERE fine_id = %s;
    """, (reader_id, librarian_id, category_id, repayment_date, fine_id))
    conn.commit()
    conn.close()
def delete_fine(fine_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fine WHERE fine_id = %s;", (fine_id,))
    conn.commit()
    conn.close()
def get_all_fines_with_details():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            fine.fine_id,
            reader.reader_name,
            librarians.librarian_name,
            fine_category.category_name,
            fine.repayment_date
        FROM fine
        JOIN reader ON fine.reader = reader.reader_id
        JOIN librarians ON fine.librarian = librarians.librarian_id
        JOIN fine_category ON fine.category = fine_category.category_id
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            'fine_id': row[0],
            'reader_name': row[1],
            'librarian_name': row[2],
            'category_name': row[3],
            'repayment_date': row[4]
        }
        for row in rows
    ]

#Читатели
def get_all_readers(search=None):
    conn = get_connection()
    cursor = conn.cursor()
    if search:
        cursor.execute("""
            SELECT reader_id, reader_name, student_or_teacher, reader_phonenumber
            FROM reader
            WHERE CAST(reader_id AS TEXT) ILIKE %s OR reader_name ILIKE %s
            ORDER BY reader_id ASC
        """, (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("""
            SELECT reader_id, reader_name, student_or_teacher, reader_phonenumber
            FROM reader
            ORDER BY reader_id ASC
        """)
    results = cursor.fetchall()
    conn.close()
    return [{
        'reader_id': row[0],
        'reader_name': row[1],
        'student_or_teacher': row[2],
        'reader_phonenumber': row[3]
    } for row in results]
def add_reader(name, type_, phone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reader (reader_name, student_or_teacher, reader_phonenumber)
        VALUES (%s, %s, %s);
    """, (name, type_, phone))
    conn.commit()
    conn.close()
def get_reader_by_id(reader_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM reader WHERE reader_id = %s;", (reader_id,))
    reader = cursor.fetchone()
    conn.close()
    return reader
def update_reader(reader_id, name, type_, phone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE reader
        SET reader_name = %s, student_or_teacher = %s, reader_phonenumber = %s
        WHERE reader_id = %s;
    """, (name, type_, phone, reader_id))
    conn.commit()
    conn.close()
def delete_reader(reader_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reader WHERE reader_id = %s;", (reader_id,))
    conn.commit()
    conn.close()


def get_fines_by_category(category_id):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT *
        FROM fine
        JOIN fine_category ON fine.category = fine_category.category_id
        WHERE fine.category = %s
    """
    cursor.execute(query, (category_id,))
    fines = cursor.fetchall()
    # Преобразуем результат в список словарей для удобства
    fines_list = []
    for fine in fines:
        fines_list.append({
            'fine_id': fine[0],
            'reader_name': fine[1],
            'librarian_name': fine[2],
            'category_name': fine[3],
            'repayment_date': fine[4],
            'fine_summ': fine[5],
        })
    cursor.close()
    connection.close()
    return fines_list
def get_fine_sum_by_category(category_id):
    connection = get_connection()
    cursor = connection.cursor()
    query = """
            SELECT fc.fine_summ * sub.count_fines AS total_sum
            FROM fine_category fc
            JOIN (
                SELECT COUNT(*) AS count_fines
                FROM fine
                WHERE category = %s
            ) sub ON TRUE
            WHERE fc.category_id = %s;
        """

    cursor.execute(query, (category_id, category_id))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    # Проверка, что результат существует и не None
    return result[0] if result and result[0] is not None else 0