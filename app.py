import requests

from flask import Flask, render_template
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route("/")
@app.route("/2024")
def home():
    films = {}

    req = requests.get('https://nifff.ch/programme-2024/?sort=schedule&type=film')
    prog = BeautifulSoup(req.text, "html.parser")

    movies = prog.find_all(class_='archive-movie__item')

    for movie in movies:
        projections = []
        infos = []

        film_title = movie.find(class_='archive-movie__item__title')

        subtitle = film_title.div
        if subtitle:
            subtitle.decompose()
        
        title = film_title.get_text(strip=True)

        genre = movie.find(class_='archive-movie__item__genre').get_text(strip=True) if movie.find(class_='archive-movie__item__genre') else "N/A"
        category = movie.find(class_='archive-movie__item__categories').get_text(strip=True) if movie.find(class_='archive-movie__item__categories') else "N/A"

        if category == 'NIFFF Invasion':
            continue

        projections_raw = movie.find(class_='archive-movie__item__information--right')

        infos_raw = movie.find(class_='archive-movie__item__information--left')

        for info in infos_raw:
            if '<br/>' not in str(info) and len(str(info)) > 2 :
                infos.append(str(info).strip())

        for day in projections_raw:
            if '<br/>' not in str(day) and len(str(day)) > 2 :
                projections.append(str(day).strip())

        films[title] = {
            'genre': genre,
            'category': category,
            'projections': projections,
            'infos': infos
        }

    return render_template("index.html", films=films)

if __name__ == "__main__":
    app.run(debug=True)
