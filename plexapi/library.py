"""
PlexLibrary
"""
from plexapi import utils
from plexapi.exceptions import NotFound


class Library(object):

    def __init__(self, server, data):
        self.server = server
        self.identifier = data.attrib.get('identifier')
        self.mediaTagVersion = data.attrib.get('mediaTagVersion')
        self.title1 = data.attrib.get('title1')
        self.title2 = data.attrib.get('title2')

    def __repr__(self):
        return '<Library:%s>' % self.title1.encode('utf8')

    def sections(self):
        items = []
        SECTION_TYPES = {
            MovieSection.TYPE: MovieSection,
            ShowSection.TYPE: ShowSection,
            MusicSection.TYPE: MusicSection,
        }
        path = '/library/sections'
        for elem in self.server.query(path):
            stype = elem.attrib['type']
            if stype in SECTION_TYPES:
                cls = SECTION_TYPES[stype]
                items.append(cls(self.server, elem, path))
        return items

    def section(self, title=None):
        for item in self.sections():
            if item.title == title:
                return item
        raise NotFound('Invalid library section: %s' % title)

    def all(self):
        return utils.list_items(self.server, '/library/all')

    def onDeck(self):
        return utils.list_items(self.server, '/library/onDeck')

    def recentlyAdded(self):
        return utils.list_items(self.server, '/library/recentlyAdded')

    def get(self, title):
        return utils.find_item(self.server, '/library/all', title)

    def getByKey(self, key):
        return utils.find_key(self.server, key)
        
    def search(self, title, prefilter='all', libtype=None, **tags):
        args = {}
        if title: args['title'] = title
        if libtype: args['type'] = utils.search_type(libtype)
        for tag, obj in tags.items():
            args[tag] = obj.id
        query = '/library/%s%s' % (prefilter, utils.joinArgs(args))
        return utils.list_items(self.server, query)

    def cleanBundles(self):
        self.server.query('/library/clean/bundles')

    def emptyTrash(self):
        for section in self.sections():
            section.emptyTrash()

    def optimize(self):
        self.server.query('/library/optimize')

    def refresh(self):
        self.server.query('/library/sections/all/refresh')


class LibrarySection(object):

    def __init__(self, server, data, initpath):
        self.server = server
        self.initpath = initpath
        self.type = data.attrib.get('type')
        self.key = data.attrib.get('key')
        self.title = data.attrib.get('title')
        self.scanner = data.attrib.get('scanner')
        self.language = data.attrib.get('language')

    def __repr__(self):
        title = self.title.replace(' ','.')[0:20]
        return '<%s:%s>' % (self.__class__.__name__, title.encode('utf8'))

    def _primary_list(self, key):
        return utils.list_items(self.server, '/library/sections/%s/%s' % (self.key, key))

    def _secondary_list(self, key, input=None):
        choices = list_choices(self.server, '/library/sections/%s/%s' % (self.key, key))
        if not input:
            return list(choices.keys())
        return utils.list_items(self.server, '/library/sections/%s/%s/%s' % (self.key, key, choices[input]))

    def all(self):
        return self._primary_list('all')

    def newest(self):
        return self._primary_list('newest')

    def onDeck(self):
        return self._primary_list('onDeck')

    def recentlyAdded(self):
        return self._primary_list('recentlyAdded')

    def recentlyViewed(self):
        return self._primary_list('recentlyViewed')

    def unwatched(self):
        return self._primary_list('unwatched')

    def contentRating(self, input=None):
        return self._secondary_list('contentRating', input)

    def firstCharacter(self, input=None):
        return self._secondary_list('firstCharacter', input)

    def genre(self, input=None):
        return self._secondary_list('genre', input)

    def year(self, input=None):
        return self._secondary_list('year', input)

    def get(self, title):
        path = '/library/sections/%s/all' % self.key
        return utils.find_item(self.server, path, title)

    def search(self, title, filter='all', libtype=None, **tags):
        """ Search section content.
            title: Title to search (pass None to search all titles).
            filter: One of {all, newest, onDeck, recentlyAdded, recentlyViewed, unwatched}.
            libtype: One of {movie, show, season, episode, artist, album, track}.
            tags: One of {country, director, genre, producer, actor, writer}.
        """
        args = {}
        if title: args['title'] = title
        if libtype: args['type'] = utils.search_type(libtype)
        for tag, obj in tags.items():
            args[tag] = obj.id
        query = '/library/sections/%s/%s%s' % (self.key, filter, utils.joinArgs(args))
        return utils.list_items(self.server, query)

    def analyze(self):
        self.server.query('/library/sections/%s/analyze' % self.key)

    def emptyTrash(self):
        self.server.query('/library/sections/%s/emptyTrash' % self.key)

    def refresh(self):
        self.server.query('/library/sections/%s/refresh' % self.key)


class MovieSection(LibrarySection):
    TYPE = 'movie'

    def actor(self, input=None):
        return self._secondary_list('actor', input)

    def country(self, input=None):
        return self._secondary_list('country', input)

    def decade(self, input=None):
        return self._secondary_list('decade', input)

    def director(self, input=None):
        return self._secondary_list('director', input)

    def rating(self, input=None):
        return self._secondary_list('rating', input)

    def resolution(self, input=None):
        return self._secondary_list('resolution', input)

    def search(self, title, filter='all', **tags):
        return super(MovieSection, self).search(title, filter=filter, libtype='movie', **tags)


class ShowSection(LibrarySection):
    TYPE = 'show'

    def recentlyViewedShows(self):
        return self._primary_list('recentlyViewedShows')

    def search(self, title, filter='all', **tags):
        return super(ShowSection, self).search(title, filter=filter, libtype='show', **tags)

    def searchEpisodes(self, title, filter='all', **tags):
        return super(ShowSection, self).search(title, filter=filter, libtype='episode', **tags)


class MusicSection(LibrarySection):
    TYPE = 'artist'

    def search(self, title, filter='all', atype=None, **tags):
        """ Search section content.
            title: Title to search (pass None to search all titles).
            filter: One of {'all', 'newest', 'onDeck', 'recentlyAdded', 'recentlyViewed', 'unwatched'}.
            videotype: One of {'artist', 'album', 'track'}.
            tags: One of {country, director, genre, producer, actor, writer}.
        """
        args = {}
        if title: args['title'] = title
        if atype: args['type'] = utils.search_type(atype)
        for tag, obj in tags.items():
            args[tag] = obj.id
        query = '/library/sections/%s/%s%s' % (self.key, filter, utils.joinArgs(args))
        return utils.list_items(self.server, query)

    def recentlyViewedShows(self):
        return self._primary_list('recentlyViewedShows')

    def searchArtists(self, title, filter='all', **tags):
        return self.search(title, filter=filter, atype='artist', **tags)

    def searchAlbums(self, title, filter='all', **tags):
        return self.search(title, filter=filter, atype='album', **tags)

    def searchTracks(self, title, filter='all', **tags):
        return self.search(title, filter=filter, atype='track', **tags)


def list_choices(server, path):
    return {c.attrib['title']:c.attrib['key'] for c in server.query(path)}
