from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import math
import json
import sqlite3
import datetime
import os

app = Flask(__name__)
app.secret_key = 'campus_navigator_secret_key_2024'

# Database initialization
def init_db():
    """Initialize the SQLite database and create tables if they don't exist"""
    try:
        conn = sqlite3.connect('campus_navigation.db')
        c = conn.cursor()
        
        # users table to store login information
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT
            )
        ''')
        
        # user_activity table to track user navigation
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                start_location TEXT,
                end_location TEXT,
                route_taken TEXT,
                distance REAL,
                duration TEXT,
                activity_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")

# Initializing database when app starts
init_db()

def save_user_login(name, role, session_id):
    """Save user login data to database"""
    try:
        conn = sqlite3.connect('campus_navigation.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO users (name, role, session_id) 
            VALUES (?, ?, ?)
        ''', (name, role, session_id))
        
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        
        print(f"User login saved: {name}, {role}, ID: {user_id}")
        return user_id
    except Exception as e:
        print(f"Error saving user login: {e}")
        return None

def save_user_activity(user_id, start_location, end_location, route_taken, distance, duration):
    """Save user navigation activity to database"""
    try:
        conn = sqlite3.connect('campus_navigation.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO user_activity (user_id, start_location, end_location, route_taken, distance, duration)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, start_location, end_location, json.dumps(route_taken), distance, duration))
        
        conn.commit()
        conn.close()
        
        print(f"User activity saved: User {user_id}, {start_location} -> {end_location}")
        return True
    except Exception as e:
        print(f"Error saving user activity: {e}")
        return False

def get_user_by_session(session_id):
    """Get user data by session ID"""
    try:
        conn = sqlite3.connect('campus_navigation.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT id, name, role FROM users WHERE session_id = ? ORDER BY login_time DESC LIMIT 1
        ''', (session_id,))
        
        user = c.fetchone()
        conn.close()
        
        if user:
            return {'id': user[0], 'name': user[1], 'role': user[2]}
        return None
    except Exception as e:
        print(f"Error getting user by session: {e}")
        return None

def check_user_exists():
    """Check if current user exists in database"""
    try:
        session_id = session.get('session_id', '')
        if not session_id:
            return False
            
        conn = sqlite3.connect('campus_navigation.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT COUNT(*) FROM users WHERE session_id = ?
        ''', (session_id,))
        
        count = c.fetchone()[0]
        conn.close()
        
        return count > 0
    except Exception as e:
        print(f"Error checking user existence: {e}")
        return False

# Language 
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'हिन्दी (Hindi)',
    'kn': 'ಕನ್ನಡ (Kannada)',
    'ta': 'தமிழ் (Tamil)',
    'te': 'తెలుగు (Telugu)'
}

DEFAULT_LANGUAGE = 'en'

# Graph Data
GRAPH_DATA = {
    "nodes": {
        # --- GROUND FLOOR ---
        "Golden jubliee": {"label": "Golden jubliee", "floor": "ground", "type": "classroom", "x": 1000, "y": 1000, "description": "Large seminar/event hall for golden jubilee events."},
        "G1": {"label": "G1", "floor": "ground", "type": "classroom", "x": 1020, "y": 1050, "description": "Standard ground floor classroom."},
        "G2": {"label": "G2", "floor": "ground", "type": "classroom", "x": 1040, "y": 1100, "description": "Standard ground floor classroom."},
        "G3": {"label": "G3", "floor": "ground", "type": "classroom", "x": 1060, "y": 1150, "description": "Standard ground floor classroom."},
        "G4": {"label": "G4", "floor": "ground", "type": "classroom", "x": 1080, "y": 1200, "description": "Standard ground floor classroom."},
        "G5": {"label": "G5", "floor": "ground", "type": "classroom", "x": 1100, "y": 1250, "description": "Standard ground floor classroom."},
        "G6": {"label": "G6", "floor": "ground", "type": "classroom", "x": 1120, "y": 1300, "description": "Standard ground floor classroom."},
        "G7": {"label": "G7", "floor": "ground", "type": "classroom", "x": 1140, "y": 1350, "description": "Standard ground floor classroom."},
        "G8": {"label": "G8", "floor": "ground", "type": "classroom", "x": 1160, "y": 1400, "description": "Standard ground floor classroom."},
        "Department of Physical Education": {"label": "Gym Room", "floor": "ground", "type": "Department", "x": 1180, "y": 1450, "description": "The main office and facilities for the Department of Physical Education."},
        "Ladies Toilet1": {"label": "Ladies Toilet1", "floor": "ground", "type": "Washroom", "x": 1200, "y": 1500, "description": "Women's washroom facilities."},
        "Stairs_G3": {"label": "Stair 3 G-F", "floor": "ground", "type": "stairs", "x": 1218, "y": 1446, "description": "Staircase 3, connecting Ground and First Floor."},
        "Bun World": {"label": "Bun World", "floor": "ground", "type": "Canteen", "x": 1369, "y": 1339, "description": "A popular food stall near the main canteen."},
        "Stock Room": {"label": "Stock Room", "floor": "ground", "type": "Room", "x": 1395, "y": 1314, "description": "General college supply stock room."},
        "Health Center": {"label": "Health Room", "floor": "ground", "type": "Room", "x": 1423, "y": 1293, "description": "First-aid and basic medical facility."},
        "Transformer": {"label": "transformer", "floor": "ground", "type": "Room", "x": 1467, "y": 1243, "description": "Electrical transformer room (restricted access)."},
        "Garden": {"label": "Garden", "floor": "ground", "type": "Garden", "x": 1495, "y": 1146, "description": "The college garden/courtyard area."},
        "Examination Room": {"label": "Examination Room", "floor": "ground", "type": "Office", "x": 1216, "y": 1420, "description": "Room used for confidential examination work."},
        "Deptartment of Psychology": {"label": "Dept. Pyschology", "floor": "ground", "type": "Department", "x": 1248, "y": 1387, "description": "Departmental office for Psychology."},
        "G9": {"label": "G9", "floor": "ground", "type": "classroom", "x": 1285, "y": 1350, "description": "Standard ground floor classroom."},
        "G10": {"label": "G10", "floor": "ground", "type": "classroom", "x": 1326, "y": 1305, "description": "Standard ground floor classroom."},
        "G11": {"label": "G11", "floor": "ground", "type": "classroom", "x": 1374, "y": 1262, "description": "Standard ground floor classroom."},
        "Department of Language": {"label": "Dept. Lang", "floor": "ground", "type": "Department", "x": 1411, "y": 1233, "description": "Departmental office for Languages."},
        "Mens Toilet": {"label": "Mens Toilet", "floor": "ground", "type": "Washroom", "x": 1431, "y": 1208, "description": "Men's washroom facilities."},
        "Fee Counter": {"label": "Fee Counter", "floor": "ground", "type": "Office", "x": 1380, "y": 1187, "description": "Location for fee payment and accounts."},
        "Library": {"label": "Library", "floor": "ground", "type": "Room", "x": 1403, "y": 1164, "description": "Small reading/reference library on the ground floor."},
        "Reception": {"label": "Reception", "floor": "ground", "type": "Office", "x": 1393, "y": 1114, "description": "Main reception area for inquiries."},
        "PUC Principal Room": {"label": "PUC Principal", "floor": "ground", "type": "Office", "x": 1370, "y": 1061, "description": "Office of the PUC (Pre-University College) Principal."},
        "Stairs_G1": {"label": "Stair 1 G-F", "floor": "ground", "type": "stairs", "x": 1319, "y": 1110, "description": "Staircase 1, connecting Ground and First Floor."},
        "Muesum": {"label": "Muesum", "floor": "ground", "type": "Room", "x": 1350, "y": 1145, "description": "College history and artifact museum."},
        "Reprography": {"label": "Reprography", "floor": "ground", "type": "Room", "x": 1062, "y": 981, "description": "Photocopying and printing services."},
        "Stairs_G2": {"label": "Stair 2 G-F", "floor": "ground", "type": "stairs", "x": 1049, "y": 960, "description": "Staircase 2, connecting Ground and First Floor."},
        "Stage": {"label": "Stage", "floor": "ground", "type": "Room", "x": 1212, "y": 1146, "description": "Auditorium/Hall stage area."},
        "Server Room": {"label": "Server Room", "floor": "ground", "type": "Room", "x": 1168, "y": 1164, "description": "Main college server and network room."},
        "Finance Officer Room": {"label": "FO Room", "floor": "ground", "type": "Office", "x": 1258, "y": 1131, "description": "Office of the Finance Officer."},
        "Office Room": {"label": "Office Room", "floor": "ground", "type": "Office", "x": 1166, "y": 1096, "description": "General administrative office."},
        "Degree PrincipalRoom": {"label": "Degree Principal", "floor": "ground", "type": "office", "x": 1234, "y": 1073, "description": "Office of the Degree College Principal."},
        "Gate": {"label": "Gate", "floor": "ground", "type": "Entrance", "x": 1278, "y": 958, "description": "Main entrance/exit gate to the campus."},
        "Canteen": {"label": "Canteen", "floor": "ground", "type": "Canteen", "x": 1320, "y": 1380, "description": "The main college canteen area."},
        "Lift_G": {"label": "Lift", "floor": "ground", "type": "lift", "x": 1121, "y": 1149, "description": "Elevator connecting all floors."},

        # --- FIRST FLOOR ---
        "Animal Room": {"label": "Animal Room", "floor": "first", "type": "lab", "x": 1000, "y": 1000, "description": "Animal holding room."},
        "BioTech Lab": {"label": "BioTech Lab", "floor": "first", "type": "lab", "x": 1020, "y": 1050, "description": "Biology/Biotechnology laboratory."},
        "Zoology Lab1": {"label": "Zoology Lab1", "floor": "first", "type": "lab", "x": 1040, "y": 1100, "description": "Zoology teaching laboratory."},
        "Staff Room1": {"label": "Staff Room1", "floor": "first", "type": "office", "x": 1060, "y": 1150, "description": "First floor staff common room."},
        "PGBioChem Lab": {"label": "PGBioChem Lab", "floor": "first", "type": "lab", "x": 1080, "y": 1200, "description": "Post-Graduate Biochemistry laboratory."},
        "Chem Lab3": {"label": "Chem Lab3", "floor": "first", "type": "lab", "x": 1100, "y": 1250, "description": "Chemistry laboratory 3."},
        "Chem Lab2": {"label": "Chem Lab2", "floor": "first", "type": "lab", "x": 1140, "y": 1350, "description": "Chemistry laboratory 2."},
        "Chem Lab1": {"label": "Chem Lab1", "floor": "first", "type": "lab", "x": 1160, "y": 1400, "description": "Chemistry laboratory 1."},
        "Department of Chemistry": {"label": "Dept. Chemistry", "floor": "first", "type": "Department", "x": 1180, "y": 1450, "description": "Main office for the Department of Chemistry."},
        "Staff Room2": {"label": "Staff Room2", "floor": "first", "type": "office", "x": 1190, "y": 1478, "description": "Secondary staff common room."},
        "Ladies Toilet2": {"label": "Ladies Toilet2", "floor": "first", "type": "Washroom", "x": 1200, "y": 1500, "description": "Women's washroom facilities."},
        "Stairs_F3": {"label": "Stair 3 F-S", "floor": "first", "type": "stairs", "x": 1218, "y": 1446, "description": "Staircase 3, connecting First and Second Floor."},
        "Physics Lab1": {"label": "Physics Lab1", "floor": "first", "type": "lab", "x": 1216, "y": 1420, "description": "Physics teaching laboratory 1."},
        "Physics Lab2": {"label": "Physics Lab2", "floor": "first", "type": "lab", "x": 1326, "y": 1305, "description": "Physics teaching laboratory 2."},
        "Physics Lab3": {"label": "Physics Lab3", "floor": "first", "type": "lab", "x": 1374, "y": 1262, "description": "Physics teaching laboratory 3."},
        "F5": {"label": "F5 Class", "floor": "first", "type": "classroom", "x": 1431, "y": 1208, "description": "Standard first floor classroom F5."},
        "MicroBio Lab": {"label": "MicroBio Lab", "floor": "first", "type": "lab", "x": 1421, "y": 1189, "description": "Microbiology laboratory."},
        "Botany Lab1": {"label": "Botany Lab1", "floor": "first", "type": "lab", "x": 1409, "y": 1169, "description": "Botany teaching laboratory 1."},
        "Botany Lab2": {"label": "Botany Lab2", "floor": "first", "type": "lab", "x": 1403, "y": 1139, "description": "Botany teaching laboratory 2."},
        "Dept jornalisim": {"label": "Dept. Journalism", "floor": "first", "type": "Department", "x": 1393, "y": 1114, "description": "Office for the Department of Journalism."},
        "Dept Botany": {"label": "Dept. Botany", "floor": "first", "type": "Department", "x": 1370, "y": 1061, "description": "Main office for the Department of Botany."},
        "Stairs_F1": {"label": "Stair 1 F-S", "floor": "first", "type": "stairs", "x": 1319, "y": 1110, "description": "Staircase 1, connecting First and Second Floor."},
        "Stairs_F2": {"label": "Stair 2 F-S", "floor": "first", "type": "stairs", "x": 1049, "y": 960, "description": "Staircase 2, connecting First and Second Floor."},
        "F1": {"label": "F1 Class", "floor": "first", "type": "classroom", "x": 1212, "y": 1146, "description": "Standard first floor classroom F1."},
        "F4": {"label": "F4 Class", "floor": "first", "type": "classroom", "x": 1136, "y": 1112, "description": "Standard first floor classroom F4."},
        "F3": {"label": "F3 Class", "floor": "first", "type": "classroom", "x": 1201, "y": 1083, "description": "Standard first floor classroom F3."},
        "F2": {"label": "F2 Class", "floor": "first", "type": "classroom", "x": 1234, "y": 1073, "description": "Standard first floor classroom F2."},
        "Lift_F": {"label": "Lift", "floor": "first", "type": "lift", "x": 1121, "y": 1149, "description": "Elevator connecting all floors."},

           #-- SECOND FLOOR ---
            "Stairs_S3": { "label": "Stair 3 S-T", "floor": "second", "type": "stairs", "x": 1218, "y": 1446, "description": "Staircase 3, connecting Second and Third Floor." },
            "Stairs_S1": { "label": "Stair 1 S-T", "floor": "second", "type": "stairs", "x": 1319, "y": 1110, "description": "Staircase 1, connecting Second and Third Floor." },
            "Stairs_S2": { "label": "Stair 2 S-T", "floor": "second", "type": "stairs", "x": 1049, "y": 960, "description": "Staircase 2, connecting Second and Third Floor." },
            "Stairs_S4": { "label": "Stair 4 S-T", "floor": "second", "type": "stairs", "x": 1426, "y": 1166, "description": "Staircase 4, connecting Second and Third Floor." },
            "Zoology Lab2": { "label": "Zoology Lab2", "floor": "second", "type": "lab", "x": 1000, "y": 1000, "description": "Zoology Laboratory 2." }, 
            "S3": { "label": "S3", "floor": "second", "type": "classroom", "x": 1020, "y": 1050, "description": "Classroom S3." }, 
            "S4": { "label": "S4", "floor": "second", "type": "classroom", "x": 1040, "y": 1100, "description": "Classroom S4." }, 
            "S5": { "label": "S5", "floor": "second", "type": "classroom", "x": 1060, "y": 1150, "description": "Classroom S5." }, 
            "S6": { "label": "S6", "floor": "second", "type": "classroom", "x": 1080, "y": 1200, "description": "Classroom S6." }, 
            "S7": { "label": "S7", "floor": "second", "type": "classroom", "x": 1100, "y": 1250, "description": "Classroom S7." }, 
            "S8": { "label": "S8", "floor": "second", "type": "classroom", "x": 1140, "y": 1350, "description": "Classroom S8." }, 
            "S2": { "label": "S2", "floor": "second", "type": "classroom", "x": 1160, "y": 1400, "description": "Classroom S2." }, 
            "S1": { "label": "S1", "floor": "second", "type": "classroom", "x": 1180, "y": 1450, "description": "Classroom S1." }, 
            "Common Room": { "label": "Common Room", "floor": "second", "type": "office", "x": 1190, "y": 1478, "description": "General common/lounge area on the second floor." },
            "Ladies Toilet3": { "label": "Ladies Toilet3", "floor": "second", "type": "Washroom", "x": 1200, "y": 1500, "description": "Women's washroom facilities." },
            "Dept of commerce office": { "label": "Dept of Commerce Office", "floor": "second", "type": "Department", "x": 1216, "y": 1420, "description": "Department of Commerce administrative office." },
            "HOD Room": { "label": "HOD Room", "floor": "second", "type": "office", "x": 1248, "y": 1387, "description": "Head of Department (HOD) office." },
            "Office": { "label": "Office", "floor": "second", "type": "office", "x": 1285, "y": 1350, "description": "General office space." },
            "Conference Room": { "label": "Conference Room", "floor": "second", "type": "office", "x": 1326, "y": 1305, "description": "Meeting/conference room." },
            "Seminar Hall2": { "label": "Seminar Hall2", "floor": "second", "type": "seminar", "x": 1374, "y": 1262, "description": "Second floor seminar hall." },
            "HOD Room 2": { "label": "HOD Room 2", "floor": "second", "type": "office", "x": 1387, "y": 1242, "description": "Second Head of Department (HOD) office." },
            "Dept of Management Studies": { "label": "Dept of Management Studies", "floor": "second", "type": "Department", "x": 1431, "y": 1208, "description": "Department of Management Studies Office." },
            "NCC AirWing Room": { "label": "NCC AirWing Room", "floor": "second", "type": "office", "x": 1421, "y": 1189, "description": "NCC Air Wing meeting/store room." },
            "S9": { "label": "S9", "floor": "second", "type": "classroom", "x": 1409, "y": 1084, "description": "Classroom S9." }, 
            "S10": { "label": "S10", "floor": "second", "type": "classroom", "x": 1418, "y": 1118, "description": "Classroom S10." }, 
            "S11": { "label": "S11", "floor": "second", "type": "classroom", "x": 1432, "y": 1147, "description": "Classroom S11." }, 
            "S12": { "label": "S12", "floor": "second", "type": "classroom", "x": 1443, "y": 1176, "description": "Classroom S12." }, 
            "Step1": { "label": "Step1", "floor": "second", "type": "connector", "x": 1370, "y": 1061, "description": "Connector point 1." }, 
            "Londge": { "label": "Londge", "floor": "second", "type": "common", "x": 1466, "y": 1047, "description": "General lounge/waiting area." },
            "Lift_S": {"label": "Lift", "floor": "second", "type": "lift", "x": 1121, "y": 1149, "description": "Elevator connecting all floors."},

            # --- THIRD FLOOR ---
            "Animal Cell Culture": { "label": "Animal Cell Culture", "floor": "third", "type": "lab", "x": 995, "y": 993, "description": "Laboratory for Animal Cell Culture." },
            "Life Science Research Center": { "label": "Life Science Research Center", "floor": "third", "type": "office", "x": 1000, "y": 1000, "description": "Research center administrative office." },
            "T1": { "label": "T1", "floor": "third", "type": "connector", "x": 1030, "y": 1077, "description": "Junction point T1." },
            "PG Library": { "label": "PG Library", "floor": "third", "type": "library", "x": 1040, "y": 1100, "description": "Post-Graduate student library/study area." },
            "T2": { "label": "T2", "floor": "third", "type": "connector", "x": 1052, "y": 1130, "description": "Junction point T2." },
            "T3": { "label": "T3", "floor": "third", "type": "connector", "x": 1060, "y": 1150, "description": "Junction point T3." },
            "Kannada Research Center": { "label": "Kannada Research Center", "floor": "third", "type": "office", "x": 1075, "y": 1184, "description": "Research center for Kannada language/literature." },
            "NCC Army Stock Room": { "label": "NCC Army Stock Room", "floor": "third", "type": "office", "x": 1136, "y": 1130, "description": "Storage/office room for NCC Army Wing." },
            "Stairs_T2": { "label": "Stair 2 T-R", "floor": "third", "type": "stairs", "x": 1049, "y": 960, "description": "Staircase 2." },
            "T4": { "label": "T4", "floor": "third", "type": "connector", "x": 1180, "y": 1450, "description": "Junction point T4." },
            "T5": { "label": "T5", "floor": "third", "type": "connector", "x": 1190, "y": 1478, "description": "Junction point T5." },
            "T6": { "label": "T6", "floor": "third", "type": "connector", "x": 1200, "y": 1500, "description": "Junction point T6." },
            "Stairs_T3": { "label": "Stair 3 T-R", "floor": "third", "type": "stairs", "x": 1218, "y": 1446, "description": "Staircase 3." },
            "T7": { "label": "T7", "floor": "third", "type": "connector", "x": 1240, "y": 1402, "description": "Junction point T7." },
            "DBT Room": { "label": "DBT Room", "floor": "third", "type": "office", "x": 1248, "y": 1387, "description": "Department of Biotechnology (DBT) office/facility." },
            "Commerce Research Center": { "label": "Commerce Research Center", "floor": "third", "type": "office", "x": 1285, "y": 1350, "description": "Research center for Commerce studies." },
            "Dept of commerce": { "label": "Dept of commerce", "floor": "third", "type": "office", "x": 1326, "y": 1305, "description": "Departmental office for Commerce." },
            "Business Lab": { "label": "Business Lab", "floor": "third", "type": "lab", "x": 1374, "y": 1262, "description": "Laboratory/practical room for Business studies." },
            "T8": { "label": "T8", "floor": "third", "type": "connector", "x": 1387, "y": 1242, "description": "Junction point T8." },
            "Stairs_T4": { "label": "Stair 4 T-R", "floor": "third", "type": "stairs", "x": 1426, "y": 1166, "description": "Staircase 4." },
            "Lift_T": {"label": "Lift", "floor": "third", "type": "lift", "x": 1121, "y": 1149, "description": "Elevator connecting all floors."}

    },
    "adjacency": {
        # Ground floor adjacency
        "Golden jubliee": {"G1": 10, "Reprography": 5},
        "G1": {"G2": 10, "Golden jubliee": 10},
        "G2": {"G1": 10, "G3": 10},
        "G3": {"G2": 10, "G4": 10},
        "G4": {"G3": 10, "G5": 10, "Server Room": 15, "Office Room": 20, "Lift_G": 8},
        "G5": {"G4": 10, "G6": 10},
        "G6": {"G5": 10, "G7": 10},
        "G7": {"G6": 10, "G8": 10},
        "G8": {"G7": 10, "Department of Physical Education": 10, "Examination Room": 15},
        "Department of Physical Education": {"G8": 10, "Ladies Toilet1": 10, "Stairs_G3": 10},
        "Ladies Toilet1": {"Department of Physical Education": 10, "Canteen": 10},
        "Stairs_G3": {"Department of Physical Education": 10, "Examination Room": 10},
        "Bun World": {"Canteen": 30, "Stock Room": 10},
        "Stock Room": {"Bun World": 10, "Health Center": 10},
        "Health Center": {"Stock Room": 10, "Transformer": 10},
        "Transformer": {"Health Center": 10, "Garden": 10},
        "Garden": {"Transformer": 10, "Reception": 10},
        "Examination Room": {"Stairs_G3": 10, "Deptartment of Psychology": 10, "G8": 15},
        "Deptartment of Psychology": {"Examination Room": 10, "G9": 10},
        "G9": {"Deptartment of Psychology": 10, "G10": 10},
        "G10": {"G9": 10, "G11": 10},
        "G11": {"G10": 10, "Department of Language": 10},
        "Department of Language": {"G11": 10, "Mens Toilet": 10},
        "Mens Toilet": {"Department of Language": 10, "Fee Counter": 10},
        "Fee Counter": {"Mens Toilet": 10, "Library": 10},
        "Library": {"Fee Counter": 10, "Reception": 10},
        "Reception": {"Library": 10, "PUC Principal Room": 10, "Gate": 30, "Muesum": 10, "Garden": 10},
        "PUC Principal Room": {"Reception": 10, "Stairs_G1": 10},
        "Stairs_G1": {"PUC Principal Room": 10, "Muesum": 10, "Gate": 30},
        "Muesum": {"Stairs_G1": 10, "Reception": 10, "Stage": 20},
        "Reprography": {"Golden jubliee": 5, "Stairs_G2": 10},
        "Stairs_G2": {"Reprography": 10, "Gate": 50},
        "Stage": {"Muesum": 20, "Server Room": 10, "Finance Officer Room": 10, "Office Room": 5},
        "Server Room": {"Stage": 10, "G4": 15, "Lift_G": 12},
        "Finance Officer Room": {"Degree PrincipalRoom": 5, "Stage": 10},
        "Office Room": {"Stage": 5, "Degree PrincipalRoom": 10, "G4": 20},
        "Degree PrincipalRoom": {"Office Room": 10, "Finance Officer Room": 5},
        "Gate": {"Stairs_G1": 30, "Reprography": 50, "Garden": 80, "Stairs_G2": 50},
        "Canteen": {"Bun World": 30, "Ladies Toilet1": 10},
        "Lift_G": {"G4": 8, "Server Room": 12},

        # First floor adjacency
        "Animal Room": {"BioTech Lab": 10, "Stairs_F2": 5},
        "BioTech Lab": {"Animal Room": 10, "Zoology Lab1": 10},
        "Zoology Lab1": {"BioTech Lab": 10, "Staff Room1": 10},
        "Staff Room1": {"Zoology Lab1": 10, "PGBioChem Lab": 10, "F4": 10, "F3": 10, "Lift_F": 8},
        "PGBioChem Lab": {"Staff Room1": 10, "Chem Lab3": 10},
        "Chem Lab3": {"PGBioChem Lab": 10},
        "Chem Lab2": {"Chem Lab1": 10, "Chem Lab3": 20, "Physics Lab1": 30},
        "Chem Lab1": {"Chem Lab2": 10, "Department of Chemistry": 10},
        "Department of Chemistry": {"Chem Lab1": 10, "Staff Room2": 10, "Stairs_F3": 10},
        "Staff Room2": {"Department of Chemistry": 10, "Ladies Toilet2": 10},
        "Ladies Toilet2": {"Staff Room2": 10},
        "Stairs_F3": {"Department of Chemistry": 10, "Physics Lab1": 10},
        "Physics Lab1": {"Stairs_F3": 10, "Chem Lab2": 30, "F1": 10, "F2": 20},
        "Physics Lab2": {"Physics Lab3": 10, "F1": 10, "F2": 10},
        "Physics Lab3": {"Physics Lab2": 10, "F5": 10},
        "F5": {"Physics Lab3": 10, "MicroBio Lab": 10},
        "MicroBio Lab": {"F5": 10, "Botany Lab1": 10},
        "Botany Lab1": {"MicroBio Lab": 10, "Botany Lab2": 10},
        "Botany Lab2": {"Botany Lab1": 10, "Dept jornalisim": 10},
        "Dept jornalisim": {"Botany Lab2": 10, "Dept Botany": 10},
        "Dept Botany": {"Dept jornalisim": 10, "Stairs_F1": 10},
        "Stairs_F1": {"Dept Botany": 10, "F3": 20},
        "Stairs_F2": {"Animal Room": 5, "F4": 10},
        "F1": {"Physics Lab1": 10, "Physics Lab2": 10, "F4": 10, "F3": 5},
        "F4": {"F1": 10, "Staff Room1": 10, "Stairs_F2": 10, "F3": 10, "Lift_F": 8},
        "F3": {"F4": 10, "F1": 5, "Staff Room1": 10, "Stairs_F1": 20, "F2": 5},
        "F2": {"F3": 5, "Physics Lab1": 20, "Physics Lab2": 10},
        "Lift_F": {"Staff Room1": 8, "F4": 8},

             #-- SECOND FLOOR ADJACENCY (Intra-Floor) ---
            "Zoology Lab2": { "S3": 10, "Stairs_S2": 10 },
            "S3": { "Zoology Lab2": 10, "S4": 10 },
            "S4": { "S3": 10, "S5": 10 },
            "S5": { "S4": 10, "S6": 10 },
            "S6": { "S5": 10, "S7": 10 },
            "S7": { "S6": 10, "S8": 10 },
            "S8": { "S7": 10, "S2": 10 },
            "S2": { "S8": 10, "S1": 10, "Dept of commerce office": 10 },
            "S1": { "S2": 10, "Common Room": 10, "Stairs_S3": 10 },
            "Common Room": { "S1": 10, "Ladies Toilet3": 10 },
            "Ladies Toilet3": { "Common Room": 10 },
            "Dept of commerce office": { "S2": 10, "HOD Room": 10 },
            "HOD Room": { "Dept of commerce office": 10, "Office": 10 },
            "Office": { "HOD Room": 10, "Conference Room": 10 },
            "Conference Room": { "Office": 10, "Seminar Hall2": 10 },
            "Seminar Hall2": { "Conference Room": 10, "HOD Room 2": 10 },
            "HOD Room 2": { "Seminar Hall2": 10, "Dept of Management Studies": 10, "NCC AirWing Room": 10},
            "Dept of Management Studies": { "HOD Room 2": 10, "NCC AirWing Room": 10 },
            "NCC AirWing Room": { "Dept of Management Studies": 10, "S12": 10 },
            "S12": { "NCC AirWing Room": 10, "S11": 10, "Stairs_S3": 10, "Stairs_S4": 10, "Lift_S": 8}, #PATCHED: Added Stairs_S4
            "S11": { "S12": 10, "S10": 10 },
            "S10": { "S11": 10, "S9": 10 },
            "S9": { "S10": 10, "Step1": 10 },
            "Step1": { "S9": 10, "Londge": 10, "Stairs_S1": 10 },
            "Londge": { "Step1": 10 },
            "Stairs_S3": { "S1": 10, "S12": 10 },
            "Stairs_S1": { "Step1": 10 },
            "Stairs_S2": { "Zoology Lab2": 10 },
            "Stairs_S4": { "S12": 10 },
            "Lift_S": {"S12": 8},

            #-- THIRD FLOOR ADJACENCY (Intra-Floor) ---
            "Animal Cell Culture": { "Stairs_T2": 10, "Life Science Research Center": 10 },
            "Life Science Research Center": { "Animal Cell Culture": 10, "T1": 15 },
            "T1": { "Life Science Research Center": 15, "PG Library": 10 },
            "PG Library": { "T1": 10, "T2": 15 },
            "T2": { "PG Library": 15, "T3": 10},
            "T3": { "T2": 10, "Kannada Research Center": 10},
            "Kannada Research Center": { "T3": 10, "NCC Army Stock Room": 10},
            "NCC Army Stock Room": { "Kannada Research Center": 10},
            "Stairs_T2": { "Animal Cell Culture": 10, }, 
            "T4": { "T5": 10, "Stairs_T3": 10 },
            "T5": { "T4": 10, "T6": 10 },
            "T6": { "T5": 10 },
            "Stairs_T3": { "T4": 10, "T7": 10}, 
            "T7": { "Stairs_T3": 10, "DBT Room": 10 },
            "DBT Room": { "T7": 10, "Commerce Research Center": 10 },
            "Commerce Research Center": { "DBT Room": 10, "Dept of commerce": 10 },
            "Dept of commerce": { "Commerce Research Center": 10, "Business Lab": 10 },
            "Business Lab": { "Dept of commerce": 10, "T8": 10 },
            "T8": { "Business Lab": 10, "Stairs_T4": 5, "Lift_T": 8},
            "Stairs_T4": { "T8": 5 },
            "Lift_T": {"T8": 8},

             #--- INTER-FLOOR ADJACENCY (G->F, F->S, S->T) ---
            "Stairs_G1": { "Stairs_F1": 10 },
            "Stairs_G2": { "Stairs_F2": 10 },
            "Stairs_G3": { "Stairs_F3": 10 },

            "Stairs_F1": { "Stairs_G1": 10, "Stairs_S1": 10 },
            "Stairs_F2": { "Stairs_G2": 10, "Stairs_S2": 10 },
            "Stairs_F3": { "Stairs_G3": 10, "Stairs_S3": 10 },

            "Stairs_S1": { "Stairs_F1": 10 },
            "Stairs_S2": { "Stairs_F2": 10, "Stairs_T2": 10 },
            "Stairs_S3": { "Stairs_F3": 10, "Stairs_T3": 10 },
            "Stairs_S4": { "Stairs_T4": 10 }, # S->T connection

            "Stairs_T2": { "Stairs_S2": 10 }, 
            "Stairs_T3": { "Stairs_S3": 10 }, 
            "Stairs_T4": { "Stairs_S4": 10 }, # T->S connection

            # Lift connections (faster than stairs)
            "Lift_G": { "Lift_F": 3 }, 
            "Lift_F": { "Lift_G": 3, "Lift_S": 3 },
            "Lift_S": { "Lift_F": 3, "Lift_T": 3 },
            "Lift_T": { "Lift_S": 3 }
    }
}

# Path Data for corridors and pathways
PATH_DATA = {
    "ground": [
        # Main corridors based on adjacency connections
        {"type": "corridor", "points": [[1000, 1000], [1020, 1050], [1040, 1100], [1060, 1150], [1080, 1200]]},
        {"type": "corridor", "points": [[1080, 1200], [1100, 1250], [1120, 1300], [1140, 1350], [1160, 1400]]},
        {"type": "corridor", "points": [[1160, 1400], [1180, 1450], [1200, 1500]]},
        {"type": "corridor", "points": [[1180, 1450], [1218, 1446], [1216, 1420]]},
        {"type": "corridor", "points": [[1216, 1420], [1248, 1387], [1285, 1350], [1326, 1305], [1374, 1262]]},
        {"type": "corridor", "points": [[1374, 1262], [1411, 1233], [1431, 1208]]},
        {"type": "corridor", "points": [[1431, 1208], [1380, 1187], [1403, 1164]]},
        {"type": "corridor", "points": [[1403, 1164], [1393, 1114], [1370, 1061]]},
        {"type": "corridor", "points": [[1393, 1114], [1350, 1145], [1319, 1110]]},
        {"type": "corridor", "points": [[1319, 1110], [1278, 958]]},
        {"type": "corridor", "points": [[1000, 1000], [1062, 981], [1049, 960]]},
        {"type": "corridor", "points": [[1049, 960], [1278, 958]]},
        {"type": "corridor", "points": [[1350, 1145], [1212, 1146]]},
        {"type": "corridor", "points": [[1212, 1146], [1168, 1164], [1121, 1149]]},
        {"type": "corridor", "points": [[1212, 1146], [1258, 1131], [1234, 1073]]},
        {"type": "corridor", "points": [[1234, 1073], [1166, 1096]]},
        {"type": "corridor", "points": [[1200, 1500], [1320, 1380]]},
        {"type": "corridor", "points": [[1320, 1380], [1369, 1339], [1395, 1314], [1423, 1293], [1467, 1243], [1495, 1146]]},
        {"type": "corridor", "points": [[1495, 1146], [1393, 1114]]}
    ],
    "first": [
        # First floor corridors
        {"type": "corridor", "points": [[1000, 1000], [1020, 1050], [1040, 1100], [1060, 1150], [1080, 1200]]},
        {"type": "corridor", "points": [[1060, 1150], [1100, 1250]]},
        {"type": "corridor", "points": [[1140, 1350], [1160, 1400], [1180, 1450], [1200, 1500]]},
        {"type": "corridor", "points": [[1180, 1450], [1218, 1446], [1216, 1420]]},
        {"type": "corridor", "points": [[1216, 1420], [1326, 1305], [1374, 1262]]},
        {"type": "corridor", "points": [[1374, 1262], [1431, 1208]]},
        {"type": "corridor", "points": [[1431, 1208], [1421, 1189], [1409, 1169], [1403, 1139]]},
        {"type": "corridor", "points": [[1403, 1139], [1393, 1114], [1370, 1061]]},
        {"type": "corridor", "points": [[1393, 1114], [1319, 1110]]},
        {"type": "corridor", "points": [[1319, 1110], [1212, 1146]]},
        {"type": "corridor", "points": [[1212, 1146], [1201, 1083], [1234, 1073]]},
        {"type": "corridor", "points": [[1212, 1146], [1136, 1112], [1121, 1149]]},
        {"type": "corridor", "points": [[1000, 1000], [1049, 960]]},
        {"type": "corridor", "points": [[1049, 960], [1136, 1112]]}
    ],
    "second": [
        # Second floor corridors
        {"type": "corridor", "points": [[1000, 1000], [1020, 1050], [1040, 1100], [1060, 1150], [1080, 1200], [1100, 1250]]},
        {"type": "corridor", "points": [[1100, 1250], [1140, 1350], [1160, 1400], [1180, 1450], [1200, 1500]]},
        {"type": "corridor", "points": [[1180, 1450], [1218, 1446], [1216, 1420]]},
        {"type": "corridor", "points": [[1216, 1420], [1248, 1387], [1285, 1350], [1326, 1305], [1374, 1262]]},
        {"type": "corridor", "points": [[1374, 1262], [1387, 1242], [1431, 1208]]},
        {"type": "corridor", "points": [[1431, 1208], [1421, 1189], [1443, 1176]]},
        {"type": "corridor", "points": [[1443, 1176], [1432, 1147], [1418, 1118], [1409, 1084]]},
        {"type": "corridor", "points": [[1409, 1084], [1370, 1061], [1466, 1047]]},
        {"type": "corridor", "points": [[1370, 1061], [1319, 1110]]},
        {"type": "corridor", "points": [[1319, 1110], [1049, 960]]},
        {"type": "corridor", "points": [[1049, 960], [1000, 1000]]},
        {"type": "corridor", "points": [[1443, 1176], [1426, 1166]]}
    ],
    "third": [
        # Third floor corridors
        {"type": "corridor", "points": [[995, 993], [1000, 1000], [1030, 1077], [1040, 1100], [1052, 1130], [1060, 1150]]},
        {"type": "corridor", "points": [[1060, 1150], [1075, 1184], [1136, 1130]]},
        {"type": "corridor", "points": [[1180, 1450], [1190, 1478], [1200, 1500]]},
        {"type": "corridor", "points": [[1180, 1450], [1218, 1446], [1240, 1402]]},
        {"type": "corridor", "points": [[1240, 1402], [1248, 1387], [1285, 1350], [1326, 1305], [1374, 1262]]},
        {"type": "corridor", "points": [[1374, 1262], [1387, 1242], [1426, 1166]]},
        {"type": "corridor", "points": [[995, 993], [1049, 960]]},
        {"type": "corridor", "points": [[1049, 960], [1121, 1149]]}
    ]
}

# Graph data without lift (for MLACW students)
GRAPH_DATA_WITHOUT_LIFT = {
    "nodes": {k: v for k, v in GRAPH_DATA["nodes"].items() if not k.startswith("Lift_")},
    "adjacency": {}
}

# Remove lift connections from adjacency for students
for node, connections in GRAPH_DATA["adjacency"].items():
    if not node.startswith("Lift_"):
        GRAPH_DATA_WITHOUT_LIFT["adjacency"][node] = {
            k: v for k, v in connections.items() 
            if not k.startswith("Lift_")
        }

FLOOR_NAMES = {
    'ground': 'Ground Floor (G)',
    'first': 'First Floor (F)',
    'second': 'Second Floor (S)',
    'third': 'Third Floor (T)',
}

TIME_PER_UNIT_SECONDS = 2.0

class PriorityQueue:
    def __init__(self):
        self.values = []
    
    def enqueue(self, element, priority):
        self.values.append({"element": element, "priority": priority})
        self._bubble_up()
    
    def _bubble_up(self):
        idx = len(self.values) - 1
        element = self.values[idx]
        while idx > 0:
            parent_idx = (idx - 1) // 2
            parent = self.values[parent_idx]
            if element["priority"] >= parent["priority"]:
                break
            self.values[parent_idx] = element
            self.values[idx] = parent
            idx = parent_idx
    
    def dequeue(self):
        if not self.values:
            return None
        min_val = self.values[0]
        end = self.values.pop()
        if self.values:
            self.values[0] = end
            self._sink_down()
        return min_val
    
    def _sink_down(self):
        idx = 0
        length = len(self.values)
        element = self.values[0]
        while True:
            left_child_idx = 2 * idx + 1
            right_child_idx = 2 * idx + 2
            swap = None

            if left_child_idx < length:
                left_child = self.values[left_child_idx]
                if left_child["priority"] < element["priority"]:
                    swap = left_child_idx
            
            if right_child_idx < length:
                right_child = self.values[right_child_idx]
                if (swap is None and right_child["priority"] < element["priority"]) or \
                   (swap is not None and right_child["priority"] < left_child["priority"]):
                    swap = right_child_idx
            
            if swap is None:
                break
            self.values[idx] = self.values[swap]
            self.values[swap] = element
            idx = swap
    
    def is_empty(self):
        return len(self.values) == 0

def dijkstra(start_node, end_node, graph_data):
    distances = {}
    previous = {}
    nodes = PriorityQueue()

    for node in graph_data["nodes"]:
        distances[node] = float('inf')
        previous[node] = None

    distances[start_node] = 0
    nodes.enqueue(start_node, 0)

    path = []
    smallest = None

    while not nodes.is_empty():
        smallest = nodes.dequeue()["element"]

        if smallest == end_node:
            current = end_node
            while current:
                path.append(current)
                current = previous[current]
            path.reverse()

            total_distance = 0
            for i in range(len(path) - 1):
                u = path[i]
                v = path[i + 1]
                if u in graph_data["adjacency"] and v in graph_data["adjacency"][u]:
                    total_distance += graph_data["adjacency"][u][v]
            return {"path": path, "distance": total_distance}

        if smallest not in graph_data["adjacency"]:
            continue

        for neighbor in graph_data["adjacency"][smallest]:
            next_val = distances[smallest] + graph_data["adjacency"][smallest][neighbor]

            if next_val < distances[neighbor]:
                distances[neighbor] = next_val
                previous[neighbor] = smallest
                nodes.enqueue(neighbor, next_val)

    return {"path": [], "distance": 0}

def format_time(total_seconds):
    if total_seconds == 0:
        return "0 seconds"
    minutes = math.floor(total_seconds / 60)
    seconds = round(total_seconds % 60)
    time_string = []
    if minutes > 0:
        time_string.append(f"{minutes} min")
    if seconds > 0 or minutes == 0:
        time_string.append(f"{seconds} sec")
    return ' '.join(time_string)

def make_graph_bidirectional(graph_data):
    for u in list(graph_data["adjacency"].keys()):
        for v in graph_data["adjacency"][u]:
            weight = graph_data["adjacency"][u][v]
            if v not in graph_data["adjacency"]:
                graph_data["adjacency"][v] = {}
            if u not in graph_data["adjacency"][v]:
                graph_data["adjacency"][v][u] = weight

def convert_node_path_to_coordinates(node_path, graph_data):
    """Convert a path of node IDs to a list of coordinates"""
    coordinates = []
    for node_id in node_path:
        node = graph_data["nodes"].get(node_id)
        if node:
            coordinates.append([node["x"], node["y"]])
    return coordinates

def get_floor_segmented_path(node_path, graph_data):
    """Convert node path to floor-segmented coordinate paths"""
    floor_paths = {
        'ground': [],
        'first': [],
        'second': [],
        'third': []
    }
    
    current_floor = None
    current_segment = []
    
    for node_id in node_path:
        node = graph_data["nodes"].get(node_id)
        if not node:
            continue
            
        if node["floor"] != current_floor:
            if current_floor and current_segment:
                floor_paths[current_floor] = current_segment
            
            current_floor = node["floor"]
            current_segment = [[node["x"], node["y"]]]
        else:
            current_segment.append([node["x"], node["y"]])
    
    if current_floor and current_segment:
        floor_paths[current_floor] = current_segment
    
    return floor_paths

# Initialize the graphs
make_graph_bidirectional(GRAPH_DATA)
make_graph_bidirectional(GRAPH_DATA_WITHOUT_LIFT)

# APPLICATION ROUTES

@app.route('/')
def index():
    return render_template('ui.html')

@app.route('/login', methods=['POST'])
def login():
    name = request.form.get('name')
    role = request.form.get('role')
    
    if name and role:
        # unique session identifier
        session_id = os.urandom(16).hex()
        
        # Save user data to database
        user_id = save_user_login(name, role, session_id)
        
        if user_id:
            # Store user info in session
            session['user_name'] = name
            session['user_role'] = role
            session['user_id'] = user_id
            session['session_id'] = session_id
            
            return jsonify({'success': True, 'redirect': url_for('front1')})
        else:
            return jsonify({'success': False, 'error': 'Failed to save user data'})
    
    return jsonify({'success': False, 'error': 'Name and Role required'})

@app.route('/front1')
def front1():
    if 'user_name' not in session:
        return redirect(url_for('index'))
    
    # Verify user exists in database
    user_data = get_user_by_session(session.get('session_id', ''))
    if not user_data:
        return redirect(url_for('index'))
    
    return render_template('front1.html')

@app.route('/route')
def route_page():
    if 'user_name' not in session:
        return redirect(url_for('index'))
    
    start = request.args.get('start')
    end = request.args.get('end')
    
    if not start or not end:
        return redirect(url_for('front1'))
        
    return render_template('route.html', start=start, end=end)

# API ENDPOINTS

@app.route('/calculate-route')
def calculate_route():
    start_node = request.args.get('start')
    end_node = request.args.get('end')
    
    if not start_node or not end_node:
        return jsonify({"error": "Start and end nodes are required"}), 400
    
    # Choose graph data based on user role
    user_role = session.get('user_role', 'mlacw_student')
    if user_role == 'mlacw_student':
        graph_data = GRAPH_DATA_WITHOUT_LIFT
    else:
        graph_data = GRAPH_DATA
    
    # Validate that nodes exist in the graph
    if start_node not in graph_data["nodes"]:
        return jsonify({"error": f"Start node '{start_node}' not found in graph"}), 400
    
    if end_node not in graph_data["nodes"]:
        return jsonify({"error": f"End node '{end_node}' not found in graph"}), 400
    
    try:
        result = dijkstra(start_node, end_node, graph_data)
        
        # Convert node path to floor-segmented coordinate paths
        floor_segmented_paths = get_floor_segmented_path(result["path"], graph_data)
        
        total_time_seconds = result["distance"] * TIME_PER_UNIT_SECONDS
        
        # Save user activity to database
        user_id = session.get('user_id')
        if user_id:
            save_user_activity(
                user_id=user_id,
                start_location=start_node,
                end_location=end_node,
                route_taken=result["path"],
                distance=result["distance"],
                duration=format_time(total_time_seconds)
            )
        
        response = {
            "path": result["path"],
            "floor_segmented_paths": floor_segmented_paths,
            "distance": result["distance"],
            "time": format_time(total_time_seconds),
            "start_label": graph_data["nodes"][start_node]["label"],
            "end_label": graph_data["nodes"][end_node]["label"],
            "user_role": user_role
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": f"Error calculating route: {str(e)}"}), 500

@app.route('/get-graph-data')
def get_graph_data():
    user_role = session.get('user_role', 'mlacw_student')
    if user_role == 'mlacw_student':
        return jsonify(GRAPH_DATA_WITHOUT_LIFT)
    else:
        return jsonify(GRAPH_DATA)

@app.route('/get-path-data')
def get_path_data():
    return jsonify(PATH_DATA)

@app.route('/set-language', methods=['POST'])
def set_language():
    language = request.json.get('language')
    if language in SUPPORTED_LANGUAGES:
        session['language'] = language
        return jsonify({'success': True, 'message': f'Language set to {SUPPORTED_LANGUAGES[language]}'})
    return jsonify({'success': False, 'error': 'Unsupported language'})

@app.route('/get-language')
def get_language():
    return jsonify({
        'current_language': session.get('language', DEFAULT_LANGUAGE),
        'supported_languages': SUPPORTED_LANGUAGES
    })

@app.route('/check-user-exists')
def check_user_exists():
    try:
        session_id = session.get('session_id', '')
        user_id = session.get('user_id')
        
        if not session_id or not user_id:
            return jsonify({'user_exists': False}) 
            
        conn = sqlite3.connect('campus_navigation.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT COUNT(*) FROM users 
            WHERE session_id = ? AND id = ?
        ''', (session_id, user_id))
        
        count = c.fetchone()[0]
        conn.close()
        
        print(f"User existence check: session_id={session_id}, user_id={user_id}, exists={count > 0}")
        return jsonify({'user_exists': count > 0})  
    except Exception as e:
        print(f"Error checking user existence: {e}")
        return jsonify({'user_exists': False}) 
    
@app.route('/chatbot')
def chatbot():
    """Chatbot interface for campus assistance"""
    return render_template('chatbot.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/get-user-data')
def get_user_data():
    if 'user_name' not in session:
        return jsonify({'error': 'User not logged in'}), 401
    
    # Get additional user data from database
    try:
        conn = sqlite3.connect('campus_navigation.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT name, role, login_time FROM users 
            WHERE session_id = ? 
            ORDER BY login_time DESC LIMIT 1
        ''', (session.get('session_id', ''),))
        
        user = c.fetchone()
        conn.close()
        
        if user:
            # Format the login time as member since
            login_time = datetime.datetime.strptime(user[2], '%Y-%m-%d %H:%M:%S')
            member_since = login_time.strftime('%B %Y')
            
            return jsonify({
                'name': user[0],
                'role': user[1],
                'member_since': member_since
            })
    
    except Exception as e:
        print(f"Error fetching user data: {e}")
    
    # Fallback to session data
    return jsonify({
        'name': session.get('user_name', 'User Name'),
        'role': session.get('user_role', 'User Role'),
        'member_since': 'Current Session'
    })

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/get-user-history')
def get_user_history():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401
    
    try:
        conn = sqlite3.connect('campus_navigation.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT COUNT(*) FROM user_activity 
            WHERE user_id = ?
        ''', (session.get('user_id'),))
        
        route_count = c.fetchone()[0]
        conn.close()
        
        return jsonify({
            'route_count': route_count
        })
    
    except Exception as e:
        print(f"Error fetching user history: {e}")
        return jsonify({'route_count': 0})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin/stats')
def admin_stats():
    try:
        conn = sqlite3.connect('campus_navigation.db')
        c = conn.cursor()
        
        # Get total users
        c.execute('SELECT COUNT(*) FROM users')
        total_users = c.fetchone()[0]
        
        # Get total routes calculated
        c.execute('SELECT COUNT(*) FROM user_activity')
        total_routes = c.fetchone()[0]
        
        # Get user distribution by role
        c.execute('SELECT role, COUNT(*) FROM users GROUP BY role')
        role_distribution = dict(c.fetchall())
        
        # Get recent activity
        c.execute('''
            SELECT u.name, u.role, ua.start_location, ua.end_location, ua.duration, ua.activity_time 
            FROM user_activity ua 
            JOIN users u ON ua.user_id = u.id 
            ORDER BY ua.activity_time DESC 
            LIMIT 10
        ''')
        recent_activity = []
        for row in c.fetchall():
            recent_activity.append({
                'name': row[0],
                'role': row[1],
                'start_location': row[2],
                'end_location': row[3],
                'duration': row[4],
                'activity_time': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'total_users': total_users,
            'total_routes': total_routes,
            'role_distribution': role_distribution,
            'recent_activity': recent_activity
        })
        
    except Exception as e:
        return jsonify({'error': f'Error fetching stats: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)