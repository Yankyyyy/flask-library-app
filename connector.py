from flask import Flask
import mysql.connector

app = Flask(__name__)

config = {
  'host': 'localhost',
  'user': 'root',
  'password': 'Yanky-007',
  'database': 'library'
}

@app.route('/')
def connect_to_database():
  """Connects to the MySQL database."""
  try:
    connection = mysql.connector.connect(**config)
    my_cursor = connection.cursor()
    my_cursor.execute('SHOW TABLES')
    for table in my_cursor:
      print(table)
    return "Done"
  except mysql.connector.Error as err:
    print("Error connecting to database:", err)
    return "Error"



if __name__ == '__main__':
   app.run(debug = True)