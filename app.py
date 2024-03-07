from shutil import move
from spin_sdk.http import IncomingHandler, Request, Response
from spin_sdk import sqlite
from spin_sdk.sqlite import ValueText, ValueInteger
from urllib.parse import ParseResult, urlparse, parse_qs
from http_router import Router, exceptions
import json
import numpy as np


router = Router(trim_last_slash=True)

@router.route("/")
def handle_index(uri: ParseResult, request: Request) -> Response:
    # Basic response for a basic request
    return Response(200, {"content-type": "text/plain"}, b"Hello World")

@router.route('/add_movie', methods=['POST'])
def add_movie(uri: ParseResult, request: Request):
    try:
        data = json.loads(request.body)
        with sqlite.open_default() as db:
        # Insert movie into the database
            db.execute('''
                INSERT INTO movies (title, genre) 
                VALUES (?, ?)
            ''', [ValueText(data['title']), ValueText(data['genre'])])

        return Response(200, {"content-type": "text/plain"}, b"Movie added successfully")

    except Exception as e:
        return Response(500, {"content-type": "text/plain"}, bytes(f"error {e}", "utf-8"))
    
@router.route('/add_rating', methods=['POST'])
def add_rating(uri: ParseResult, request: Request):
    try:
        data = json.loads(request.body)
        # Insert rating into the database
        with sqlite.open_default() as db:
            db.execute('''
                INSERT INTO ratings (movie_id, user_id, rating) 
                VALUES (?, ?, ?)
            ''', [ValueInteger(data['movie_id']), ValueInteger(data['user_id']), ValueInteger(data['rating'])])

        return Response(200, {"content-type": "text/plain"}, b"Rating added successfully")

    except Exception as e:
        return Response(500, {"content-type": "text/plain"}, bytes(f"error {e}", "utf-8"))

@router.route('/calculate_movie_ratings', methods=['GET'])
def calculate_movie_ratings(uri: ParseResult, request: Request):
    try:
        params = parse_qs(uri.query)
        movie_id = int(params["movie_id"][0])
        # Retrieve ratings for a specific movie from the database
        with sqlite.open_default() as db:
            data = db.execute('SELECT rating FROM ratings WHERE movie_id = ?', [ValueInteger(movie_id)])
    
        if not data.rows:
            return Response(404, {"content-type": "text/plain"}, b"No ratings available for the movie")
    
        values = [result.values[0].value for result in data.rows]

        # Convert the values to a NumPy array
        ratings = np.array(values)
        average_rating = np.mean(ratings)

        # Calculate highest and lowest ratings
        highest_rating = np.max(ratings)
        lowest_rating = np.min(ratings)

        # Calculate standard deviation of ratings
        rating_std_dev = np.std(ratings)

        result = {
            'movie_id': movie_id,
            'average_rating': average_rating,
            'highest_rating': highest_rating,
            'lowest_rating': lowest_rating,
            'rating_std_dev': rating_std_dev
        }

        return Response(200, {"content-type": "text/plain"}, bytes(json.dumps(result, default=custom_encoder), "utf-8"))

    except Exception as e:
        return Response(500, {"content-type": "text/plain"}, bytes(f"error {e}", "utf-8"))


@router.route('/movie_recommendations', methods=['GET'])
def movie_recommendations(uri: ParseResult, request: Request):
    try:
        params = parse_qs(uri.query)
        user_id = int(params["user_id"][0])

        # Fetch all ratings from the database
        with sqlite.open_default() as db:
            all_ratings_data = db.execute('SELECT movie_id, user_id, rating FROM ratings', []).rows

        if not all_ratings_data:
            return Response(404, {"content-type": "text/plain"}, b"No ratings available")

        values = [(row.values[0].value, row.values[1].value, row.values[2].value) for row in all_ratings_data]

        # Convert the values to a NumPy array
        all_ratings = np.array(values)

        # Create dictionaries to map movie and user IDs to matrix indices
        movie_to_index = {movie_id: idx for idx, movie_id in enumerate(np.unique(all_ratings[:, 0]))}
        user_to_index = {user_id: idx for idx, user_id in enumerate(np.unique(all_ratings[:, 1]))}

        # Get the number of unique movies and users from the dictionaries
        num_movies = len(movie_to_index)
        num_users = len(user_to_index)

        # Generate a dynamic movie-user matrix
        movie_user_matrix = np.zeros((num_movies, num_users))
        for row in all_ratings:
            movie_user_matrix[movie_to_index[row[0]], user_to_index[row[1]]] = row[2]

        # Find similar users
        user_correlation_matrix = np.corrcoef(movie_user_matrix)
        similar_user_indices = np.argsort(user_correlation_matrix[user_to_index[user_id]])[::-1][1:100]

        # Generate movie recommendations based on similar users
        recommendations = []
        for movie_id in movie_to_index:
            if movie_user_matrix[movie_to_index[movie_id], user_to_index[user_id]] == 0:
                # Movie not rated by the user
                rated_by_similar_users = [
                    movie_user_matrix[movie_to_index[movie_id], similar_user]
                    for similar_user in similar_user_indices
                    if (
                        movie_to_index[movie_id] < movie_user_matrix.shape[0]
                        and similar_user < movie_user_matrix.shape[1]
                        and movie_user_matrix[movie_to_index[movie_id], similar_user] > 4
                    )
                ]

                if rated_by_similar_users and len(rated_by_similar_users) > 1:  # Ensure there are enough ratings
                    predicted_rating = np.mean(rated_by_similar_users)
                    recommendations.append({"movie_id": movie_id, "predicted_rating": predicted_rating})

        # Sort recommendations by predicted rating in descending order
        recommendations.sort(key=lambda x: x['predicted_rating'], reverse=True)

        result = {
            'user_id': user_id,
            'movie_recommendations': recommendations[:5]
        }

        return Response(200, {"content-type": "application/json"}, json.dumps(result, default=custom_encoder).encode('utf-8'))

    except Exception as e:
        return Response(500, {"content-type": "text/plain"}, bytes(f"error {e}", "utf-8"))

class IncomingHandler(IncomingHandler):
    def handle_request(self, request: Request) -> Response:
        uri = urlparse(request.uri)
        try:
            handler = router(uri.path, request.method)
            return handler.target(uri, request)
        except exceptions.NotFoundError:  
            return Response(404, {}, None)

def custom_encoder(obj):
    if isinstance(obj, np.int32):
        return int(obj)  # Convert numpy.int32 to regular int
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
