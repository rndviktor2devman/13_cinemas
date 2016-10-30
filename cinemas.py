import requests
from bs4 import BeautifulSoup as BS
import argparse
import math
from itertools import islice


def fetch_afisha_page():
    url = "http://www.afisha.ru/msk/schedule_cinema/"
    afisha_content = requests.get(url).content
    return parse_afisha_list(afisha_content)


def parse_afisha_list(raw_html):
    soup = BS(raw_html, "lxml")
    descriptions = []
    for item in soup.find_all('div',
                              "object s-votes-hover-area collapsed"):
        description = {}
        a = item.find('h3', "usetags")
        ref = a.find('a', href=True)
        description["title"] = a.text
        description["afishaUrl"] = "http:{}".format(ref['href'])
        table = item.find('table')
        description["cinemas"] = len(table.find_all('tr'))
        descriptions.append(description)

    return descriptions


def fetch_movie_info(description):
    kinopoisk_url = "https://www.kinopoisk.ru/index.php"
    params = {"first": "no",
                      "what": "",
                      "kp_query": description['title']}
    try:
        kinopoisk_content = requests.get(kinopoisk_url,
                                      params=params).content
        soup = BS(kinopoisk_content, "lxml")
        item = soup.find('div', "element most_wanted")
        rating = item.find('div', "rating")
        vote_str = rating['title']
        voted_full = vote_str[vote_str.find('(')+1: vote_str.find(')')]
        voted = [int(s) for s in voted_full.split() if s.isdigit()]
        number_voted = 0
        for i in range(len(voted)):
            numb = len(voted) - i
            number_voted += voted[numb-1] * math.pow(1000, i)

        description['rating'] = rating.text
        description['voted'] = int(number_voted)
    except (IndexError, AttributeError, KeyError):
        description['rating'] = 0
        description['voted'] = 0


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
    data = fetch_afisha_page()
    for movie in data:
        fetch_movie_info(movie)
    output_movies_to_console(data, args)

