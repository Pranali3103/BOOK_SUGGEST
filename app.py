from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from pymongo import MongoClient
import pickle
import numpy as np
import pandas as pd
app = Flask(__name__)
app.secret_key = ''  # Replace with a strong secret key
CORS(app)
bcrypt = Bcrypt(app)

    # Load data and initialize MongoDB Atlas connection (you can replace this with your own data loading and database connection)

popular_df = pickle.load(open('popular.pkl', 'rb'))
pt = pickle.load(open('pt.pkl', 'rb'))
books = pickle.load(open('books.pkl', 'rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))



genre = pickle.load(open('genre.pkl', 'rb'))

genre_with_name= pickle.load(open('genre_with_name.pkl', 'rb'))


    # Initialize MongoDB Atlas connection (you can replace this with your own MongoDB connection)
client = MongoClient('')#mongodb link
db = client['FLASK-05']
users_collection = db['users']

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username']
        password = request.form['password']

            # Check if the provided username or email exists in the MongoDB collection
        user = users_collection.find_one({'$or': [{'username': username_or_email}, {'email': username_or_email}]})

        if user and bcrypt.check_password_hash(user['password'], password):
                # Successfully logged in
            flash('Login successful!', 'success')
                # Call the JavaScript function to show the success message
            return render_template('login.html', success=True)

        else:
            flash('Invalid username/email or password. Please try again.', 'danger')

    return render_template('login.html', success=False)



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']

        existing_user = users_collection.find_one({'email': email})

        if existing_user:
            flash('Email already exists. Please use another email.', 'danger')
        else:
            try:
                    # Hash the password before storing it in the database
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

                    # Create a new user document and insert it into the MongoDB collection
                new_user = {
                        'password': hashed_password,
                        'firstName': first_name,
                        'lastName': last_name,
                        'email': email
                    }
                users_collection.insert_one(new_user)
                flash('Signup successful! You can now log in.', 'success')
                return redirect(url_for('login'))  # Redirect to the login page on successful signup
            except Exception as e:
                flash(f'Signup failed. Error: {str(e)}', 'danger')

    return render_template('signup.html')



@app.route('/',methods=['GET'])
def index():
    return render_template('index.html',
                               book_name = list(popular_df['Book-Title'].values),
                               author=list(popular_df['Book-Author'].values),
                               image=list(popular_df['Image-URL-M'].values),
                               votes=list(popular_df['num_ratings'].values),
                               rating=list(popular_df['avg_rating'].values)
                               )

@app.route('/recommend',methods=['GET'])
def recommend_ui():
    return render_template('recommend.html')

@app.route('/recommend_books',methods=['post'])
def recommend():
        user_input = request.form.get('user_input')
        index = np.where(pt.index == user_input)[0][0]
        similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]

        data = []
        for i in similar_items:
            item = []
            temp_df = books[books['Book-Title'] == pt.index[i[0]]]
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

            data.append(item)

        print(data)

        return render_template('recommend.html',data=data)

    # --->Genrestart
genre_data = pd.read_csv('Genre.csv')

def get_books_by_genre(genre_name):
        # Filter books by the specified genre
        genre_books = genre_data[genre_data['Genre'] == genre_name]

        # Extract the relevant columns (Title, Author, Image) for the specified genre
        selected_columns = ['Book-Title', 'Book-Author', 'Image-URL-M']
        genre_books_info = genre_books[selected_columns]

        # Convert the filtered data to a list of dictionaries
        genre_books_list = genre_books_info.to_dict(orient='records')

        return genre_books_list

@app.route('/recommend_genre', methods=['POST', 'GET'])
def recommend_genre():
        genre_name = request.form.get('genre')
        genre_books = get_books_by_genre(genre_name)
        return render_template('recommend_genre.html', genre_books=genre_books)



if __name__ == '__main__':
        app.run(host='0.0.0.0', debug=True)


    # GenreEnd

    # def recommend_genre(genre_name):
    #     # Filter books by the specified genre
    #     genre_books = genre_with_name[genre_with_name['Genre'] == genre_name]
    #
    #     # Create a list of book titles in the specified genre
    #     genre_book_titles = genre_books['Book-Title'].tolist()
    #
    #     recommended_books = []
    #
    #     for book_title in genre_book_titles:
    #         # Check if the book is in the user-item ratings matrix
    #         if book_title in pt.index:
    #             # Get recommendations for books in the specified genre
    #             recommendations = recommend(book_title)
    #             recommended_books.extend(recommendations)
    #
    #     return render_template('recommend.html',recommended_books=recommend)


    # @app.route('/recommend_books', methods=['POST'])
    # def recommend_books():
    #     if request.method == 'POST':
    #         user_input = request.form.get('user_input')
    #         search_type = request.form.get('search_type')
    #
    #         if search_type == "book_title":
    #             # The input is a book title, get book recommendations
    #             book_recommendations = recommend(user_input)
    #             return render_template('recommend.html', data=book_recommendations)
    #         elif search_type == "genre":
    #             # The input is a genre, get genre-based recommendations
    #             genre_recommendations = recommend_genre(user_input)  # Implement this function
    #             return render_template('recommend.html', data=genre_recommendations)
    #         else:
    #             flash('Invalid search type. Please try again.', 'danger')

    # @app.route('/recommend_books', methods=['POST'])
    # def recommend_books():
    #     if request.method == 'POST':
    #         user_input = request.form.get('user_input')
    #         search_type = request.form.get('search_type')
    #
    #         if search_type == "book_title":
    #             # The input is a book title, get book recommendations
    #             book_recommendations = recommend(user_input)
    #             return render_template('recommend.html', data=book_recommendations)
    #         elif search_type == "genre":
    #             # The input is a genre, get genre-based recommendations
    #             genre_recommendations = recommend_genre(user_input)  # Implement this function
    #             return render_template('recommend.html', data=genre_recommendations)
    #         else:
    #             flash('Invalid search type. Please try again.', 'danger')

# from flask import Flask,render_template,request
# import pickle
# import numpy as np
#
# popular_df = pickle.load(open('popular.pkl','rb'))
# pt = pickle.load(open('pt.pkl','rb'))
# books = pickle.load(open('books.pkl','rb'))
# similarity_scores = pickle.load(open('similarity_scores.pkl','rb'))
#
# app = Flask(__name__)
#
# @app.route('/')
# def index():
#     return render_template('index.html',
#                            book_name = list(popular_df['Book-Title'].values),
#                            author=list(popular_df['Book-Author'].values),
#                            image=list(popular_df['Image-URL-M'].values),
#                            votes=list(popular_df['num_ratings'].values),
#                            rating=list(popular_df['avg_rating'].values)
#                            )
#
# @app.route('/recommend')
# def recommend_ui():
#     return render_template('recommend.html')
#
# @app.route('/recommend_books',methods=['post'])
# def recommend():
#     user_input = request.form.get('user_input')
#     index = np.where(pt.index == user_input)[0][0]
#     similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]
#
#     data = []
#     for i in similar_items:
#         item = []
#         temp_df = books[books['Book-Title'] == pt.index[i[0]]]
#         item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
#         item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
#         item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))
#
#         data.append(item)
#
#     print(data)
#
#     return render_template('recommend.html',data=data)
#
# if __name__ == '__main__':
#     app.run(debug=True)