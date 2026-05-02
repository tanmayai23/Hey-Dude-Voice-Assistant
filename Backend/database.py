import sqlite3
import csv
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

con = sqlite3.connect("HeyDude.db")
cursor = con.cursor()

# Drop the old tables and create new ones with UNIQUE constraint
cursor.execute("DROP TABLE IF EXISTS sys_commands")
cursor.execute("DROP TABLE IF EXISTS web_commands")

# Create sys_commands table for desktop applications
query = "CREATE TABLE sys_commands(id integer primary key , name VARCHAR(100) UNIQUE,path VARCHAR(1000))"
cursor.execute(query)

# Create web_commands table for web applications
query = "CREATE TABLE web_commands(id integer primary key , name VARCHAR(100) UNIQUE, url VARCHAR(1000))"
cursor.execute(query)

# Insert desktop applications
applications = [
    ('android studio', 'C:\\Program Files\\Android\\Android Studio\\bin\\studio64.exe'),
    ('OneNote', 'C:\\Program Files\\Microsoft Office\\root\\Office16\\ONENOTE.EXE'),
    ('notepad', 'notepad.exe'),
    ('chrome', 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'),
    ('calculator', 'calc.exe')
]

print("Adding Desktop Applications:")
print("-" * 40)
for app_name, app_path in applications:
    try:
        query = "INSERT INTO sys_commands (name,path) VALUES (?, ?)"
        cursor.execute(query, (app_name, app_path))
        print(f"✅ Added: {app_name}")
    except sqlite3.IntegrityError:
        print(f"⚠️  Skipped: {app_name} (already exists)")

# Insert web applications with URLs
web_applications = [
    ('youtube', 'https://www.youtube.com/'),
    ('fast', 'https://fast.com/'),
    ('gemini', 'https://gemini.google.com/app'),
    ('chatgpt', 'https://chatgpt.com/'),
    ('perplexity', 'https://www.perplexity.ai/'),
    ('google ai studio', 'https://aistudio.google.com/prompts/new_chat'),
    ('amazon', 'https://www.amazon.in/'),
    ('flipkart', 'https://www.flipkart.com/'),
    ('canva', 'https://www.canva.com/'),
    ('google', 'https://www.google.com/'),
    ('instagram', 'https://www.instagram.com/'),
    # Additional important websites
    ('facebook', 'https://www.facebook.com/'),
    ('twitter', 'https://www.twitter.com/'),
    ('linkedin', 'https://www.linkedin.com/'),
    ('github', 'https://www.github.com/'),
    ('stackoverflow', 'https://stackoverflow.com/'),
    ('reddit', 'https://www.reddit.com/'),
    ('netflix', 'https://www.netflix.com/'),
    ('spotify web', 'https://open.spotify.com/'),
    ('whatsapp web', 'https://web.whatsapp.com/'),
    ('gmail', 'https://mail.google.com/'),
    ('outlook', 'https://outlook.live.com/'),
    ('drive', 'https://drive.google.com/'),
    ('onedrive', 'https://onedrive.live.com/'),
    ('dropbox', 'https://www.dropbox.com/'),
    ('discord', 'https://discord.com/'),
    ('slack', 'https://slack.com/'),
    ('zoom', 'https://zoom.us/'),
    ('microsoft teams', 'https://teams.microsoft.com/'),
    ('notion', 'https://www.notion.so/'),
    ('trello', 'https://trello.com/'),
    ('figma', 'https://www.figma.com/'),
    ('codecademy', 'https://www.codecademy.com/'),
    ('coursera', 'https://www.coursera.org/'),
    ('khan academy', 'https://www.khanacademy.org/'),
    ('wikipedia', 'https://www.wikipedia.org/'),
    ('weather', 'https://weather.com/'),
    ('maps', 'https://maps.google.com/')
]

print("\nAdding Web Applications:")
print("-" * 40)
for web_name, web_url in web_applications:
    try:
        query = "INSERT INTO web_commands (name, url) VALUES (?, ?)"
        cursor.execute(query, (web_name, web_url))
        print(f"🌐 Added: {web_name}")
    except sqlite3.IntegrityError:
        print(f"⚠️  Skipped: {web_name} (already exists)")

#conn.commit is used for save the database
con.commit()
print("\n" + "="*50)
print("DATABASE UPDATED SUCCESSFULLY!")
print("="*50)

# Show what's in both databases
print("\n📋 DESKTOP APPLICATIONS (sys_commands):")
print("-" * 60)
cursor.execute("SELECT * FROM sys_commands ORDER BY name")
results = cursor.fetchall()
for row in results:
    print(f"ID: {row[0]}, Name: {row[1]}")
    print(f"    Path: {row[2]}\n")

print("🌐 WEB APPLICATIONS (web_commands):")
print("-" * 60)
cursor.execute("SELECT * FROM web_commands ORDER BY name")
results = cursor.fetchall()
for row in results:
    print(f"ID: {row[0]}, Name: {row[1]}")
    print(f"    URL: {row[2]}\n")

print(f"📊 Total Desktop Apps: {len(applications)}")
cursor.execute("SELECT COUNT(*) FROM web_commands")
web_count = cursor.fetchone()[0]
print(f"📊 Total Web Apps: {web_count}")

# Create contacts table for WhatsApp automation
print("\n" + "="*50)
print("SETTING UP CONTACTS DATABASE")
print("="*50)

cursor.execute("DROP TABLE IF EXISTS contacts")
cursor.execute('''CREATE TABLE IF NOT EXISTS contacts(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    name VARCHAR(200), 
    mobile_no VARCHAR(255), 
    email VARCHAR(255) NULL
)''')

# Import contacts from CSV
print("\nImporting contacts from contacts.csv...")
print("-" * 60)
try:
    # CSV columns: First Name (0), Middle Name (1), Last Name (2), ... Phone 1 - Value (22)
    contacts_added = 0
    contacts_skipped = 0
    
    with open('contacts.csv', 'r', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader, None)  # Skip header line
        
        for row in csvreader:
            try:
                if len(row) > 22:  # Make sure row has phone number column
                    # Extract name (combine first, middle, last name)
                    first_name = row[0].strip() if row[0] else ""
                    middle_name = row[1].strip() if row[1] else ""
                    last_name = row[2].strip() if row[2] else ""
                    
                    # Combine name parts
                    name_parts = [first_name, middle_name, last_name]
                    full_name = " ".join([part for part in name_parts if part])
                    
                    # Extract phone number (column 22 - Phone 1 - Value)
                    phone_number = row[22].strip() if row[22] else ""
                    
                    # Clean phone number - remove spaces, dashes, +91, ::: separators
                    if phone_number:
                        # If multiple numbers separated by :::, take the first one
                        if ':::' in phone_number:
                            phone_number = phone_number.split(':::')[0].strip()
                        
                        # Remove common formatting characters
                        phone_number = phone_number.replace('+91', '').replace('+', '').replace('-', '').replace(' ', '')
                        
                        # Only add if we have both name and phone
                        if full_name and phone_number and phone_number.isdigit():
                            cursor.execute('''INSERT INTO contacts (name, mobile_no) VALUES (?, ?)''', (full_name, phone_number))
                            contacts_added += 1
                            if contacts_added <= 10:  # Show first 10 as examples
                                print(f"✅ Added: {full_name} - {phone_number}")
                        else:
                            contacts_skipped += 1
                    else:
                        contacts_skipped += 1
                        
            except Exception as e:
                contacts_skipped += 1
                continue
    
    print(f"... (showing first 10)")
    print(f"\n📊 Total Contacts Added: {contacts_added}")
    print(f"⚠️  Skipped (no phone/invalid): {contacts_skipped}")
    
except FileNotFoundError:
    print("⚠️  contacts.csv not found. Skipping contact import.")
    print("   Create contacts.csv with proper format")
except Exception as e:
    print(f"❌ Error importing contacts: {e}")

print("\n📋 CONTACTS IN DATABASE:")
print("-" * 60)
cursor.execute("SELECT * FROM contacts ORDER BY name LIMIT 20")
contacts = cursor.fetchall()
for contact in contacts:
    print(f"✅ {contact[1]} - {contact[2]}")

cursor.execute("SELECT COUNT(*) FROM contacts")
total_contacts = cursor.fetchone()[0]
print(f"... (showing first 20)")
print(f"\n📊 Total Contacts in Database: {total_contacts}")

con.commit()
con.close()

print("\n" + "="*50)
print("ALL DATABASES SETUP COMPLETE!")
print("="*50)