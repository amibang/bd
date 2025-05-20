from flask import Flask, render_template, request, redirect, url_for
import databases as db

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

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