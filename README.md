[README.txt](https://github.com/user-attachments/files/22974964/README.txt)
Library Management Streamlit App
================================

Files:
- library_streamlit.py   -> Streamlit app (main file)
- library.db             -> SQLite database with sample data (5 books, 2 borrowed records)

How to run locally:
1. Install required packages:
   pip install streamlit pandas

2. Run the app:
   streamlit run library_streamlit.py

Deploy to Streamlit Community Cloud:
1. Create a GitHub repository (e.g., streamlit-library-system).
2. Upload the files from this package (library_streamlit.py and library.db) to the repository root.
3. Go to https://share.streamlit.io and sign in with GitHub.
4. Click "New app", select your repository and branch (main), and set the main file path to:
   library_streamlit.py
5. Deploy. Note: Streamlit Cloud may reset ephemeral files between sessions. For a persistent database,
   consider using a cloud DB (Supabase, PostgreSQL) or re-initialize on startup.

Database notes:
- Sample borrowed records include one overdue record so you can see fine calculation and overdue highlighting.
- Fine policy: R5 per day late (stored in DB for sample record).

If you want me to push these files directly to a GitHub repo for you, I can prepare instructions or a GitHub-ready zip.
