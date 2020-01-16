#coding=utf8

import re
import os
import sys
import json
import operator
import datetime

import requests
import humanize


ghUser = os.environ['GH_USER']
ghToken = os.environ['GH_TOKEN']


class InputStream(object):
    def __init__(self, reader):
        self.lines = list(reader)
        self.size = len(self.lines)
        self.curr = 0

    def hasNext(self):
        return self.curr < self.size

    def next(self):
        rv = self.lines[self.curr]
        self.curr += 1
        return rv

    def back(self):
        self.curr -= 1


def getRepoStars(repoName):
    url = 'https://api.github.com/repos/{}'.format(repoName)
    resp = requests.get(url, auth=(ghUser, ghToken))
    data = json.loads(resp.content)
    return data['stargazers_count']


def isProjectLine(line):
    return re.match(r'\s*-\s+\[.*?\]\(', line) is not None


def handleProjectLine(line):
    repoMatch = re.search(r'\]\(.*?github.com/([^/]+/[^/]+)/?\)', line)
    if repoMatch is None:
        print >>sys.stderr, 'cannot get github name: ', line
        return line, 0
    repoName = repoMatch.group(1)
    repoStar = getRepoStars(repoName)
    return re.sub(r'[\d\.\k\,]+\s*:star:', '{}:star:'.format(humanize.intcomma(repoStar)), line), repoStar


def handleCalendarLine(line):
    if ':calendar:' in line:
        return re.sub(r'\d{4}-\d{2}-\d{2}', datetime.datetime.now().strftime('%Y-%m-%d'), line)
    else:
        return line


def handleProjectList(stream):
    projects = []
    while stream.hasNext():
        line = stream.next()
        if not isProjectLine(line):
            stream.back()
            break

        projects.append(handleProjectLine(line))

    projects.sort(key=operator.itemgetter(1), reverse=True)
    for project in projects:
        sys.stdout.write(project[0])


def main():
    if not ghUser or not ghToken:
        raise Exception('invalid gh environ')

    stream = InputStream(sys.stdin)
    while stream.hasNext():
        line = stream.next()
        if isProjectLine(line):
            stream.back()
            handleProjectList(stream)
        else:
            sys.stdout.write(handleCalendarLine(line))


if __name__ == '__main__':
    main()
