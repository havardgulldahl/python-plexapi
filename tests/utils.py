"""
Test Library Functions
"""
import inspect, sys, traceback
import datetime, time
from plexapi import server
from plexapi.myplex import MyPlexUser

COLORS = {'blue':'\033[94m', 'green':'\033[92m', 'red':'\033[91m', 'yellow':'\033[93m', 'end':'\033[0m'}


registered = []
def register(tags=''):
    def wrap2(func):
        registered.append({'name':func.__name__, 'tags':tags.split(','), 'func':func})
        def wrap1(*args, **kwargs):  # flake8:noqa
            func(*args, **kwargs)
        return wrap1
    return wrap2


def log(indent, message, color=None):
    dt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    if color:
        return sys.stdout.write('%s: %s%s%s%s\n' % (dt, ' '*indent, COLORS[color], message, COLORS['end']))
    return sys.stdout.write('%s: %s%s\n' % (dt, ' '*indent, message))


def fetch_server(args):
    if args.resource and args.username and args.password:
        user = MyPlexUser.signin(args.username, args.password)
        return user.getResource(args.resource).connect(), user
    elif args.baseuri and args.token:
        return server.PlexServer(args.baseuri, args.token), None
    return server.PlexServer(), None


def iter_tests(query):
    tags = query[5:].split(',') if query and query.startswith('tags:') else ''
    for test in registered:
        if not query:
            yield test
        elif tags:
            matching_tags = [t for t in tags if t in test['tags']]
            if matching_tags: yield test
        elif query in test['name']:
            yield test


def run_tests(module, args):
    plex, user = fetch_server(args)
    tests = {'passed':0, 'failed':0}
    for test in iter_tests(args.query):
        startqueries = server.TOTAL_QUERIES
        starttime = time.time()
        log(0, '%s (%s)' % (test['name'], ','.join(test['tags'])))
        try:
            test['func'](plex, user)
            runtime = time.time() - starttime
            queries = server.TOTAL_QUERIES - startqueries
            log(2, 'PASS! (runtime: %.3fs; queries: %s)' % (runtime, queries), 'blue')
            tests['passed'] += 1
        except Exception as err:
            errstr = str(err)
            errstr += '\n%s' % traceback.format_exc() if args.verbose else ''
            log(2, 'FAIL!: %s' % errstr, 'red')
            tests['failed'] += 1
        log(0, '')
    log(0, 'Tests Run:    %s' % sum(tests.values()))
    log(0, 'Tests Passed: %s' % tests['passed'])
    if tests['failed']:
        log(0, 'Tests Failed: %s' % tests['failed'], 'red')
    if not tests['failed']:
        log(0, '')
        log(0, 'EVERYTHING OK!! :)')
    raise SystemExit(tests['failed'])
