
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS membership_plan (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_name TEXT NOT NULL UNIQUE,
    duration_months INTEGER NOT NULL CHECK(duration_months > 0),
    fee NUMERIC NOT NULL CHECK(fee >= 0),
    benefits TEXT
);

CREATE TABLE IF NOT EXISTS sport (
    sport_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS coach (
    coach_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    specialization TEXT,
    experience_years INTEGER CHECK(experience_years >= 0),
    contact TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS facility (
    facility_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    capacity INTEGER NOT NULL CHECK(capacity > 0),
    type TEXT NOT NULL,
    location TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS equipment (
    equipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity >= 0),
    status TEXT NOT NULL DEFAULT 'Available'
        CHECK(status IN ('Available','Issued','Maintenance')),
    UNIQUE(equipment_name, category)
);

CREATE TABLE IF NOT EXISTS member (
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL UNIQUE,
    join_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active'
        CHECK(status IN ('Active','Inactive','Suspended')),
    plan_id INTEGER NOT NULL,
    FOREIGN KEY(plan_id) REFERENCES membership_plan(plan_id)
);

CREATE TABLE IF NOT EXISTS payment (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    amount NUMERIC NOT NULL CHECK(amount >= 0),
    payment_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Paid'
        CHECK(status IN ('Paid','Pending','Failed','Refunded')),
    FOREIGN KEY(member_id) REFERENCES member(member_id),
    FOREIGN KEY(plan_id) REFERENCES membership_plan(plan_id)
);

CREATE TABLE IF NOT EXISTS equipment_issue (
    issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    equipment_id INTEGER NOT NULL,
    issue_date TEXT NOT NULL,
    return_date TEXT,
    status TEXT NOT NULL DEFAULT 'Issued'
        CHECK(status IN ('Issued','Returned','Overdue')),
    FOREIGN KEY(member_id) REFERENCES member(member_id),
    FOREIGN KEY(equipment_id) REFERENCES equipment(equipment_id),
    CHECK(return_date IS NULL OR return_date >= issue_date)
);

CREATE TABLE IF NOT EXISTS team (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_id INTEGER NOT NULL,
    coach_id INTEGER NOT NULL,
    team_name TEXT NOT NULL UNIQUE,
    founded_year INTEGER,
    status TEXT NOT NULL DEFAULT 'Active'
        CHECK(status IN ('Active','Inactive')),
    FOREIGN KEY(sport_id) REFERENCES sport(sport_id),
    FOREIGN KEY(coach_id) REFERENCES coach(coach_id)
);

CREATE TABLE IF NOT EXISTS training_session (
    training_id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    facility_id INTEGER NOT NULL,
    session_date TEXT NOT NULL,
    session_time TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
    status TEXT NOT NULL DEFAULT 'Scheduled'
        CHECK(status IN ('Scheduled','Completed','Cancelled')),
    FOREIGN KEY(team_id) REFERENCES team(team_id),
    FOREIGN KEY(facility_id) REFERENCES facility(facility_id)
);

CREATE TABLE IF NOT EXISTS tournament (
    tournament_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_id INTEGER NOT NULL,
    name TEXT NOT NULL UNIQUE,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Upcoming'
        CHECK(status IN ('Upcoming','Open','Ongoing','Completed','Cancelled')),
    FOREIGN KEY(sport_id) REFERENCES sport(sport_id),
    CHECK(end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS fixture (
    fixture_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    fixture_date TEXT NOT NULL,
    fixture_time TEXT NOT NULL,
    venue TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Scheduled'
        CHECK(status IN ('Scheduled','Completed','Cancelled')),
    FOREIGN KEY(tournament_id) REFERENCES tournament(tournament_id)
);

CREATE TABLE IF NOT EXISTS participant (
    participant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fixture_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    registration_date TEXT NOT NULL,
    role TEXT DEFAULT 'Team',
    FOREIGN KEY(fixture_id) REFERENCES fixture(fixture_id),
    FOREIGN KEY(team_id) REFERENCES team(team_id),
    UNIQUE(fixture_id,team_id)
);

CREATE TABLE IF NOT EXISTS result (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fixture_id INTEGER NOT NULL UNIQUE,
    winner TEXT,
    score TEXT NOT NULL,
    result_date TEXT NOT NULL,
    FOREIGN KEY(fixture_id) REFERENCES fixture(fixture_id)
);

CREATE INDEX IF NOT EXISTS idx_member_plan ON member(plan_id);
CREATE INDEX IF NOT EXISTS idx_payment_member ON payment(member_id);
CREATE INDEX IF NOT EXISTS idx_training_date ON training_session(session_date);
CREATE INDEX IF NOT EXISTS idx_training_facility_date ON training_session(facility_id,session_date);
CREATE INDEX IF NOT EXISTS idx_fixture_tournament ON fixture(tournament_id);
CREATE INDEX IF NOT EXISTS idx_participant_team ON participant(team_id);

-- Integrity trigger: prevents two active training sessions from overlapping
-- in the same facility on the same date.
CREATE TRIGGER IF NOT EXISTS trg_no_facility_overlap
BEFORE INSERT ON training_session
FOR EACH ROW
WHEN NEW.status <> 'Cancelled'
BEGIN
    SELECT CASE WHEN EXISTS (
        SELECT 1 FROM training_session ts
        WHERE ts.facility_id = NEW.facility_id
          AND ts.session_date = NEW.session_date
          AND ts.status <> 'Cancelled'
          AND time(NEW.session_time) <
              time(ts.session_time, '+' || ts.duration_minutes || ' minutes')
          AND time(ts.session_time) <
              time(NEW.session_time, '+' || NEW.duration_minutes || ' minutes')
    ) THEN RAISE(ABORT, 'Facility schedule overlap is not allowed') END;
END;

-- Similar trigger for team schedule overlap.
CREATE TRIGGER IF NOT EXISTS trg_no_team_overlap
BEFORE INSERT ON training_session
FOR EACH ROW
WHEN NEW.status <> 'Cancelled'
BEGIN
    SELECT CASE WHEN EXISTS (
        SELECT 1 FROM training_session ts
        WHERE ts.team_id = NEW.team_id
          AND ts.session_date = NEW.session_date
          AND ts.status <> 'Cancelled'
          AND time(NEW.session_time) <
              time(ts.session_time, '+' || ts.duration_minutes || ' minutes')
          AND time(ts.session_time) <
              time(NEW.session_time, '+' || NEW.duration_minutes || ' minutes')
    ) THEN RAISE(ABORT, 'Team schedule overlap is not allowed') END;
END;
