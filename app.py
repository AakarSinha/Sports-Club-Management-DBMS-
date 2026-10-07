
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from pathlib import Path

BASE=Path(__file__).resolve().parent
DB=BASE/"sports_club.db"
SCHEMA=BASE/"schema.sql"

app=Flask(__name__)
app.secret_key="sports-club-demo-key"

TABLES=["membership_plan","member","payment","equipment","equipment_issue","sport","coach",
        "team","facility","training_session","tournament","fixture","participant","result"]

def get_db():
    con=sqlite3.connect(DB)
    con.row_factory=sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def one_id(con, table, col, value):
    row=con.execute(f"SELECT * FROM {table} WHERE {col}=?", (value,)).fetchone()
    return row["id"] if row and "id" in row.keys() else (row[table+"_id"] if row else None)

def ensure_seed(con):
    # Master data: INSERT OR IGNORE means this is safe even after user additions.
    con.executemany("""INSERT OR IGNORE INTO membership_plan
        (plan_name,duration_months,fee,benefits) VALUES (?,?,?,?)""",[
        ("Standard",6,6000,"Gym and basic sports facilities"),
        ("Premium",12,10000,"All facilities, training access and tournament eligibility"),
        ("Student",6,4500,"Student access to selected facilities")])
    con.executemany("""INSERT OR IGNORE INTO sport(sport_name,description) VALUES(?,?)""",[
        ("Football","Outdoor team sport"),("Basketball","Indoor court team sport"),
        ("Badminton","Indoor racket sport"),("Cricket","Outdoor bat and ball sport")])
    con.executemany("""INSERT OR IGNORE INTO coach(name,specialization,experience_years,contact)
        VALUES(?,?,?,?)""",[
        ("Arjun Kumar","Football",6,"9000000001"),("Neha Singh","Basketball",5,"9000000002"),
        ("Vikram Rao","Badminton",7,"9000000003"),("Rahul Sharma","Cricket",8,"9000000004")])
    con.executemany("""INSERT OR IGNORE INTO facility(name,capacity,type,location)
        VALUES(?,?,?,?)""",[
        ("Main Football Ground",200,"Ground","North Campus"),
        ("Indoor Court 1",60,"Court","Sports Block"),
        ("Badminton Hall",40,"Hall","Sports Block"),
        ("Cricket Ground",250,"Ground","East Campus")])
    con.executemany("""INSERT OR IGNORE INTO equipment(equipment_name,category,quantity,status)
        VALUES(?,?,?,?)""",[
        ("Football","Ball",20,"Available"),("Basketball","Ball",15,"Available"),
        ("Badminton Racket","Racket",30,"Available"),("Cricket Bat","Bat",12,"Available")])

    plans={r["plan_name"]:r["plan_id"] for r in con.execute("SELECT plan_id,plan_name FROM membership_plan")}
    sports={r["sport_name"]:r["sport_id"] for r in con.execute("SELECT sport_id,sport_name FROM sport")}
    coaches={r["name"]:r["coach_id"] for r in con.execute("SELECT coach_id,name FROM coach")}
    facilities={r["name"]:r["facility_id"] for r in con.execute("SELECT facility_id,name FROM facility")}

    con.executemany("""INSERT OR IGNORE INTO member
        (first_name,last_name,email,phone,join_date,status,plan_id) VALUES(?,?,?,?,?,?,?)""",[
        ("Aarav","Mehta","aarav@example.com","9100000001","2026-01-12","Active",plans["Premium"]),
        ("Riya","Shah","riya@example.com","9100000002","2026-02-03","Active",plans["Standard"]),
        ("Kabir","Rao","kabir@example.com","9100000003","2025-09-18","Inactive",plans["Premium"]),
        ("Ananya","Verma","ananya@example.com","9100000004","2026-03-14","Active",plans["Student"]),
        ("Dev","Patel","dev@example.com","9100000005","2026-04-01","Active",plans["Premium"])])

    members={r["email"]:r["member_id"] for r in con.execute("SELECT member_id,email FROM member")}
    con.executemany("""INSERT OR IGNORE INTO payment(member_id,plan_id,amount,payment_date,status)
        VALUES(?,?,?,?,?)""",[
        (members["aarav@example.com"],plans["Premium"],10000,"2026-01-12","Paid"),
        (members["riya@example.com"],plans["Standard"],6000,"2026-02-03","Paid"),
        (members["kabir@example.com"],plans["Premium"],10000,"2025-09-18","Paid"),
        (members["ananya@example.com"],plans["Student"],4500,"2026-03-14","Paid"),
        (members["dev@example.com"],plans["Premium"],10000,"2026-04-01","Paid")])

    con.executemany("""INSERT OR IGNORE INTO team
        (sport_id,coach_id,team_name,founded_year,status) VALUES(?,?,?,?,?)""",[
        (sports["Football"],coaches["Arjun Kumar"],"Woxsen Strikers",2022,"Active"),
        (sports["Basketball"],coaches["Neha Singh"],"Campus Hoopers",2023,"Active"),
        (sports["Badminton"],coaches["Vikram Rao"],"Smash Squad",2024,"Active"),
        (sports["Cricket"],coaches["Rahul Sharma"],"Woxsen Cricket XI",2021,"Active")])
    teams={r["team_name"]:r["team_id"] for r in con.execute("SELECT team_id,team_name FROM team")}
    # Seed training rows one-by-one. The database has an overlap trigger, and
    # INSERT OR IGNORE cannot suppress a trigger's RAISE(ABORT). If a previous
    # run already created an overlapping session, keep it and skip that seed row.
    training_seed=[
        (teams["Woxsen Strikers"],facilities["Main Football Ground"],"2026-10-06","17:00",90,"Scheduled"),
        (teams["Campus Hoopers"],facilities["Indoor Court 1"],"2026-10-07","18:00",90,"Scheduled"),
        (teams["Smash Squad"],facilities["Badminton Hall"],"2026-10-08","16:00",60,"Scheduled"),
        (teams["Woxsen Cricket XI"],facilities["Cricket Ground"],"2026-10-09","17:30",120,"Scheduled")]
    for row in training_seed:
        try:
            con.execute("""INSERT OR IGNORE INTO training_session
                (team_id,facility_id,session_date,session_time,duration_minutes,status)
                VALUES(?,?,?,?,?,?)""", row)
        except sqlite3.IntegrityError:
            # Existing schedule is valid; do not prevent the application from starting.
            con.rollback()

    con.executemany("""INSERT OR IGNORE INTO tournament
        (sport_id,name,start_date,end_date,status) VALUES(?,?,?,?,?)""",[
        (sports["Football"],"Inter-College Football Cup","2026-10-12","2026-10-15","Open"),
        (sports["Basketball"],"Campus Basketball League","2026-11-02","2026-11-08","Upcoming"),
        (sports["Badminton"],"Badminton Open","2026-11-20","2026-11-22","Upcoming")])
    tournaments={r["name"]:r["tournament_id"] for r in con.execute("SELECT tournament_id,name FROM tournament")}
    con.executemany("""INSERT OR IGNORE INTO fixture
        (tournament_id,fixture_date,fixture_time,venue,status) VALUES(?,?,?,?,?)""",[
        (tournaments["Inter-College Football Cup"],"2026-10-12","17:00","Main Football Ground","Scheduled"),
        (tournaments["Inter-College Football Cup"],"2026-10-13","17:00","Main Football Ground","Scheduled"),
        (tournaments["Campus Basketball League"],"2026-11-02","18:00","Indoor Court 1","Scheduled")])
    fixtures={r["fixture_id"]:r["fixture_id"] for r in con.execute("SELECT fixture_id FROM fixture")}
    # add participants only if absent
    f1=con.execute("""SELECT fixture_id FROM fixture WHERE tournament_id=? ORDER BY fixture_id LIMIT 1""",
                   (tournaments["Inter-College Football Cup"],)).fetchone()
    f2=con.execute("""SELECT fixture_id FROM fixture WHERE tournament_id=? ORDER BY fixture_id LIMIT 1 OFFSET 1""",
                   (tournaments["Inter-College Football Cup"],)).fetchone()
    f3=con.execute("""SELECT fixture_id FROM fixture WHERE tournament_id=? ORDER BY fixture_id LIMIT 1""",
                   (tournaments["Campus Basketball League"],)).fetchone()
    if f1 and f2 and f3:
        con.executemany("""INSERT OR IGNORE INTO participant
            (fixture_id,team_id,registration_date,role) VALUES(?,?,?,?)""",[
            (f1["fixture_id"],teams["Woxsen Strikers"],"2026-10-01","Team"),
            (f1["fixture_id"],teams["Woxsen Cricket XI"],"2026-10-01","Team"),
            (f2["fixture_id"],teams["Woxsen Strikers"],"2026-10-01","Team"),
            (f2["fixture_id"],teams["Woxsen Cricket XI"],"2026-10-01","Team"),
            (f3["fixture_id"],teams["Campus Hoopers"],"2026-10-01","Team")])
    con.commit()

def init_db():
    con=get_db()
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    ensure_seed(con)
    con.close()

@app.route("/")
def dashboard():
    con=get_db()
    counts={k:con.execute(q).fetchone()[0] for k,q in {
        "members":"SELECT COUNT(*) FROM member","teams":"SELECT COUNT(*) FROM team",
        "tournaments":"SELECT COUNT(*) FROM tournament","facilities":"SELECT COUNT(*) FROM facility",
        "sessions":"SELECT COUNT(*) FROM training_session"}.items()}
    upcoming=con.execute("""SELECT t.name,s.sport_name,t.start_date,t.status
        FROM tournament t JOIN sport s ON s.sport_id=t.sport_id ORDER BY t.start_date LIMIT 5""").fetchall()
    con.close()
    return render_template("dashboard.html",counts=counts,upcoming=upcoming)

@app.route("/members")
def members():
    q=request.args.get("q","").strip()
    con=get_db()
    rows=con.execute("""SELECT m.*,p.plan_name FROM member m JOIN membership_plan p ON p.plan_id=m.plan_id
        WHERE (?='' OR m.first_name LIKE ? OR m.last_name LIKE ? OR m.email LIKE ?)
        ORDER BY m.member_id DESC""",(q,f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
    plans=con.execute("SELECT * FROM membership_plan ORDER BY plan_name").fetchall()
    con.close()
    return render_template("members.html",members=rows,plans=plans,q=q)

@app.route("/members/add",methods=["POST"])
def add_member():
    data=[request.form.get(x,"").strip() for x in ["first_name","last_name","email","phone","join_date","status","plan_id"]]
    try:
        con=get_db(); con.execute("""INSERT INTO member(first_name,last_name,email,phone,join_date,status,plan_id)
            VALUES(?,?,?,?,?,?,?)""",data); con.commit(); con.close(); flash("Member added successfully.","success")
    except sqlite3.IntegrityError as e: flash("Could not add member: "+str(e),"error")
    return redirect(url_for("members"))

@app.route("/members/edit/<int:member_id>",methods=["GET","POST"])
def edit_member(member_id):
    con=get_db()
    if request.method=="POST":
        data=[request.form.get(x,"").strip() for x in ["first_name","last_name","email","phone","join_date","status","plan_id"]]
        try:
            con.execute("""UPDATE member SET first_name=?,last_name=?,email=?,phone=?,join_date=?,status=?,plan_id=? WHERE member_id=?""",
                        data+[member_id]); con.commit(); flash("Member updated.","success")
        except sqlite3.IntegrityError as e: flash("Update failed: "+str(e),"error")
        con.close(); return redirect(url_for("members"))
    row=con.execute("SELECT * FROM member WHERE member_id=?",(member_id,)).fetchone()
    plans=con.execute("SELECT * FROM membership_plan ORDER BY plan_name").fetchall()
    con.close(); return render_template("edit_member.html",member=row,plans=plans)

@app.route("/members/delete/<int:member_id>",methods=["POST"])
def delete_member(member_id):
    try:
        con=get_db(); con.execute("DELETE FROM member WHERE member_id=?",(member_id,)); con.commit(); con.close(); flash("Member deleted.","success")
    except sqlite3.IntegrityError as e: flash("Cannot delete member: "+str(e),"error")
    return redirect(url_for("members"))

@app.route("/teams")
def teams():
    con=get_db()
    rows=con.execute("""SELECT t.*,s.sport_name,c.name coach_name FROM team t
        JOIN sport s ON s.sport_id=t.sport_id JOIN coach c ON c.coach_id=t.coach_id ORDER BY t.team_id""").fetchall()
    sessions=con.execute("""SELECT ts.*,t.team_name,f.name facility_name FROM training_session ts
        JOIN team t ON t.team_id=ts.team_id JOIN facility f ON f.facility_id=ts.facility_id
        ORDER BY ts.session_date,ts.session_time""").fetchall()
    sports=con.execute("SELECT * FROM sport ORDER BY sport_name").fetchall()
    coaches=con.execute("SELECT * FROM coach ORDER BY name").fetchall()
    facilities=con.execute("SELECT * FROM facility ORDER BY name").fetchall()
    con.close()
    return render_template("teams.html",teams=rows,sessions=sessions,sports=sports,coaches=coaches,facilities=facilities)

@app.route("/teams/add",methods=["POST"])
def add_team():
    try:
        con=get_db(); con.execute("""INSERT INTO team(sport_id,coach_id,team_name,founded_year,status) VALUES(?,?,?,?,?)""",
            [request.form.get("sport_id"),request.form.get("coach_id"),request.form.get("team_name").strip(),
             request.form.get("founded_year") or None,request.form.get("status","Active")])
        con.commit(); con.close(); flash("Team added.","success")
    except sqlite3.IntegrityError as e: flash("Could not add team: "+str(e),"error")
    return redirect(url_for("teams"))

@app.route("/teams/delete/<int:team_id>",methods=["POST"])
def delete_team(team_id):
    try:
        con=get_db(); con.execute("DELETE FROM team WHERE team_id=?",(team_id,)); con.commit(); con.close(); flash("Team deleted.","success")
    except sqlite3.IntegrityError as e: flash("Cannot delete team: "+str(e),"error")
    return redirect(url_for("teams"))

@app.route("/training/add",methods=["POST"])
def add_training():
    try:
        con=get_db(); con.execute("""INSERT INTO training_session
            (team_id,facility_id,session_date,session_time,duration_minutes,status) VALUES(?,?,?,?,?,?)""",
            [request.form.get("team_id"),request.form.get("facility_id"),request.form.get("session_date"),
             request.form.get("session_time"),request.form.get("duration_minutes"),request.form.get("status","Scheduled")])
        con.commit(); con.close(); flash("Training session added.","success")
    except sqlite3.IntegrityError as e: flash("Could not add session: "+str(e),"error")
    return redirect(url_for("teams"))

@app.route("/training/delete/<int:training_id>",methods=["POST"])
def delete_training(training_id):
    con=get_db(); con.execute("DELETE FROM training_session WHERE training_id=?",(training_id,)); con.commit(); con.close()
    flash("Training session deleted.","success"); return redirect(url_for("teams"))

@app.route("/tournaments")
def tournaments():
    con=get_db()
    rows=con.execute("""SELECT t.*,s.sport_name FROM tournament t JOIN sport s ON s.sport_id=t.sport_id ORDER BY t.start_date""").fetchall()
    fixtures=con.execute("""SELECT f.*,t.name tournament_name FROM fixture f JOIN tournament t ON t.tournament_id=f.tournament_id
        ORDER BY f.fixture_date,f.fixture_time""").fetchall()
    sports=con.execute("SELECT * FROM sport ORDER BY sport_name").fetchall()
    con.close(); return render_template("tournaments.html",tournaments=rows,fixtures=fixtures,sports=sports)

@app.route("/tournaments/add",methods=["POST"])
def add_tournament():
    try:
        con=get_db(); con.execute("""INSERT INTO tournament(sport_id,name,start_date,end_date,status) VALUES(?,?,?,?,?)""",
            [request.form.get("sport_id"),request.form.get("name").strip(),request.form.get("start_date"),
             request.form.get("end_date"),request.form.get("status","Upcoming")])
        con.commit(); con.close(); flash("Tournament added.","success")
    except sqlite3.IntegrityError as e: flash("Could not add tournament: "+str(e),"error")
    return redirect(url_for("tournaments"))

@app.route("/tournaments/delete/<int:tournament_id>",methods=["POST"])
def delete_tournament(tournament_id):
    try:
        con=get_db(); con.execute("DELETE FROM tournament WHERE tournament_id=?",(tournament_id,)); con.commit(); con.close(); flash("Tournament deleted.","success")
    except sqlite3.IntegrityError as e: flash("Cannot delete tournament: "+str(e),"error")
    return redirect(url_for("tournaments"))

@app.route("/fixtures/add",methods=["POST"])
def add_fixture():
    try:
        con=get_db(); con.execute("""INSERT INTO fixture(tournament_id,fixture_date,fixture_time,venue,status) VALUES(?,?,?,?,?)""",
            [request.form.get("tournament_id"),request.form.get("fixture_date"),request.form.get("fixture_time"),
             request.form.get("venue").strip(),request.form.get("status","Scheduled")])
        con.commit(); con.close(); flash("Fixture added.","success")
    except sqlite3.IntegrityError as e: flash("Could not add fixture: "+str(e),"error")
    return redirect(url_for("tournaments"))

@app.route("/facilities")
def facilities():
    con=get_db()
    rows=con.execute("""SELECT f.*,COUNT(ts.training_id) sessions FROM facility f LEFT JOIN training_session ts
        ON ts.facility_id=f.facility_id GROUP BY f.facility_id ORDER BY f.name""").fetchall()
    con.close(); return render_template("facilities.html",facilities=rows)

@app.route("/facilities/add",methods=["POST"])
def add_facility():
    try:
        con=get_db(); con.execute("""INSERT INTO facility(name,capacity,type,location) VALUES(?,?,?,?)""",
            [request.form.get("name").strip(),request.form.get("capacity"),request.form.get("type").strip(),request.form.get("location").strip()])
        con.commit(); con.close(); flash("Facility added.","success")
    except sqlite3.IntegrityError as e: flash("Could not add facility: "+str(e),"error")
    return redirect(url_for("facilities"))

@app.route("/facilities/delete/<int:facility_id>",methods=["POST"])
def delete_facility(facility_id):
    try:
        con=get_db(); con.execute("DELETE FROM facility WHERE facility_id=?",(facility_id,)); con.commit(); con.close(); flash("Facility deleted.","success")
    except sqlite3.IntegrityError as e: flash("Cannot delete facility: "+str(e),"error")
    return redirect(url_for("facilities"))

@app.route("/schema")
def schema():
    con=get_db(); tables=[]
    for t in TABLES:
        cols=con.execute(f"PRAGMA table_info({t})").fetchall()
        fks=con.execute(f"PRAGMA foreign_key_list({t})").fetchall()
        tables.append({"name":t,"columns":cols,"fks":fks})
    con.close(); return render_template("schema.html",tables=tables)

@app.route("/reports")
def reports():
    con=get_db()
    active=con.execute("""SELECT p.plan_name,COUNT(m.member_id) n FROM membership_plan p LEFT JOIN member m
        ON m.plan_id=p.plan_id AND m.status='Active' GROUP BY p.plan_id,p.plan_name""").fetchall()
    payments=con.execute("""SELECT p.plan_name,SUM(pay.amount) total FROM membership_plan p LEFT JOIN payment pay
        ON pay.plan_id=p.plan_id GROUP BY p.plan_id,p.plan_name""").fetchall()
    con.close(); return render_template("reports.html",active=active,payments=payments)

@app.route("/queries")
def queries():
    con=get_db()
    defs=[
    ("Q1","Active members with plans","SELECT m.member_id,m.first_name||' '||COALESCE(m.last_name,'') member_name,p.plan_name,m.status FROM member m JOIN membership_plan p ON p.plan_id=m.plan_id WHERE m.status='Active';"),
    ("Q2","Teams with sport and coach","SELECT t.team_name,s.sport_name,c.name coach FROM team t JOIN sport s ON s.sport_id=t.sport_id JOIN coach c ON c.coach_id=t.coach_id ORDER BY t.team_name;"),
    ("Q3","Training schedule with facility","SELECT ts.session_date,ts.session_time,t.team_name,f.name facility,ts.duration_minutes FROM training_session ts JOIN team t ON t.team_id=ts.team_id JOIN facility f ON f.facility_id=ts.facility_id ORDER BY ts.session_date;"),
    ("Q4","Upcoming tournaments","SELECT t.name,s.sport_name,t.start_date,t.end_date,t.status FROM tournament t JOIN sport s ON s.sport_id=t.sport_id WHERE t.status IN ('Open','Upcoming') ORDER BY t.start_date;"),
    ("Q5","Payment totals by plan","SELECT p.plan_name,COALESCE(SUM(pay.amount),0) total_collected FROM membership_plan p LEFT JOIN payment pay ON pay.plan_id=p.plan_id GROUP BY p.plan_id,p.plan_name;")]
    result=[]
    for code,title,sql in defs: result.append({"code":code,"title":title,"sql":sql,"rows":con.execute(sql).fetchall()})
    con.close(); return render_template("queries.html",query_rows=result)

@app.route("/api/health")
def health(): return jsonify({"status":"ok","database":DB.name})

if __name__=="__main__":
    init_db()
    app.run(debug=True)
