import sqlite3
import requests
from bs4 import BeautifulSoup

class DocSet(object):

    def __init__(self, name):

        self.name = name
        self.init_db()

    @property
    def path(self):

        return '{name}.docset'.format(name = self.name)

    def init_db(self):

        path = '{path}/Contents/Resources/docSet.dsidx'.format(path = self.path)

        database = sqlite3.connect(path)

        cursor = database.cursor()

        try: cursor.execute('DROP TABLE searchIndex;')
        except: pass

        cursor.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
        cursor.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

        database.commit()
        database.close()

    def insert_entries(self, entries):

        path = '{path}/Contents/Resources/docSet.dsidx'.format(path = self.path)

        database = sqlite3.connect(path)

        cursor = database.cursor()

        inserts = [(entry.name, entry.type_, entry.path) for entry in entries]

        cursor.executemany('insert into searchIndex(name, type, path) values (?,?,?)', inserts)

        database.commit()
        database.close()

class Entry(object):

    def __init__(self, name, path, type_, url, docset):

        self.name = name
        self.type_ = type_
        self.url = url
        self.docset = docset
        self.path = path

    @property
    def full_path(self):

        return '{docset}/Contents/Resources/Documents/{path}'.format(
                                                    docset = self.docset.path,
                                                    path = self.path)

    def download(self):

        r = requests.get(self.url)

        if r.status_code == 200:

            with open(self.full_path, 'w') as f:

                f.write(r.content)

        else:

            raise Exception('Received "{code}" when downloading "{name}"'.format(
                                                        code = r.status_code,
                                                        name = self.name))

    def rewrite(self, entries):

        source = open(self.full_path, 'r+')

        soup = BeautifulSoup(source.read())

        unnecessary = [
            '#megabladeContainer',
            '#ux-header',
            '#isd_print',
            '#isd_printABook',
            '#expandCollapseAll',
            '#leftNav',
            '.feedbackContainer',
            '#isd_printABook',
            '.communityContentContainer',
            '#ux-footer'
        ]

        for u in unnecessary:

            if u[0] == '#':

                try:
                    soup.find(id=u[1:]).decompose()
                except AttributeError:
                    pass

            elif u[0] == '.':

                for element in soup.find_all('div', class_=u[1:]):
                    element.decompose()

        for link in soup.find_all('a'):
            for entry in entries:
                try:
                    if link.attrs['href'] == entry.url:
                        link.attrs['href'] = entry.path
                except KeyError:
                    pass

        source.seek(0)
        source.write(str(soup))
        source.truncate()
        source.close()
