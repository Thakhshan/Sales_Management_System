import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="sales_management_system"
)

if conn.is_connected():
    print("MySQL connection successful!")

conn.close()