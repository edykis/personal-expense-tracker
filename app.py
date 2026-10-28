from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import math
import os
from pathlib import Path
from datetime import date

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'local-demo-only-change-for-deployment')
DB = Path(__file__).with_name('expenses.db')
CATEGORIES = ['Food', 'Transport', 'Shopping', 'Bills', 'Other']

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT NOT NULL, amount REAL NOT NULL CHECK(amount > 0), category TEXT NOT NULL, spent_on TEXT NOT NULL)')

@app.route('/')
def index():
    with connect() as db:
        expenses = db.execute('SELECT * FROM expenses ORDER BY spent_on DESC, id DESC').fetchall()
        total = db.execute('SELECT COALESCE(SUM(amount),0) FROM expenses').fetchone()[0]
    return render_template('index.html', expenses=expenses, total=total, categories=CATEGORIES, today=date.today().isoformat())

@app.post('/add')
def add():
    description = request.form.get('description','').strip()
    category = request.form.get('category','')
    spent_on = request.form.get('spent_on','')
    try:
        amount = round(float(request.form.get('amount','')), 2)
        date.fromisoformat(spent_on)
        if not description or len(description) > 120 or category not in CATEGORIES or not math.isfinite(amount) or amount <= 0 or amount > 1000000:
            raise ValueError
    except (ValueError, OverflowError):
        flash('Please enter valid expense details.')
        return redirect(url_for('index'))
    with connect() as db:
        db.execute('INSERT INTO expenses (description, amount, category, spent_on) VALUES (?,?,?,?)', (description,amount,category,spent_on))
    flash('Expense added.')
    return redirect(url_for('index'))

@app.post('/delete/<int:expense_id>')
def delete(expense_id):
    with connect() as db:
        db.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    flash('Expense deleted.')
    return redirect(url_for('index'))


@app.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
def edit(expense_id):
    with connect() as db:
        expense = db.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,)).fetchone()
    if expense is None:
        flash('Expense not found.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '')
        spent_on = request.form.get('spent_on', '')
        try:
            amount = round(float(request.form.get('amount', '')), 2)
            date.fromisoformat(spent_on)
            if not description or len(description) > 120 or category not in CATEGORIES or not math.isfinite(amount) or amount <= 0 or amount > 1000000:
                raise ValueError
        except (ValueError, OverflowError):
            flash('Please enter valid expense details.')
            return redirect(url_for('edit', expense_id=expense_id))
        with connect() as db:
            db.execute('UPDATE expenses SET description = ?, amount = ?, category = ?, spent_on = ? WHERE id = ?', (description, amount, category, spent_on, expense_id))
        flash('Expense updated.')
        return redirect(url_for('index'))
    return render_template('edit.html', expense=expense, categories=CATEGORIES)

init_db()
if __name__ == '__main__':
    app.run(debug=True)
