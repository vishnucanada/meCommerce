import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Sample Data: Movie catalog with genres
movies = pd.DataFrame([
    {"movie_id": 1, "title": "The Matrix", "genres": "Sci-Fi Action Cyberpunk"},
    {"movie_id": 2, "title": "John Wick", "genres": "Action Thriller Gun-Fu"},
    {"movie_id": 3, "title": "Interstellar", "genres": "Sci-Fi Space Drama"},
    {"movie_id": 4, "title": "Toy Story", "genres": "Animation Children Comedy"},
    {"movie_id": 5, "title": "Blade Runner 2049", "genres": "Sci-Fi Action Dystopian"}
])

# 2. Vectorize the text data using TF-IDF
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(movies['genres'])

# 3. Compute the Cosine Similarity Matrix
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

# 4. Recommendation function based on a movie title
def get_recommendations(movie_title, cosine_sim_matrix, df, top_n=2):
    # Get the index of the movie that matches the title
    try:
        idx = df[df['title'] == movie_title].index[0]
    except IndexError:
        return f"Movie '{movie_title}' not found in the catalog."
    
    # Get similarity scores of all movies with this movie
    sim_scores = list(enumerate(cosine_sim_matrix[idx]))
    
    # Sort the movies based on the similarity scores (highest first)
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    # Get the scores of the top_n most similar movies (skip the first one since it's the movie itself)
    sim_scores = sim_scores[1:top_n+1]
    
    # Get the movie indices
    movie_indices = [i[0] for i in sim_scores]
    
    # Return the top N most similar movies
    return df['title'].iloc[movie_indices].tolist()

# 5. Test the recommendation model
target_movie = "The Matrix"
recommendations = get_recommendations(target_movie, cosine_sim, movies, top_n=2)

print(f"Because you watched '{target_movie}', you might like:")
for movie in recommendations:
    print(f"- {movie}")
