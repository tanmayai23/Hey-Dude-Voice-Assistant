import sqlite3

def add_application(name, path):
    """Add a new application to the database"""
    con = sqlite3.connect("HeyDude.db")
    cursor = con.cursor()
    
    try:
        query = "INSERT INTO sys_commands (name, path) VALUES (?, ?)"
        cursor.execute(query, (name, path))
        con.commit()
        print(f"✅ Successfully added: {name}")
    except sqlite3.IntegrityError:
        print(f"⚠️  '{name}' already exists in the database")
    except Exception as e:
        print(f"❌ Error adding {name}: {e}")
    finally:
        con.close()

def show_all_apps():
    """Display all applications in the database"""
    con = sqlite3.connect("HeyDude.db")
    cursor = con.cursor()
    
    cursor.execute("SELECT * FROM sys_commands ORDER BY name")
    results = cursor.fetchall()
    
    print("\n📋 All applications in database:")
    print("-" * 50)
    for row in results:
        print(f"ID: {row[0]}, Name: {row[1]}")
        print(f"    Path: {row[2]}\n")
    
    con.close()

if __name__ == "__main__":
    # Example: Add more applications here
    applications_to_add = [
        ("Visual Studio Code", "C:\\Users\\tanma\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"),
        ("Word", "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE"),
        ("Excel", "C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE"),
        ("PowerPoint", "C:\\Program Files\\Microsoft Office\\root\\Office16\\POWERPNT.EXE")
    ]
    
    for app_name, app_path in applications_to_add:
        add_application(app_name, app_path)
    
    # Show all applications
    show_all_apps()