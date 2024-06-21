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

        film_title = movie.find(class_='archive-movie__item__title')

        subtitle = film_title.div
        if subtitle:
            subtitle.decompose()
        
        title = film_title.get_text(strip=True)

        # film_title = movie.find(class_='archive-movie__item__title').get_text(strip=True) if movie.find(class_='archive-movie__item__title') else "N/A"
        genre = movie.find(class_='archive-movie__item__genre').get_text(strip=True) if movie.find(class_='archive-movie__item__genre') else "N/A"
        category = movie.find(class_='archive-movie__item__categories').get_text(strip=True) if movie.find(class_='archive-movie__item__categories') else "N/A"
        projections_raw = movie.find(class_='archive-movie__item__information--right')

        for day in projections_raw:
            if '<br/>' not in str(day) and len(str(day)) > 2 :
                projections.append(str(day).strip())

        films[title] = {
            # 'title': film_title,
            'genre': genre,
            'category': category,
            'projections': projections
        }

    return (films)

if __name__ == "__main__":
    app.run(debug=True)




# def home():
#     # prog = {}
#     films = {}
#     titles = []
#     genres = []
#     infos = []
#     categories = []
#     projections = []

#     req = requests.get('https://nifff.ch/programme-2024/?sort=schedule&type=film')
#     prog = BeautifulSoup(req.text, "html.parser")

#     movies = prog(class_='archive-movie__list')

#     for id, title in enumerate(movies):
        
#         film_title = title(class_='archive-movie__item__title')


#         films[id]['title'] = film_title

#         films[id]['genre'] = title(class_='archive-movie__item__genre')
#         films[id]['infos'] = title(class_='archive-movie__information')
#         films[id]['category'] = title(class_='archive-movie__categories')

#     return(films)


        # all_div = title.div.get_text(strip=True)



        # subtitle = film_title.div
        # if subtitle:
        #     subtitle.decompose()
        # films[title] = film_title.get_text(strip=True)
        # print(film_title)
        # print(films[title])
        


    # for title in prog(class_='archive-movie__item__title'):
    #     subtitle = title.div
    #     if subtitle:
    #         subtitle.decompose()

    #     print(title)
    #     films[title] = title.get_text(strip=True)
    #     # titles.append(title.get_text(strip=True))
    #     print(films[title])

    #     genre = title.find(class_='archive-movie__item__genre')
    #     print(genre)

    #     # films[title]['genre'] = prog.find(class_='archive-movie__item__genre').get_text(strip=True)
    #     # films[title]['infos'] = prog.find(class_='archive-movie__information').get_text(strip=True)
    #     # films[title]['category'] = prog.find(class_='archive-movie__categories').get_text(strip=True)

    #     for id, projection in enumerate(prog(class_='archive-movie__information--right')):
    #         films[title]['projections'][projection] = projection
    #     # get_info(prog, 'archive-movie__item__genre', genres)
    #     # get_info(prog, 'archive-movie__information', infos)
    #     # get_info(prog, 'archive-movie__categories', categories)
    #     # get_info(prog, 'archive-movie__information--right', projections)

    # return render_template("index.html", titles=titles, genres=genres, infos=infos, categories=categories, projections=projections)
