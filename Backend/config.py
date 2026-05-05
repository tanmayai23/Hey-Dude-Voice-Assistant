ASSISTANT_NAME = "Hey Dude"

import sqlite3
import eel

DB_PATH = "HeyDude.db"

def _get_table_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def ensure_database_schema():
    """Ensure all tables/columns used by the UI and command handlers exist."""
    con = sqlite3.connect(DB_PATH)
    cursor = con.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS profile
                     (id INTEGER PRIMARY KEY, name TEXT, mobile TEXT, email TEXT, city TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sys_commands
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, path TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS web_commands
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, url TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS contacts
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, mobile TEXT, mobile_no TEXT, address TEXT, email TEXT)''')

    contact_columns = _get_table_columns(cursor, "contacts")
    if "mobile" not in contact_columns:
        cursor.execute("ALTER TABLE contacts ADD COLUMN mobile TEXT")
    if "mobile_no" not in contact_columns:
        cursor.execute("ALTER TABLE contacts ADD COLUMN mobile_no TEXT")
    if "address" not in contact_columns:
        cursor.execute("ALTER TABLE contacts ADD COLUMN address TEXT")
    if "email" not in contact_columns:
        cursor.execute("ALTER TABLE contacts ADD COLUMN email TEXT")

    # Keep both phone columns in sync so old WhatsApp logic (mobile_no)
    # and new settings UI (mobile) both work.
    cursor.execute("""
        UPDATE contacts
        SET
            mobile = COALESCE(NULLIF(TRIM(mobile), ''), NULLIF(TRIM(mobile_no), ''), ''),
            mobile_no = COALESCE(NULLIF(TRIM(mobile_no), ''), NULLIF(TRIM(mobile), ''), '')
        WHERE COALESCE(TRIM(mobile), '') = '' OR COALESCE(TRIM(mobile_no), '') = ''
    """)

    con.commit()
    con.close()


ensure_database_schema()

# ===== PROFILE MANAGEMENT =====

@eel.expose
def get_profile():
    """Get user profile from database"""
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        
        # Create profile table if doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS profile 
                         (id INTEGER PRIMARY KEY, name TEXT, mobile TEXT, email TEXT, city TEXT)''')
        
        cursor.execute("SELECT name, mobile, email, city FROM profile WHERE id=1")
        result = cursor.fetchone()
        con.close()
        
        if result:
            return {
                'name': result[0],
                'mobile': result[1],
                'email': result[2],
                'city': result[3]
            }
        return None
    except Exception as e:
        print(f"Error getting profile: {e}")
        return None

@eel.expose
def update_profile(profile):
    """Update user profile in database"""
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        
        # Create profile table if doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS profile 
                         (id INTEGER PRIMARY KEY, name TEXT, mobile TEXT, email TEXT, city TEXT)''')
        
        # Check if profile exists
        cursor.execute("SELECT id FROM profile WHERE id=1")
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("""UPDATE profile SET name=?, mobile=?, email=?, city=? WHERE id=1""",
                         (profile['name'], profile['mobile'], profile['email'], profile['city']))
        else:
            cursor.execute("""INSERT INTO profile (id, name, mobile, email, city) VALUES (1, ?, ?, ?, ?)""",
                         (profile['name'], profile['mobile'], profile['email'], profile['city']))
        
        con.commit()
        con.close()
        return {'success': True}
    except Exception as e:
        print(f"Error updating profile: {e}")
        return {'success': False, 'error': str(e)}

# ===== SYSTEM COMMANDS MANAGEMENT =====

@eel.expose
def get_system_commands():
    """Get all system commands"""
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        cursor.execute("SELECT id, name, path FROM sys_commands ORDER BY name")
        results = cursor.fetchall()
        con.close()
        
        commands = []
        for row in results:
            commands.append({
                'id': row[0],
                'name': row[1],
                'path': row[2]
            })
        return commands
    except Exception as e:
        print(f"Error getting system commands: {e}")
        return []

@eel.expose
def add_system_command(name, path):
    """Add a new system command"""
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        cursor.execute("INSERT INTO sys_commands (name, path) VALUES (?, ?)", (name.lower(), path))
        con.commit()
        con.close()
        return {'success': True}
    except sqlite3.IntegrityError:
        return {'success': False, 'error': 'Command already exists'}
    except Exception as e:
        print(f"Error adding system command: {e}")
        return {'success': False, 'error': str(e)}

@eel.expose
def delete_system_command(cmd_id):
    """Delete a system command"""
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        cursor.execute("DELETE FROM sys_commands WHERE id=?", (cmd_id,))
        con.commit()
        con.close()
        return {'success': True}
    except Exception as e:
        print(f"Error deleting system command: {e}")
        return {'success': False, 'error': str(e)}

# ===== WEB COMMANDS MANAGEMENT =====

@eel.expose
def get_web_commands():
    """Get all web commands"""
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        cursor.execute("SELECT id, name, url FROM web_commands ORDER BY name")
        results = cursor.fetchall()
        con.close()
        
        commands = []
        for row in results:
            commands.append({
                'id': row[0],
                'name': row[1],
                'url': row[2]
            })
        return commands
    except Exception as e:
        print(f"Error getting web commands: {e}")
        return []

@eel.expose
def add_web_command(name, url):
    """Add a new web command"""
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        cursor.execute("INSERT INTO web_commands (name, url) VALUES (?, ?)", (name.lower(), url))
        con.commit()
        con.close()
        return {'success': True}
    except sqlite3.IntegrityError:
        return {'success': False, 'error': 'Command already exists'}
    except Exception as e:
        print(f"Error adding web command: {e}")
        return {'success': False, 'error': str(e)}

@eel.expose
def delete_web_command(cmd_id):
    """Delete a web command"""
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        cursor.execute("DELETE FROM web_commands WHERE id=?", (cmd_id,))
        con.commit()
        con.close()
        return {'success': True}
    except Exception as e:
        print(f"Error deleting web command: {e}")
        return {'success': False, 'error': str(e)}

# ===== CONTACTS MANAGEMENT =====

@eel.expose
def get_contacts():
    """Get all contacts"""
    try:
        ensure_database_schema()
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                COALESCE(NULLIF(TRIM(mobile), ''), NULLIF(TRIM(mobile_no), ''), '') AS mobile,
                COALESCE(address, '') AS address
            FROM contacts
            ORDER BY name
        """)
        results = cursor.fetchall()
        con.close()
        
        contacts = []
        for row in results:
            contacts.append({
                'id': row[0],
                'name': row[1],
                'mobile': row[2],
                'address': row[3]
            })
        return contacts
    except Exception as e:
        print(f"Error getting contacts: {e}")
        return []

@eel.expose
def add_contact(name, mobile, address=''):
    """Add a new contact"""
    try:
        ensure_database_schema()
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()

        clean_mobile = mobile.strip() if mobile else ''
        cursor.execute(
            "INSERT INTO contacts (name, mobile, mobile_no, address) VALUES (?, ?, ?, ?)",
            (name, clean_mobile, clean_mobile, address),
        )
        con.commit()
        con.close()
        return {'success': True}
    except Exception as e:
        print(f"Error adding contact: {e}")
        return {'success': False, 'error': str(e)}

@eel.expose
def delete_contact(contact_id):
    """Delete a contact"""
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        cursor.execute("DELETE FROM contacts WHERE id=?", (contact_id,))
        con.commit()
        con.close()
        return {'success': True}
    except Exception as e:
        print(f"Error deleting contact: {e}")
        return {'success': False, 'error': str(e)}
