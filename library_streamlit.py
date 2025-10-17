import streamlit as st
import sqlite3
from datetime import date, datetime
import pandas as pd

# Page config and dark theme adjustments
st.set_page_config(page_title="Library Management System", layout="wide")
# Apply some dark theme CSS
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0e1117;
        color: #e6eef8;
    }
    .css-1d391kg {padding-top:0rem;} /* reduce top padding on some Streamlit versions */
    .stButton>button {border-radius:8px;}
    .big-number {font-size:26px; font-weight:700; color:#ffffff;}
    .card {background-color:#111318; padding:12px; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.5);}
    .table-header {background-color:#0b57a4 !important; color: white !important; font-weight:700;}
    </style>
    """,
    unsafe_allow_html=True
)

DB_PATH = "library.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

# Helper functions
def get_available_books(conn):
    c = conn.cursor()
    c.execute("SELECT id, title FROM books WHERE quantity > 0")
    return c.fetchall()

def add_borrow(conn, student, book_id, borrow_date, return_date):
    today = date.today()
    fine = 0
    if return_date < today:
        fine = (today - return_date).days * 5
    c = conn.cursor()
    c.execute("INSERT INTO borrowed_books (student_name, book_id, borrow_date, return_date, fine) VALUES (?, ?, ?, ?, ?)",
              (student, book_id, borrow_date.isoformat(), return_date.isoformat(), float(fine)))
    c.execute("UPDATE books SET quantity = quantity - 1 WHERE id=?", (book_id,))
    conn.commit()

def delete_borrow(conn, record_id):
    c = conn.cursor()
    c.execute("SELECT book_id FROM borrowed_books WHERE id=?", (record_id,))
    row = c.fetchone()
    if not row:
        return False
    book_id = row[0]
    c.execute("DELETE FROM borrowed_books WHERE id=?", (record_id,))
    c.execute("UPDATE books SET quantity = quantity + 1 WHERE id=?", (book_id,))
    conn.commit()
    return True

def fetch_borrowed(conn, search_text=""):
    c = conn.cursor()
    query = """SELECT bb.id, bb.student_name, bk.title, bb.borrow_date, bb.return_date, bb.fine
               FROM borrowed_books bb
               JOIN books bk ON bb.book_id = bk.id
               ORDER BY bb.id DESC"""
    c.execute(query)
    rows = c.fetchall()
    if search_text:
        rows = [r for r in rows if search_text.lower() in r[1].lower() or search_text.lower() in r[2].lower()]
    return rows

def dashboard_stats(conn):
    c = conn.cursor()
    c.execute("SELECT SUM(quantity) FROM books")
    total_available = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM borrowed_books")
    total_borrowed = c.fetchone()[0] or 0
    today = date.today().isoformat()
    c.execute("SELECT COUNT(*) FROM borrowed_books WHERE date(return_date) < date(?)", (today,))
    overdue = c.fetchone()[0] or 0
    c.execute("SELECT SUM(fine) FROM borrowed_books")
    total_fines = c.fetchone()[0] or 0.0
    return total_available, total_borrowed, overdue, total_fines

# --- UI ---
st.title("📚 Library Management System — Dark Mode")
conn = get_connection()

# Dashboard
total_available, total_borrowed, overdue_count, total_fines = dashboard_stats(conn)
col1, col2, col3, col4 = st.columns([1,1,1,1])
col1.markdown("<div class='card'><div class='big-number'>Total Available Books</div><div style='font-size:18px'>"+str(total_available)+"</div></div>", unsafe_allow_html=True)
col2.markdown("<div class='card'><div class='big-number'>Borrowed Records</div><div style='font-size:18px'>"+str(total_borrowed)+"</div></div>", unsafe_allow_html=True)
col3.markdown("<div class='card'><div class='big-number'>Overdue</div><div style='font-size:18px'>"+str(overdue_count)+"</div></div>", unsafe_allow_html=True)
col4.markdown("<div class='card'><div class='big-number'>Total Fines (R)</div><div style='font-size:18px'>R"+f\"{total_fines:.2f}\"+"</div></div>", unsafe_allow_html=True)

st.markdown("---")

# Borrow form and table side-by-side
left, right = st.columns([1,2])

with left:
    st.subheader("Borrow Book Form")
    with st.form("borrow_form"):
        student = st.text_input("Student Name")
        available = get_available_books(conn)
        if available:
            book_map = {title: bid for bid, title in available}
            book_choice = st.selectbox("Select Book", list(book_map.keys()))
        else:
            st.info("No books available to borrow.")
            book_choice = None
            book_map = {}
        borrow_date = st.date_input("Borrow Date", date.today())
        return_date = st.date_input("Return Date", date.today())
        submitted = st.form_submit_button("Add")
        if submitted:
            if not student:
                st.error("Student name is required.")
            elif borrow_date < date.today():
                st.error("Borrow date cannot be in the past.")
            elif return_date < borrow_date:
                st.error("Return date cannot be before borrow date.")
            elif not book_choice:
                st.error("Select a book.")
            else:
                add_borrow(conn, student, book_map[book_choice], borrow_date, return_date)
                st.success(f"'{book_choice}' borrowed for {student}.")
                st.experimental_rerun()

    if st.button("Clear Form"):
        # no direct reset; re-run to clear; display message
        st.experimental_rerun()

with right:
    st.subheader("Borrowed Books")
    search_text = st.text_input("Search by student or book")
    rows = fetch_borrowed(conn, search_text)
    st.write(f"Total Records: {len(rows)}")
    if rows:
        df = pd.DataFrame(rows, columns=["ID", "Student", "Book", "Borrow Date", "Return Date", "Fine"])
        # format dates and fine
        df["Borrow Date"] = pd.to_datetime(df["Borrow Date"]).dt.date
        df["Return Date"] = pd.to_datetime(df["Return Date"]).dt.date
        df["Fine"] = df["Fine"].apply(lambda x: f"R{float(x):.2f}")
        # highlight overdue rows
        def highlight_overdue(r):
            try:
                ret = r["Return Date"]
                if ret < date.today():
                    return ['background-color: #8b1a1a; color: white' for _ in r]
                else:
                    return ['' for _ in r]
            except Exception:
                return ['' for _ in r]
        st.dataframe(df.style.apply(highlight_overdue, axis=1).set_table_styles(
            [{'selector':'th', 'props':[('background-color','#0b57a4'), ('color','white'), ('font-weight','700')]}]
        ), height=350)
    else:
        st.info("No records to show.")

    st.markdown("### Delete a record")
    record_id = st.number_input("Record ID to delete", min_value=0, step=1)
    if st.button("Delete"):
        if record_id <= 0:
            st.error("Enter a valid record ID (>0).")
        else:
            ok = delete_borrow(conn, int(record_id))
            if ok:
                st.success(f"Record {record_id} deleted.")
                st.experimental_rerun()
            else:
                st.error("Record ID not found.")

conn.close()
