import requests
from bs4 import BeautifulSoup as BS
import argparse
import math
from itertools import islice


def fetch_afisha_page():
    url = "http://www.afisha.ru/msk/schedule_cinema/"
    return requests.get(url).content


def parse_afisha_list(raw_html):
    soup = BS(raw_html, "lxml")
    movies = []
    for item in soup.find_all('div',
                              "object s-votes-hover-area collapsed"):
        movie = {}
        a = item.find('h3', "usetags")
        ref = a.find('a', href=True)
        movie["title"] = a.text
        movie["afishaUrl"] = "http:{}".format(ref['href'])
        table = item.find('table')
        movie["cinemas"] = len(table.find_all('tr'))
        movies.append(movie)

    return movies


def fetch_movie_info(movie):
    kinopoisk_url = "https://www.kinopoisk.ru/index.php"
    params = {"first": "no",
                      "what": "",
                      "kp_query": movie['title']}
    try:
        kinopoisk_content = requests.get(kinopoisk_url,
                                      params=params).content
        soup = BS(kinopoisk_content, "lxml")
        wanted_item = soup.find('div', "element most_wanted")
        rating = wanted_item.find('div', "rating")
        if rating is not None:
            item = rating['title']
            vote_raw = item[item.find('(')+1: item.find(')')]
            digits = [int(s) for s in vote_raw.split() if s.isdigit()]
            full_number = 0
            for i in range(len(digits)):
                number = len(digits) - i
                full_number += digits[number-1] * math.pow(1000, i)

            movie['rating'] = rating.text
            movie['voted'] = int(full_number)
        else:
            movie['rating'] = 0
            movie['voted'] = 0
    except (IndexError, AttributeError, KeyError):
        movie['rating'] = 0
        movie['voted'] = 0


def output_movies_to_console(movies, args, output_length=10):
    if args.cinema:
        print("Check for cinema")
        sorted_movies = sorted(movies, key=lambda x: (int(x['cinemas']),
                                                      float(x['rating'])),
                               reverse=True)
    else:
        print("No check for cinema")
        sorted_movies = sorted(movies, key=lambda x: (float(x['rating'])),
                               reverse=True)
    for index, movie in enumerate(islice(sorted_movies,
                                         output_length)):
        print("{}. {}".format(index + 1, movie['title']))
        print("Show in {} cinema, rating '{}', voted by {}.".format(
            movie['cinemas'],
            movie['rating'],
            movie['voted']
        ))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Get most voted movies in cinema.")
    parser.add_argument("--cinema",
                        help="Add count cinemas as a sorting key",
                        action="store_true")
    args = parser.parse_args()
    raw_afisha_page = fetch_afisha_page()
    movies = parse_afisha_list(raw_afisha_page)
    for movie in movies:
        fetch_movie_info(movie)
    output_movies_to_console(movies, args)
