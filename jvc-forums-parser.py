#!/usr/bin/python3
# Coding: utf-8

# Author : Antoine Paix
# This program downloads all posts from all forum topics.

import requests
import re
from bs4 import BeautifulSoup
import time

def generateUrls(forum_url, pages_forum='all'):
    """Génère les urls des pages d'un forum"""

    # on génère toutes les urls de toutes les pages d'un forum
    if pages_forum == 'all':
        url = forum_url.split('-')
        i = 1
        while True:
            link = '-'.join(url[:5] + [str(int(i))] + url[6:])
            i += 25
            time.sleep(0.5)
            yield link

    # on renvoie simplement l'url passée en argument
    elif pages_forum == 'current':
        link = forum_url
        yield link

    # on renvoie une sélection d'urls
    elif isinstance(pages_forum, list) or isinstance(pages_forum, tuple) or isinstance(pages_forum, set):
        url = forum_url.split('-')

        def convert_page_number(page):
            new_page_number = ((int(page) - 1) * 25) + 1
            return new_page_number
        
        for i in pages_forum:
            try:
                if isinstance(i, int) and i != 0:
                    link = '-'.join(url[:5] + [str(convert_page_number(i))] + url[6:])
                    yield link
            except ValueError:
                raise("This page does not exist.")


def getTopics(forum_url):
    """Télécharge les données de tous les topics d'un forum"""
    html_content = requests.get(forum_url).text
    soup = BeautifulSoup(html_content, "html.parser")
    bloc_topic = soup.find("ul", class_="topic-list topic-list-admin")
    topic_list = bloc_topic.findAll('li', {'data-id':re.compile('[0-9]{8}')})

    for topic in topic_list:
        id_topic = topic['data-id']
        topic_link = "http://www.jeuxvideo.com" + topic.find('a', {'class':'lien-jv topic-title'}).get('href')
        topic_title = topic.find('a', {'class':'lien-jv topic-title'}).get_text().strip()
        author = topic.find('span', {'class':'topic-author'}).get_text().strip()
        nb_messages = topic.find('span', {'class':'topic-count'}).get_text().strip()
        last_mes = topic.find('span', {'class':'topic-date'}).get_text().strip()

        yield id_topic, topic_link, topic_title, author, nb_messages, last_mes

def getTopicPages(url):
    """
    Génère les urls de toutes les pages du topic.
    On passe en argument la première page du topic
    """
    html_content = requests.get(url).text
    soup = BeautifulSoup(html_content, "html.parser")
    pages = soup.find('div', class_="bloc-liste-num-page").find_all('span') # on ajoute l'url des pages suivantes

    # si le nombre de pages par topic est strictement inférieur à 12
    if len(pages) < 12:
        urls = [url]
        pages = soup.find('div', class_="bloc-liste-num-page").find_all('a')
        for page in pages:
            url = "http://www.jeuxvideo.com" + page.get('href')
            urls.append(url)

        for url in urls:
            yield url

    # si le nombre de pages par topic est supérieur ou égal à 12
    else:
        nbre_pages = int(pages[-2].text)
        url = url.split('/')[-1]
        url = url.split('-')
        for i in range(1, nbre_pages+1):
            yield "http://www.jeuxvideo.com/forums/" + '-'.join(url[:3] +[str(i)] + url[4:])
        
def getPosts(url):
    """Récupération de tous les posts d'une page et on les renvoie dans un générateur"""
    html_content = requests.get(url).text
    soup = BeautifulSoup(html_content, "html.parser")
    posts = soup.find('div', class_="conteneur-messages-pagi")
    posts = soup.find_all('div', class_="bloc-message-forum")
    for post in posts:
        yield post

def parserPost(post):
    """On parse le post pour retenir certaines infos (post_id, auteur, date, contenu)"""
    post_id = post['data-id']

    # On parse le header (id, auteur, date)
    bloc_header = post.find('div', class_="bloc-header")

    # on récupère le pseudo
    try:
        pseudo = bloc_header.find('span', class_=re.compile('JvCare [0-9A-Z]* bloc-pseudo-msg text-[user|modo|admin]')).text.strip()
    except AttributeError:
        pseudo = 'Pseudo supprimé'
    
    # on récupère la date
    try:
        date = bloc_header.find('div', class_='bloc-date-msg').find('span', class_=re.compile('JvCare [0-9A-Z]* lien-jv')).text
    except AttributeError:
        date = bloc_header.find('div', class_='bloc-date-msg').text.strip() # balise différente pour les pseudos supprimés

    # On parse le contenu du post
    try:
        contenu = post.find('div', class_='txt-msg text-enrichi-forum').text
    except AttributeError:
        contenu = '' # si erreur, on renvoie une chaîne vide

    return post_id, pseudo, date, contenu

########## MAIN PROGRAM ##########

if __name__ == '__main__':

    for page_url in generateUrls('http://www.jeuxvideo.com/forums/0-38-0-1-0-1-0-linux.htm', pages_forum=[1, 2, 3, 4, 5]):
        for id_topic, topic_url, topic_title, *_ in getTopics(page_url):
            for page in getTopicPages(topic_url):
                for post in getPosts(page):
                    print(parserPost(post))
                    print(id_topic)
                    print(topic_title)
                    print(topic_url)
                    print('-' * 200)

    # for pages in generateUrls('http://www.jeuxvideo.com/forums/0-51-0-1-0-26-0-blabla-18-25-ans.htm', pages_forum=[i for i in range(1, 11)]):
    #     print(pages)