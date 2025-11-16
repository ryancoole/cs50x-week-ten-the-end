# CS50x - Week 10: The End

# ReadTrack
#### Video Demo: <URL HERE>
#### Description

ReadTrack is a simple, focused web application that helps users keep track of the books they’re reading. It acts as a lightweight personal reading log, not a social network or recommendation engine, just a clean way to record what you’re reading, what you’ve finished, and what you want to get to next.

The app is built with **Flask**, **SQLite**, **Python**, **HTML/CSS**, and **Bootstrap**. It uses standard Flask patterns (routing, templates, sessions), SQL for persistent storage, and basic CRUD operations to manage a user’s reading list.

---

## 🎯 Features

### ✔ Add Books
Users can add a book with:
- Title  
- Author  
- Page Count (optional)

### ✔ Update Books
Any book can be updated with adding a page number to show progress or adding a rating and review after finishing.

### ✔ Stats
Statistics show how many books have been added, total pages logged and reviews added.

### ✔ Persistent Storage
All data is stored in `readtrack.db` using a single normalized table:
