from flask import Flask, render_template, request, redirect, url_for, session, flash
import databases as db

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# STATUS_TRANSLATIONS = {
#     'pending': 'Рассматривается',
#     'approved': 'Одобрена',
#     'rejected': 'Отклонена'
# }
# #STATUS_INTERNAL = {v: k for k, v in STATUS_DISPLAY.items()}

@app.route('/')
def home():
    return render_template('home.html')
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'nwjns':  # простой пароль для входа
            session['is_admin'] = True
            flash('Вы успешно вошли как администратор')
            return redirect(url_for('home'))
        else:
            flash('Неверный пароль!')
    return render_template('admin_login.html')
@app.route('/admin_logout')
def admin_logout():
    session.pop('is_admin', None)
    flash('Вы вышли из админ-панели')
    return redirect(url_for('home'))

#книги
@app.route('/books', methods=['GET', 'POST'])
def books():
    categories = db.get_book_categories()
    filters = {}
    if request.method == 'POST':
        filters['title'] = request.form.get('title') or None
        filters['author'] = request.form.get('author') or None
        filters['year'] = request.form.get('year') or None
        filters['publisher'] = request.form.get('publisher') or None
        filters['category_id'] = request.form.get('category_id') or None
        books = db.search_books(filters)
    else:
        books = db.get_all_books()
    return render_template('books.html', books=books, categories=categories)
@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        publishing_house = request.form['publishing_house']
        publishing_date = request.form['publishing_date']
        category = request.form['category']
        db.add_book(title, author, publishing_house, publishing_date, category)
        return redirect(url_for('books'))
    categories = db.get_book_categories()
    return render_template('add_book.html', categories=categories)
@app.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        publishing_house = request.form['publishing_house']
        publishing_date = request.form['publishing_date']
        category = request.form['category']
        db.update_book(book_id, title, author, publishing_house, publishing_date, category)
        return redirect(url_for('books'))
    book = db.get_book_by_id(book_id)
    categories = db.get_book_categories()
    return render_template('edit_book.html', book=book, categories=categories)
@app.route('/books/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    db.delete_book(book_id)
    return redirect(url_for('books'))
@app.route('/books/request/<int:book_id>', methods=['POST'])

def request_book(book_id):
    if not session.get('reader_id'):
        flash('Вы должны быть авторизованы как читатель')
        return redirect(url_for('home'))
    reader_id = session.get('reader_id')  # предполагается, что id читателя хранится в сессии
    db.add_book_request(book_id, reader_id)
    flash('Запрос на книгу успешно отправлен')
    return redirect(url_for('books'))
#@app.route('/admin/requests', methods=['GET'])
@app.route('/admin/requests')
def view_book_requests():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    requests = db.get_all_book_requests()
    raw_stats = db.get_request_status_stats()
    STATUS_MAP = {
        'рассматривается': 'Рассматривается',
        'Одобрено': 'Одобрена',
        'Отклонено': 'Отклонена'
    }
    status_stats = {ru_status: 0 for ru_status in STATUS_MAP.values()}
    for db_status, count in raw_stats.items():
        if db_status in STATUS_MAP:
            ru_status = STATUS_MAP[db_status]
            status_stats[ru_status] = count
        else:
            print(f"Warning: Unknown status '{db_status}' with count {count}")
    print("Final status stats:", status_stats)
    return render_template('admin_requests.html',
                           requests=requests,
                           status_stats=status_stats)

@app.route('/admin/requests/edit/<int:request_id>', methods=['GET', 'POST'])
def edit_book_request(request_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))

    request_data = db.get_book_request_by_id(request_id)
    categories = db.get_book_categories()

    if request.method == 'POST':
        book_title = request.form['book_title']
        author = request.form['author']
        publishing_house = request.form['publishing_house']
        publishing_date = request.form['publishing_date']
        category_id = request.form['category_id']
        status = request.form['status']

        db.update_full_book_request(request_id, book_title, author, publishing_house, publishing_date, category_id,
                                    status)
        flash("Запрос обновлен.")
        return redirect(url_for('view_book_requests'))

    return render_template('edit_book_request.html', request=request_data, categories=categories)
@app.route('/admin/requests/delete/<int:request_id>', methods=['POST'])
def delete_book_request(request_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    db.delete_book_request(request_id)
    flash("Запрос удален.")
    return redirect(url_for('view_book_requests'))
@app.route('/add_book_request', methods=['GET', 'POST'])
def add_book_request():
    categories = db.get_book_categories()
    if request.method == 'POST':
        book_title = request.form['book_title']
        author = request.form['author']
        publishing_house = request.form['publishing_house']
        publishing_date = request.form['publishing_date']
        category_id = request.form['category_id']
        reader_name = request.form['reader_name'].strip()
        # Получаем ID читателя или создаем нового
        reader_id = db.get_or_create_reader(reader_name)
        # Сохраняем запрос
        db.add_book_request(book_title, author, publishing_house, publishing_date, category_id, reader_id)
        flash("Запрос успешно отправлен.")
        return redirect(url_for('books'))
    return render_template('add_book_request.html', categories=categories)

@app.route('/reader/history', methods=['GET', 'POST'])
def reader_history():
    history = None
    reader_id = None

    if request.method == 'POST':
        reader_id = request.form.get('reader_id')
        if reader_id:
            try:
                reader_id = int(reader_id)
                history = db.get_reader_history(reader_id)
            except ValueError:
                flash("ID читателя должен быть числом")

    return render_template('reader_history.html', history=history, reader_id=reader_id)

#штрафы
@app.route('/fines', methods=['GET', 'POST'])
def fines():
    fines = db.get_all_fines()
    categories = db.get_fine_categories()
    total_sum = None
    selected_category_name = None
    if request.method == 'POST':
        category_id = request.form.get('sum_category_id')
        if category_id:
            total_sum = db.get_fine_sum_by_category(category_id)
            selected_category = next((c for c in categories if str(c['category_id']) == category_id), None)
            if selected_category:
                selected_category_name = selected_category['category_name']
    return render_template(
        'fines.html',
        fines=fines,
        categories=categories,
        total_sum=total_sum,
        selected_category_name=selected_category_name
    )
@app.route('/add_fine', methods=['GET', 'POST'])
def add_fine():
    categories = db.get_fine_categories()
    if request.method == 'POST':
        reader_id = request.form.get('reader')
        librarian_id = request.form.get('librarian')
        category_id = request.form.get('category')
        repayment_date = request.form.get('repayment_date')
        if reader_id and librarian_id and category_id and repayment_date:
            db.add_fine(reader_id, librarian_id, category_id, repayment_date)
            return redirect(url_for('fines'))
    return render_template('add_fine.html', categories=categories)
@app.route("/fines/edit/<int:fine_id>", methods=["GET", "POST"])
def edit_fine(fine_id):
    if request.method == "POST":
        reader = request.form["reader"]
        librarian = request.form["librarian"]
        category = request.form["category"]
        repayment_date = request.form["repayment_date"]
        db.update_fine(fine_id, reader, librarian, category, repayment_date)
        return redirect(url_for("fines"))
    fine = db.get_fine_by_id(fine_id)
    readers = db.get_all_readers()
    librarians = db.get_all_librarians()
    categories = db.get_fine_categories()
    return render_template("edit_fine.html", fine=fine, readers=readers, librarians=librarians, categories=categories)
@app.route("/fines/delete/<int:fine_id>", methods=["POST"])
def delete_fine(fine_id):
    db.delete_fine(fine_id)
    return redirect(url_for("fines"))

#читатели
@app.route('/readers', methods=['GET', 'POST'])
def readers():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    search = request.form.get('search') if request.method == 'POST' else None
    readers = db.get_all_readers(search)
    return render_template('readers.html', readers=readers, search=search)
@app.route("/readers/add", methods=["GET", "POST"])
def add_reader():
    if request.method == "POST":
        name = request.form["name"]
        type_ = request.form["type"]
        phone = request.form["phone"]
        db.add_reader(name, type_, phone)
        return redirect(url_for("readers"))
    return render_template("add_reader.html")
@app.route("/readers/edit/<int:reader_id>", methods=["GET", "POST"])
def edit_reader(reader_id):
    if request.method == "POST":
        name = request.form["name"]
        type_ = request.form["type"]
        phone = request.form["phone"]
        db.update_reader(reader_id, name, type_, phone)
        return redirect(url_for("readers"))
    reader = db.get_reader_by_id(reader_id)
    return render_template("edit_reader.html", reader=reader)
@app.route("/readers/delete/<int:reader_id>", methods=["POST"])
def delete_reader(reader_id):
    db.delete_reader(reader_id)
    return redirect(url_for("readers"))

if __name__ == '__main__':
    app.run(debug=True)