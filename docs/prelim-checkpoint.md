## Developer Information

Name: Paule Kenneth D. Dela Rosa
GitHub Username:  KennethTheCode 
Primary Technology Stack: Python, Flask, SQLite
T03 Branch: feature/t03-resident-persistence  

## My T03 Implementation

For T03, I saved Resident data in a real SQLite database file instead of just keeping it in memory or using a Python list or dictionary. All of this is handled by a class called ResidentRepository, which takes care of saving and finding Residents. When I call save(), it connects to the database, runs an INSERT command with the Resident's info (name, address, contact number, email, and status), and saves it. I don't have to make up an ID myself — SQLite automatically creates one because I set up the id column to auto-increment. After saving, I grab that new ID using cursor.lastrowid and attach it to the Resident object so I can use it later. When I call find_by_id(), it looks up the Resident using their ID and turns the database row back into a normal Resident object I can work with. If the ID doesn't exist, it just returns None instead of crashing or making up fake data.

## My Persistence Design Decision

One choice I made was to put my database setup code in its own file, database.py, instead of putting it inside the repository folder. I did this because setting up the database felt like something the whole app needs, not just something related to Residents specifically. I did think about just putting it next to resident_repository.py since that's the only thing using the database right now, but I figured keeping it separate would make more sense later if the project needs to store other kinds of data too.

## Files I Changed
File: csms/database.py
Purpose: Sets up the connection to the SQLite database and creates the residents table if it doesn't already exist.

File: csms/repositories/resident_repository.py
Purpose: Contains the ResidentRepository class with the save() and find_by_id() methods that actually store and retrieve Resident data.

File: tests/test_resident_repository.py
Purpose: Contains the 7 required persistence tests plus my own student-designed test, all using a temporary database so they don't touch the real dev database.

## Problem I Encountered

Problem or error: I got a syntax error when trying to create the residents table.

Cause: I wrote my CREATE TABLE SQL statement directly inside cursor.execute() without wrapping it in quotes, so Python tried to read the SQL keywords as if they were Python code instead of treating them as one string.

How I resolved it: I put the whole SQL statement inside triple quotes so it was passed to cursor.execute() as a proper string, which fixed the error and let the table get created correctly.

## My Student-Designed Test

Test name: test_multiple_residents_receive_different_ids

What it verifies: This test saves two different Residents through the same repository and checks that they end up with different IDs instead of somehow getting the same one.

Why I chose this scenario: None of the seven required tests actually save more than one Resident at a time, so I felt like this was a gap worth covering myself. If there were ever a bug in how IDs get generated or read from cursor.lastrowid, saving just one Resident wouldn't catch it — but saving two and comparing their IDs would.

If you ended up naming your test something different when you actually wrote it, swap in your real test name here so it matches your code exactly — that consistency is something you might get asked about directly.

## Tools and References Used

Visual Studio Code — used to write, edit, and organize my project files.

Claude — used as a coding assistant. It didn't write my implementation for me; instead it gave me skeleton code with blanks I had to fill in myself, reviewed what I wrote, and pointed out mistakes, like the cursor.execute() syntax error I ran into with my CREATE TABLE statement. It also helped me understand why certain things had to be done a specific way, such as why contact_number needs to be stored as TEXT instead of a number, how cursor.lastrowid works for getting the auto-generated ID, and how sqlite3.Row lets me access database columns by name when rebuilding a Resident object from a database row.