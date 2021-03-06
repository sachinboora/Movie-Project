from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import sqlalchemy
from datetime import datetime
import sqlite3

MOVIE_DB_API_KEY = "d6c6a6cc6c0682193477911229b6a82e"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)


# Add Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Create Model
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


class RateMovieForm(FlaskForm):
    # Our Form has 2 fields -- Ratings(out of 10) and Reviews

    ratings = StringField('Your Rating out of 10')
    review = StringField('Your Reviews')
    submit = SubmitField('Done')


class AddMovie(FlaskForm):
    # Our Form has only 1 field - Add movie name

    title = StringField('Please Enter Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


# class FindMovieForm():
#     title = StringField("Movie Title", validators=[DataRequired()])
#     submit = SubmitField("Add Movie")
#
#     def validate_on_submit(self):
#         pass


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=['GET', 'POST'])
def rate_movie():
    rating_form = RateMovieForm()
    movie_id = request.args.get('id')
    movie = Movie.query.get(movie_id)
    if rating_form.validate_on_submit():
        movie.rating = float(rating_form.ratings.data)
        movie.review = rating_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=rating_form)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get('id')
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add_movie():
    add_form = AddMovie()
    if add_form.validate_on_submit():
        movie_title = add_form.title.data
        response = requests.get("https://api.themoviedb.org/3/search/movie?api_key=d6c6a6cc6c0682193477911229b6a82e&"
                                f"query={movie_title}")
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=add_form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY})
        data = response.json()
        new_movie = Movie(
            title = data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("rate_movie", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
