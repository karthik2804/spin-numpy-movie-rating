#!/bin/bash

# List of sample movie names
movie_names=("The Matrix" "Inception" "The Shawshank Redemption" "Pulp Fiction" "The Dark Knight" "Fight Club" "Forrest Gump" "The Godfather" "Star Wars" "Jurassic Park")

# Function to get a random movie name
get_random_movie_name() {
    echo ${movie_names[$((RANDOM % ${#movie_names[@]}))]}
}

# Populate movies
for i in {1..100}; do
    title=$(get_random_movie_name)
    genre=$((i % 5 + 1))  # Assuming there are 5 genres
    curl -X POST -H "Content-Type: application/json" -d "{\"title\": \"$title\", \"genre\": \"$genre\"}" http://localhost:3000/add_movie
done

# Populate ratings for each user and each movie (40-50 movies per user)
for user_id in {1..1000}; do
    for movie_id in $(shuf -i 1-100 -n $((RANDOM % 11 + 40))); do
        rating=$((RANDOM % 5 + 1))
        curl -X POST -H "Content-Type: application/json" -d "{\"movie_id\": $movie_id, \"user_id\": $user_id, \"rating\": $rating}" http://localhost:3000/add_rating
    done
done
