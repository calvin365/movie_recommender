import pandas as pd
import pickle
from surprise import Dataset, Reader, SVD

# Load MovieLens 100k dataset
ratings_raw = pd.read_csv("ml-100k/u.data", sep="\t", names=["userId", "movieId", "rating", "timestamp"])
ratings_raw.drop("timestamp", axis=1, inplace=True)
ratings_raw.to_csv("data/ratings.csv", index=False)

movies_raw = pd.read_csv("ml-100k/u.item", sep='|', encoding='latin-1', header=None)
movies_raw = movies_raw[[0, 1]]
movies_raw.columns = ["movieId", "title"]
movies_raw.to_csv("data/movies.csv", index=False)

ratings = pd.read_csv("data/ratings.csv")
reader = Reader(rating_scale=(0.5, 5.0))
data = Dataset.load_from_df(ratings[["userId", "movieId", "rating"]], reader)

trainset = data.build_full_trainset()
model = SVD()
model.fit(trainset)

with open("model.pkl", "wb") as f:
    pickle.dump(model, f)