import sqlite3
import datetime
import threading
import calendar
from prettytable import PrettyTable 

db_lock = threading.Lock()

def adapt_date(date_obj):
    return date_obj.isoformat()

sqlite3.register_adapter(datetime.date, adapt_date)
# Making the connection
connection = sqlite3.connect('expenses.db')
cursor = connection.cursor()
# Creating my two tables
cursor.execute("CREATE TABLE IF NOT EXISTS Spending (date TEXT, location TEXT, amount REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS Paid (date TEXT, received TEXT, amount REAL)") 

def get_connection_and_cursor():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    return conn, cursor

# Function to close connection and cursor
def close_connection_and_cursor(conn):
    conn.commit()
    conn.close()

# Function to insert money spent 
def insert_spending():
    date = datetime.date.today()
    location = input("Enter where you spent money: ")
    amount = input("Enter how much you spent: ")
    values = (date, location, amount)
    
    with db_lock:
        conn, cursor = get_connection_and_cursor()
        cursor.execute("INSERT INTO Spending VALUES (?, ?, ?)", values)
        conn.commit()

        cursor.execute("SELECT * FROM Spending WHERE rowid = last_insert_rowid()")
        inserted_row = cursor.fetchone()
        print("Inserted Row: ")
        print(inserted_row)

        close_connection_and_cursor(conn)

# Function to insert income
def insert_income():
    date = datetime.date.today()
    location = input("Enter description of payment: ")
    amount = input("Enter how much you received: ")
    values = (date, location, amount)

    with db_lock:
        conn, cursor = get_connection_and_cursor()
        cursor.execute("INSERT INTO Paid VALUES (?, ?, ?)", values)
        conn.commit()

        cursor.execute("SELECT * FROM Paid WHERE rowid = last_insert_rowid()")
        inserted_row = cursor.fetchone()
        print("Inserted Row: ")
        print(inserted_row)

        close_connection_and_cursor(conn)

# Function to view the table
def view_table(table_name):
    with db_lock:
        conn, cursor = get_connection_and_cursor()

        query = f'SELECT * FROM {table_name}'
        cursor.execute(query)
        rows = cursor.fetchall()

        table = PrettyTable()
        table.field_names = [col[0] for col in cursor.description]

        query_sum = f'SELECT SUM(amount) FROM {table_name}'
        cursor.execute(query_sum)
        total_sum = cursor.fetchone()[0] or 0

        conn.close()
    
        for row in rows:
            table.add_row(row)
        print(table)
        print(f'Total Amount in {table_name}: {round(total_sum, 2)}')


# Function to view both tables
def view_both_tables():
    view_table('Spending')
    view_table('Paid')

# Functions to help clean up main
def choice_3():
    print("What would you like to view ")
    print(" 1. Spending")
    print(" 2. Income")
    print(" 3. View All")
    user_input = int(input("> "))

    if user_input == 1:
        view_table("Spending")
    elif user_input == 2:
        view_table("Paid")
    elif user_input == 3:
        view_both_tables()
    else:
        print("Invalid Input Try Again")

def delete_row(table_name):
    conn, cursor = get_connection_and_cursor()
    
    view_table(table_name)
    row_id = input("Enter the row ID you want to delete: ")

    try:
        row_id = int(row_id)
        cursor.execute(f"DELETE FROM {table_name} WHERE rowid=?", (row_id,))
        conn.commit()
        print(f"Row with ID {row_id} deleted successfully.")
    except ValueError:
        print("Invalid input. Row ID must be an integer.")

    close_connection_and_cursor(conn)

def choice_4():
    print("Which table would you like to edit: ")
    print(" 1. Spending")
    print(" 2. Income")
    user_input = int(input("> "))

    if user_input == 1:
        delete_row("Spending")
    elif user_input == 2:
        delete_row("Paid")
    else:
        print("Invalid input Try again")
        choice_4()

def choice_5():
    print("This is where you can view your expenses by the month!")
    print("Pick a month that you would like to look at: (1-12)")
    user_input_month = int(input("> "))

    view_table_by_month("Spending", user_input_month)

def view_table_by_month(table_name, month):
    conn, cursor = get_connection_and_cursor()

    query = f'SELECT * FROM {table_name} WHERE strftime("%m", date) = ?'
    cursor.execute(query, (str(month).zfill(2),))
    rows = cursor.fetchall()

    table = PrettyTable()
    table.field_names = [col[0] for col in cursor.description]

    query_sum = f'SELECT SUM(amount) FROM {table_name} WHERE strftime("%m", date) = ?'
    cursor.execute(query_sum, (str(month).zfill(2),))
    total_sum = cursor.fetchone()[0] or 0

    _, last_day = calendar.monthrange(datetime.date.today().year, month)
    total_days_in_month = last_day

    average_spent_per_day = total_sum / total_days_in_month

    conn.close()

    for row in rows:
        table.add_row(row)
    print(table)
    print(f'Total Amount in {table_name} for month {month}: {round(total_sum, 2)}')
    print(f'Average Spent per Day: {round(average_spent_per_day, 2)}')


def main():

    print("Welcome to the Expense Tracker!")
    income_thread = threading.Thread(target=insert_income)
    spending_thread = threading.Thread(target=insert_spending)

    while True:
        print("Enter the number of the task you would like to do: ")
        print(" 1. Insert Spending")
        print(" 2. Insert Income")
        print(" 3. View Expenses")
        print(" 4. Delete from Tables")
        print(" 5. Month Overview")
        print(" 6. Exit")

        user_input = int(input("> "))

        if user_input == 1:
            spending_thread.start()
            spending_thread.join()
        elif user_input == 2:
            income_thread.start()
            income_thread.join()
        elif user_input == 3:
            choice_3()
        elif user_input == 4:
            choice_4()
        elif user_input == 5:
            choice_5()
        elif user_input == 6:    
            break
        else:
            print("Invalid Input. Try Again")

    connection.close()

if __name__ == "__main__":
    main()