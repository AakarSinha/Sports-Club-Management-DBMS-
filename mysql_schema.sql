
-- MySQL 8+ logical design version.
-- Run this in MySQL Workbench / MySQL Shell.
DROP DATABASE IF EXISTS sports_club_db;
CREATE DATABASE sports_club_db;
USE sports_club_db;

CREATE TABLE membership_plan (
 plan_id INT AUTO_INCREMENT PRIMARY KEY,
 plan_name VARCHAR(80) NOT NULL UNIQUE,
 duration_months INT NOT NULL CHECK(duration_months>0),
 fee DECIMAL(10,2) NOT NULL CHECK(fee>=0),
 benefits VARCHAR(500)
);

CREATE TABLE sport (
 sport_id INT AUTO_INCREMENT PRIMARY KEY,
 sport_name VARCHAR(80) NOT NULL UNIQUE,
 description VARCHAR(500)
);

CREATE TABLE coach (
 coach_id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(120) NOT NULL,
 specialization VARCHAR(120),
 experience_years INT CHECK(experience_years>=0),
 contact VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE facility (
 facility_id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(120) NOT NULL UNIQUE,
 capacity INT NOT NULL CHECK(capacity>0),
 type VARCHAR(60) NOT NULL,
 location VARCHAR(150) NOT NULL
);

CREATE TABLE equipment (
 equipment_id INT AUTO_INCREMENT PRIMARY KEY,
 equipment_name VARCHAR(120) NOT NULL,
 category VARCHAR(80) NOT NULL,
 quantity INT NOT NULL CHECK(quantity>=0),
 status VARCHAR(30) NOT NULL DEFAULT 'Available',
 UNIQUE(equipment_name,category)
);

CREATE TABLE member (
 member_id INT AUTO_INCREMENT PRIMARY KEY,
 first_name VARCHAR(60) NOT NULL,
 last_name VARCHAR(60),
 email VARCHAR(150) NOT NULL UNIQUE,
 phone VARCHAR(30) NOT NULL UNIQUE,
 join_date DATE NOT NULL,
 status VARCHAR(20) NOT NULL DEFAULT 'Active',
 plan_id INT NOT NULL,
 FOREIGN KEY(plan_id) REFERENCES membership_plan(plan_id),
 CHECK(status IN ('Active','Inactive','Suspended'))
);

CREATE TABLE payment (
 payment_id INT AUTO_INCREMENT PRIMARY KEY,
 member_id INT NOT NULL,
 plan_id INT NOT NULL,
 amount DECIMAL(10,2) NOT NULL CHECK(amount>=0),
 payment_date DATE NOT NULL,
 status VARCHAR(20) NOT NULL DEFAULT 'Paid',
 FOREIGN KEY(member_id) REFERENCES member(member_id),
 FOREIGN KEY(plan_id) REFERENCES membership_plan(plan_id),
 CHECK(status IN ('Paid','Pending','Failed','Refunded'))
);

CREATE TABLE equipment_issue (
 issue_id INT AUTO_INCREMENT PRIMARY KEY,
 member_id INT NOT NULL,
 equipment_id INT NOT NULL,
 issue_date DATE NOT NULL,
 return_date DATE,
 status VARCHAR(20) NOT NULL DEFAULT 'Issued',
 FOREIGN KEY(member_id) REFERENCES member(member_id),
 FOREIGN KEY(equipment_id) REFERENCES equipment(equipment_id),
 CHECK(return_date IS NULL OR return_date>=issue_date),
 CHECK(status IN ('Issued','Returned','Overdue'))
);

CREATE TABLE team (
 team_id INT AUTO_INCREMENT PRIMARY KEY,
 sport_id INT NOT NULL,
 coach_id INT NOT NULL,
 team_name VARCHAR(120) NOT NULL UNIQUE,
 founded_year YEAR,
 status VARCHAR(20) NOT NULL DEFAULT 'Active',
 FOREIGN KEY(sport_id) REFERENCES sport(sport_id),
 FOREIGN KEY(coach_id) REFERENCES coach(coach_id),
 CHECK(status IN ('Active','Inactive'))
);

CREATE TABLE training_session (
 training_id INT AUTO_INCREMENT PRIMARY KEY,
 team_id INT NOT NULL,
 facility_id INT NOT NULL,
 session_date DATE NOT NULL,
 session_time TIME NOT NULL,
 duration_minutes INT NOT NULL CHECK(duration_minutes>0),
 status VARCHAR(20) NOT NULL DEFAULT 'Scheduled',
 FOREIGN KEY(team_id) REFERENCES team(team_id),
 FOREIGN KEY(facility_id) REFERENCES facility(facility_id),
 CHECK(status IN ('Scheduled','Completed','Cancelled'))
);

CREATE TABLE tournament (
 tournament_id INT AUTO_INCREMENT PRIMARY KEY,
 sport_id INT NOT NULL,
 name VARCHAR(150) NOT NULL UNIQUE,
 start_date DATE NOT NULL,
 end_date DATE NOT NULL,
 status VARCHAR(20) NOT NULL DEFAULT 'Upcoming',
 FOREIGN KEY(sport_id) REFERENCES sport(sport_id),
 CHECK(end_date>=start_date),
 CHECK(status IN ('Upcoming','Open','Ongoing','Completed','Cancelled'))
);

CREATE TABLE fixture (
 fixture_id INT AUTO_INCREMENT PRIMARY KEY,
 tournament_id INT NOT NULL,
 fixture_date DATE NOT NULL,
 fixture_time TIME NOT NULL,
 venue VARCHAR(150) NOT NULL,
 status VARCHAR(20) NOT NULL DEFAULT 'Scheduled',
 FOREIGN KEY(tournament_id) REFERENCES tournament(tournament_id),
 CHECK(status IN ('Scheduled','Completed','Cancelled'))
);

CREATE TABLE participant (
 participant_id INT AUTO_INCREMENT PRIMARY KEY,
 fixture_id INT NOT NULL,
 team_id INT NOT NULL,
 registration_date DATE NOT NULL,
 role VARCHAR(50) DEFAULT 'Team',
 FOREIGN KEY(fixture_id) REFERENCES fixture(fixture_id),
 FOREIGN KEY(team_id) REFERENCES team(team_id),
 UNIQUE(fixture_id,team_id)
);

CREATE TABLE result (
 result_id INT AUTO_INCREMENT PRIMARY KEY,
 fixture_id INT NOT NULL UNIQUE,
 winner VARCHAR(120),
 score VARCHAR(40) NOT NULL,
 result_date DATE NOT NULL,
 FOREIGN KEY(fixture_id) REFERENCES fixture(fixture_id)
);

CREATE INDEX idx_member_plan ON member(plan_id);
CREATE INDEX idx_payment_member ON payment(member_id);
CREATE INDEX idx_training_date ON training_session(session_date);
CREATE INDEX idx_training_facility_date ON training_session(facility_id,session_date);
CREATE INDEX idx_fixture_tournament ON fixture(tournament_id);
CREATE INDEX idx_participant_team ON participant(team_id);

-- Add sample data from the SQLite version if required.
