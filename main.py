from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, FloatField, StringField
import requests, html
from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
headers = {
    "accept": "application/json",
    "Authorization": "###Insert APIKEY###"
}



class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config['SECRET_KEY'] = '###Insert Secret Key###'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
db.init_app(app)
Bootstrap5(app)


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    rating: Mapped[int] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String, nullable=True)
    img_url: Mapped[str] = mapped_column(String, nullable=True)


with app.app_context():
    db.create_all()

class Form(FlaskForm):
    rating = FloatField("Rating out of 10")
    review = TextAreaField("Review")
    submit = SubmitField("Submit")

class MovieForm(FlaskForm):
    name = StringField("Movie Title")
    submit_movie = SubmitField("Submit")

@app.route("/", methods=['GET', 'POST'])
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating.desc())).scalars().all()
    rank = 1
    for movie in movies:
        movie.ranking = rank
        rank += 1
    db.session.commit()
    movie_id = request.args.get('id')
    if movie_id:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        response = requests.get(url, headers=headers).json()
        new_movie = Movie(title=response['original_title'], img_url=f"https://www.themoviedb.org/t/p/original/{response['backdrop_path']}", year= response['release_date'].split("-")[0], description= response['overview'])
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id= new_movie.id))
    return render_template("index.html", movies=movies)

@app.route("/add", methods=['GET', 'POST'])
def add():
    movie_form = MovieForm()
    if movie_form.validate_on_submit():
        movie_name = html.escape(movie_form.name.data)
        url = f"https://api.themoviedb.org/3/search/movie?query={movie_name}"
        response = requests.get(url, headers=headers).json()
        return render_template('select.html', response=response)
    return render_template("add.html", form=movie_form)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form = Form()
    id = request.args.get('id')
    movie = db.session.execute(db.select(Movie).where(Movie.id == id)).scalar()
    if form.validate_on_submit():
        rating = form.rating.data
        review = form.review.data
        movie.rating = rating
        movie.review = review
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/<id>")
def delete(id):
    movie = db.session.execute(db.select(Movie).where(Movie.id == id)).scalar()
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
