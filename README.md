# Approved Shoes

**Approved Shoes** is an app currently in development, designed to support **track and field officials** in verifying footwear regulations with speed and ease.  

## 📌 Overview
Track and field officials often need to check whether a shoe model is approved for specific events. Traditionally, this requires consulting websites or lengthy PDF lists, a process that can be slow and inefficient during competitions.  

Approved Shoes solves this by providing:
- ⚡ **Instant responses** on shoe eligibility  
- 🎯 **Simple and fast interface** for quick checks  
- 🏟️ **Field-ready tool** to make officials’ work more efficient  

## 🚀 Functionality
The mobile app, instead, uses a non-relational JSON file as a DataBase to handle data queries. JSON was chosen over a database because the dataset is relatively small and doesn’t require complex queries. This choice was made for simplicity (easy to read and edit), portability, speed and flexibility. For larger datasets or more advanced queries, a relational database (e.g., SQLite) would be more suitable.

The Python interface, instead, is built on an SQLite database, which is queried instantly when the user makes a selection from the drop-down menu. This choice was made to try both possibilities.

## 🛠️ Tech Info
SwiftUI - App currently limited to Apple devices.
JSON – Non-relational format for lightweight data retrieval
