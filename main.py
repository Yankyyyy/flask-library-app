from flask import Flask, request, jsonify
import mysql.connector
from functools import wraps
import jwt

app = Flask(__name__)
app.name = "Library Management"  # Set application name


SECRET_KEY = "6379573186"

@app.route('/login', methods=['POST'])
def login():
  data = request.get_json()
  username = data.get('username')
  password = data.get('password')
  # Validate credentials 
  if username == 'admin' and password == 'admin@123':
    payload = {'username': username}
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return jsonify({'token': token})
  else:
    return jsonify({'error': 'Invalid credentials'}), 401

def token_required(func):
  @wraps(func)
  def decorated(*args, **kwargs):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
      return jsonify({'error': 'Missing or invalid token'}), 401

    token = auth_header.split()[1]
    
    try:
      payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
      return func(*args, **kwargs)
    except:
      return jsonify({'message' : 'Token is invalid !!'}), 401
    
  return decorated



# Simple home just for checking error
@app.route('/')
def home():
   return "Library Management App"


# Database connection details
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Yanky-007',
    'database': 'library'
}

def connect_to_database():
  """Connects to the MySQL database."""
  try:
    connection = mysql.connector.connect(**config)
    return connection
  except mysql.connector.Error as err:
    print("Error connecting to database:", err)
    return None


@app.route('/books', methods=['POST'])
@token_required
def add_book():
  """Adds a new book to the database."""
  # Get book details from request body
  data = request.get_json()
  id = data.get('id')
  title = data.get('title')
  author = data.get('author')
  genre = data.get('genre')
  published_year = data.get('published_year')

  # Validate input data
  if not all([id, title, author, genre, published_year]):
    return jsonify({'error': 'Missing required fields'}), 400

  # Connect to database
  connection = connect_to_database()
  if not connection:
    return jsonify({'error': 'Database connection error'}), 500
  cursor = connection.cursor()

  # Insert book details
  sql = """INSERT INTO books (id, title, author, genre, published_year) VALUES (%s, %s, %s, %s, %s)"""
  try:
    cursor.execute(sql, (id, title, author, genre, published_year))
    connection.commit()
  except mysql.connector.Error as err:
    connection.rollback()
    print("Error inserting book:", err)
    return jsonify({'error': 'Error adding book'}), 500

  connection.close()
  return jsonify({'message': 'Book added successfully!'}), 201


@app.route('/books', methods=['GET'])
@token_required
def get_books():
  """Retrieves books from the database with optional filtering."""
  # Get query parameters for filtering
  data = request.get_json()
  title = data.get('title')
  author = data.get('author')
  genre = data.get('genre')

  # Connect to database
  connection = connect_to_database()
  if not connection:
    return jsonify({'error': 'Database connection error'}), 500
  cursor = connection.cursor()

  filters = {}  # Dictionary to store filter criteria

  # Populate the filters dictionary with extracted parameters (if they have values)
  filters['title'] = title if title else None  # Store title filter if it exists
  filters['author'] = author if author else None  # Store author filter if it exists
  filters['genre'] = genre if genre else None  # Store genre filter if it exists


  params = []
  where_clause = ""
  for field, value in filters.items():
    if value:  # Check if value exists before adding to query
      where_clause += f" AND {field} LIKE %s"
      params.append(f"%{value}%")

  if where_clause:
    sql = f"""
    SELECT *
    FROM books
    WHERE 1 = 1 {where_clause}
    ORDER BY id;
    """
  else:
    # Handle case where no filters are provided (optional)
    sql = "SELECT * FROM books ORDER BY id;"

  cursor.execute(sql, params)
  books = cursor.fetchall()

  connection.close()

  # Return book data or 'not found' message
  return jsonify(books) if books else jsonify({'message': 'No books found'}), 404

  # Build query with filtering criteria (if provided)
  # if title:
    # sql = """SELECT *
    #         FROM books
    #         WHERE (title LIKE %s OR COALESCE(title, '') = '')
    #           AND (author LIKE %s OR COALESCE(author, '') = '')
    #           AND (genre LIKE %s OR COALESCE(genre, '') = '')
    #         ORDER BY id;
    #       """
    
    # params = [f"%{title}%", f"%{author}%", f"%{genre}%"]

    # cursor.execute(sql, params)

    # Fetch book data
    # books = cursor.fetchall()
    # connection.close()
  # else:
    # sql = "SELECT * FROM books"

    # cursor.execute(sql)
    # Fetch book data
    # books = cursor.fetchall()
    # connection.close()

@app.route('/books/book_by_id', methods=['GET', 'PUT', 'DELETE'])
@token_required
def book_by_id():
  """Handles requests for a specific book based on ID."""
  # Connect to database
  connection = connect_to_database()
  if not connection:
    return jsonify({'error': 'Database connection error'}), 500
  cursor = connection.cursor()

  # Get book id from request body
  data = request.get_json()
  book_id = data.get('id')

  # GET request - retrieve book details
  if request.method == 'GET':
    sql = "SELECT * FROM books WHERE id = %s"
    cursor.execute(sql, (book_id,))
    book = cursor.fetchone()
        # Check if book exists
    if not book:
      return jsonify({'message': 'Book not found'}), 404

    # Convert book data to dictionary (optional, can be customized)
    book_data = {
      'id': book[0],
      'title': book[1],
      'author': book[2],
      'genre': book[3],
      'published_year': book[4]
    }

    connection.close()
    return jsonify(book)
  
  # Handle PUT request - update book details
  if request.method == 'PUT':
    # Get updated book details from request body
    data = request.get_json()
    update_fields = {}
    if data.get('title'):
      update_fields['title'] = data['title']
    if data.get('author'):
      update_fields['author'] = data['author']
    if data.get('genre'):
      update_fields['genre'] = data['genre']
    if data.get('published_year'):
      update_fields['published_year'] = data['published_year']

    # Validate that at least one field is provided for update
    if not update_fields:
      connection.close()
      return jsonify({'error': 'No fields provided for update'}), 400

    # Construct update query
    set_clause = ', '.join([f"{field} = %({field})s" for field in update_fields])
    query = f"UPDATE books SET {set_clause} WHERE id = {book_id}"
    params = {**update_fields}

    # Execute update query
    cursor.execute(query, params)
    connection.commit()
    connection.close()

    return jsonify({'message': 'Book updated successfully!'}), 200

  # Handle DELETE request - delete book
  elif request.method == 'DELETE':
    # Construct delete query
    sql = "DELETE FROM books WHERE id = %s"

    # Execute delete query
    cursor.execute(sql, (book_id,))
    connection.commit()
    connection.close()

    return jsonify({'message': 'Book deleted successfully!'}), 200


@app.route('/books/aggregate', methods=['GET'])
@token_required
def get_aggregate_data():
  """Retrieves aggregated data from the books table."""
  connection = connect_to_database()
  if not connection:
    return jsonify({'error': 'Database connection error'}), 500
  cursor = connection.cursor()

  # Construct query for book count by genre
  query = "SELECT genre, COUNT(*) AS count FROM books GROUP BY genre"
  cursor.execute(query)
  results = cursor.fetchall()
  connection.close()

  # Return aggregated data
  return jsonify([{'genre': result[0], 'count': result[1]} for result in results])


if __name__ == '__main__':
  app.run(debug=True)