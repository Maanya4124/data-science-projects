import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import mysql.connector
import csv


# ---------------- DB CONNECTION ---------------- #
db_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="d2h0w0a5j##",
    database="bms"
)
db_cursor = db_conn.cursor()



#MAIN WINDOW#
bms = tk.Tk()
bms.title("Badminton Management System")
bms.geometry("1200x700")
bms.configure(bg="#05668D")

notebook = ttk.Notebook(bms)
notebook.pack(fill='both', expand=True)


#BADMINTON DATA ANALYSIS TAB#
frame_queries = tk.Frame(notebook, bg="#F0F3BD")
notebook.add(frame_queries, text="Badminton Data Analysis")


query_results = []
user_inputs = []


def equipment_dropdown():
    db_cursor.execute("SELECT DISTINCT equipment_name FROM equipment")
    return [row[0] for row in db_cursor.fetchall()]


queries = {
    "Top N Youngest Players with > X% Win Rate": {
        "sql": """SELECT
                     name,
                     country,
                     birth_date,
                     ROUND(CAST(wins AS FLOAT) / NULLIF(total_matches, 0) * 100, 2) AS win_rate
                  FROM
                     players
                  WHERE
                     total_matches > 0
                     AND (CAST(wins AS FLOAT) / total_matches) * 100 > %s
                  ORDER BY
                     birth_date DESC
                  LIMIT %s;""",
        "parameters": [("Min Win Rate (%)", "float"), ("Top N", "int")]
    },
    "Top Ranked Players": {
        "sql": """SELECT
                    player_id,
                    name,
                    country,
                    ranking,
                    wins,
                    total_matches
                  FROM
                    players
                  ORDER BY
                    ranking ASC
                  LIMIT %s;""",
        "parameters": [("Top N Players", "dropdown")]
    },
    "Equipment Analysis by Type": {
        "sql": """SELECT e.equipment_name, e.brand_name,
                         ROUND(AVG(ps.wins / NULLIF(ps.matches_played, 0)) * 100, 2) AS avg_win_percentage,
                         COUNT(DISTINCT e.player_id) AS users
                  FROM equipment e
                  JOIN player_stats ps ON e.player_id = ps.player_id
                  WHERE ps.matches_played > 0 AND e.equipment_name = %s
                  GROUP BY e.equipment_name, e.brand_name
                  ORDER BY avg_win_percentage DESC""",
        "parameters": [("Equipment Type", "dropdown")]
    },
    "Coach Average Player Win %": {
        "sql": """SELECT
                    c.coach_id,
                    c.name AS coach_name,
                    ROUND(AVG(
                        CAST(p.wins AS FLOAT) / NULLIF(p.total_matches, 0) * 100
                    ), 2) AS avg_player_win_percentage
                  FROM
                    coaches c
                  JOIN
                    players p ON c.coach_id = p.coach_id
                  WHERE
                    p.total_matches > 0
                  GROUP BY
                    c.coach_id, c.name
                  ORDER BY
                    avg_player_win_percentage DESC
                  LIMIT %s;""",
        "parameters": [("Top N Coaches", "int")]
    },
    "Sponsors with Most Tournaments and Total Amount": {
        "sql": """SELECT
                    s.sponsor_name,
                    COUNT(t.tournament_id) AS tournaments_sponsored,
                    SUM(s.sponsorship_amt) AS total_amount_sponsored
                  FROM
                    sponsorship s
                  JOIN
                    tournaments t ON s.sponsorship_id = t.sponsorship_id
                  GROUP BY
                    s.sponsor_name
                  ORDER BY
                    tournaments_sponsored DESC
                  LIMIT %s;""",
        "parameters": [("Top N Sponsors", "int")]
    },
    "Player Stats - Wins, Win Rate, Smash Accuracy": {
        "sql": """SELECT
                    p.player_id,
                    p.name,
                    ps.matches_played,
                    ps.wins,
                    ROUND(CAST(ps.wins AS FLOAT) / NULLIF(ps.matches_played, 0) * 100, 2) AS win_rate,
                    ps.smash_wins,
                    ps.smash_attempts,
                    ROUND(CAST(ps.smash_wins AS FLOAT) / NULLIF(ps.smash_attempts, 0) * 100, 2) AS smash_accuracy
                  FROM
                    players p
                  JOIN
                    player_stats ps ON p.player_id = ps.player_id
                  WHERE
                    ps.matches_played >= %s
                  ORDER BY
                    win_rate DESC;""",
        "parameters": [("Min Matches", "int")]
    },
    "Top Officials by Matches Officiated": {
        "sql": """SELECT
                    o.officials_id,
                    o.name AS official_name,
                    COUNT(mo.match_id) AS matches_officiated
                  FROM
                    Match_Officials mo
                  JOIN
                    Officials o ON mo.officials_id = o.officials_id
                  GROUP BY
                    o.officials_id, o.name
                  ORDER BY
                    matches_officiated DESC;""",
       
    },
    "Country-wise Count in Top 50 Ranked Players": {
        "sql": """SELECT
                    country,
                    COUNT(*) AS num_players
                  FROM (
                      SELECT
                          player_id,
                          name,
                          country,
                          ranking
                      FROM
                          players
                      ORDER BY
                          ranking ASC
                      LIMIT 50
                  ) AS top_players
                  GROUP BY
                      country
                  ORDER BY
                      num_players DESC;""",
        "parameters": []
    }
}


frame_top = tk.Frame(frame_queries, bg="#F0F3BD")
frame_top.pack(pady=10)
frame_parameters = tk.Frame(frame_queries, bg="#F0F3BD")
frame_parameters.pack(pady=5)
frame_buttons = tk.Frame(frame_queries, bg="#F0F3BD")
frame_buttons.pack(pady=5)
frame_result = tk.Frame(frame_queries, bg="#F0F3BD")
frame_result.pack(pady=10, fill="both", expand=True)


query_variable = tk.StringVar()
tk.Label(frame_top, text="Select Query:", bg="#F0F3BD", fg="#05668D", font=("Helvetica", 11, "bold")).pack(side="left")
query_list = ttk.Combobox(frame_top, textvariable=query_variable, state="readonly", width=60)
query_list["values"] = list(queries.keys())
query_list.pack(side="left", padx=10)


query_output = ttk.Treeview(frame_result)
query_output.pack(fill="both", expand=True)
vsb = ttk.Scrollbar(frame_result, orient="vertical", command=query_output.yview)
vsb.pack(side='right', fill='y')
query_output.configure(yscrollcommand=vsb.set)


def show_parameters(event):
    for widget in frame_parameters.winfo_children():
        widget.destroy()
    user_inputs.clear()
    selected_query = query_variable.get()
    if not selected_query:
        return


    for label_text, input_type in queries[selected_query]["parameters"]:
        tk.Label(frame_parameters, text=label_text, bg="#F0F3BD").pack(side="left")
        if selected_query == "Top Ranked Players" and label_text == "Top N Players":
            dropdown_var = tk.StringVar()
            dropdown = ttk.Combobox(frame_parameters, textvariable=dropdown_var, state="readonly")
            dropdown["values"] = [3, 5, 10, 20]
            dropdown.set(5)
            dropdown.pack(side="left", padx=5)
            user_inputs.append((dropdown, "int"))
        elif input_type == "dropdown":
            dropdown_var = tk.StringVar()
            dropdown = ttk.Combobox(frame_parameters, textvariable=dropdown_var, state="readonly")
            dropdown["values"] = equipment_dropdown()
            dropdown.pack(side="left", padx=5)
            user_inputs.append((dropdown, input_type))
        else:
            entry = tk.Entry(frame_parameters)
            entry.pack(side="left", padx=5)
            user_inputs.append((entry, input_type))


query_list.bind("<<ComboboxSelected>>", show_parameters)


def run_query():
    selected_query = query_variable.get()
    if not selected_query:
        messagebox.showwarning("Warning", "Please select a query.")
        return


    sql = queries[selected_query]["sql"]
    inputs = []


    for input_widget, input_type in user_inputs:
        value = input_widget.get()
        if value == "":
            messagebox.showwarning("Missing Input", "All parameters must be filled.")
            return
        inputs.append(int(value) if input_type == "int" else float(value) if input_type == "float" else value)


    try:
        db_cursor.execute(sql, tuple(inputs))
        rows = db_cursor.fetchall()
        col_names = [desc[0] for desc in db_cursor.description]
        query_output.delete(*query_output.get_children())
        query_output["columns"] = col_names
        query_output["show"] = "headings"
        for col in col_names:
            query_output.heading(col, text=col)
            query_output.column(col, anchor="center", width=150)
        for row in rows:
            query_output.insert("", "end", values=row)
        global query_results
        query_results = [col_names] + rows
    except Exception as e:
        messagebox.showerror("Error", str(e))


def export_csv():
    if not query_results:
        messagebox.showwarning("Warning", "Run a query first.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
    if path:
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(query_results)
        messagebox.showinfo("Success", "CSV exported successfully!")


tk.Button(frame_buttons, text="Run Query", command=run_query).pack(side="left", padx=10)
tk.Button(frame_buttons, text="Export CSV", command=export_csv).pack(side="left", padx=10)


#TRANSACTION#
frame_txn = tk.Frame(notebook,bg="#F0F3BD")
notebook.add(frame_txn, text="Register New Match")


tk.Label(frame_txn, text="Match ID").grid(row=0, column=0)
tk.Label(frame_txn, text="Tournament ID").grid(row=1, column=0)
tk.Label(frame_txn, text="Winner ID").grid(row=2, column=0)
tk.Label(frame_txn, text="Loser ID").grid(row=3, column=0)
tk.Label(frame_txn, text="Date (YYYY-MM-DD)").grid(row=4, column=0)
tk.Label(frame_txn, text="Venue").grid(row=5, column=0)
tk.Label(frame_txn, text="Score").grid(row=6, column=0)


match_entry = tk.Entry(frame_txn)
tournament_entry = tk.Entry(frame_txn)
winner_entry = tk.Entry(frame_txn)
loser_entry = tk.Entry(frame_txn)
date_entry = tk.Entry(frame_txn)
venue_entry = tk.Entry(frame_txn)
score_entry = tk.Entry(frame_txn)


match_entry.grid(row=0, column=1)
tournament_entry.grid(row=1, column=1)
winner_entry.grid(row=2, column=1)
loser_entry.grid(row=3, column=1)
date_entry.grid(row=4, column=1)
venue_entry.grid(row=5, column=1)
score_entry.grid(row=6, column=1)


def register_match():
    try:
        db_conn.start_transaction()
        match_id = match_entry.get()
        tournament_id = tournament_entry.get()
        winner_id = winner_entry.get()
        loser_id = loser_entry.get()
        date = date_entry.get()
        venue = venue_entry.get()
        score = score_entry.get()


        db_cursor.execute("""INSERT INTO Matches
                            (match_id, tournament_id, player1_id, player2_id, date, venue, score, winner_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
                          (match_id, tournament_id, winner_id, loser_id, date, venue, score, winner_id))


        db_cursor.execute("UPDATE players SET total_matches = total_matches + 1, wins = wins + 1 WHERE player_id = %s", (winner_id,))
        db_cursor.execute("UPDATE players SET total_matches = total_matches + 1 WHERE player_id = %s", (loser_id,))


        db_conn.commit()
        messagebox.showinfo("Success", "Match registered successfully!")
    except Exception as e:
        db_conn.rollback()
        messagebox.showerror("Error", str(e))


tk.Button(frame_txn, text="Register Match", command=register_match).grid(row=7, column=0, columnspan=2, pady=10)


bms.mainloop()


