#!/usr/bin/env python
from __future__ import (absolute_import, print_function)

import json
import os
import string
import sys

HTML_TEMPLATE = '''
<!DOCTYPE html>
<title>webtreemap demo</title>
<style>
${webtreemapcss}
</style>
<style>
body {
  font-family: sans-serif;
  font-size: 0.8em;
  margin: 2ex 4ex;
}

h1 {
  font-weight: normal;
}

#map {
  width: screen.width;
  height: 1000px;

  position: relative;
  cursor: pointer;
  -webkit-user-select: none;
}
</style>

<h1>webtreemap demo</h1>

<p>This is a simple demonstration of
<a href="http://github.com/emvar/webtreemap">webtreemap</a>.</p>

<p>Click on a box to zoom in.  Click on the outermost box to zoom out.</p>

<div id='map'></div>

<script type="text/javascript">
${ninjalogtree}
</script>

<script type="text/javascript">
${webtreemapjs}
</script>

<script type="text/javascript">
var map = document.getElementById('map');
appendTreemap(map, kTree);
</script>

'''

class Node(object):
  def __init__(self, size):
    self.children = {}
    self.size = size


def Insert(data, path, duration):
  """Takes a directory path and a build duration, and inserts nodes for every
  path component into data, adding duration to all directory nodes along the
  path."""
  if '/' not in path:
    if path in data.children:
      Insert(data, os.path.join(path, 'postbuild'), duration)
      return
    assert not path in data.children
    data.children[path] = Node(size=duration)
    data.size += duration
    return

  prefix, path = path.split('/', 1)
  if prefix not in data.children:
    data.children[prefix] = Node(size=0)
  data.size += duration
  Insert(data.children[prefix], path, duration)


def FormatTime(t):
  """Converts a time into a human-readable format."""
  if t < 60:
    return '%.1fs' % t
  if t < 60 * 60:
    return '%dm%.1fs' % (t / 60, t % 60)
  return '%dh%dm%.1fs' % (t / (60 * 60), t % (60 * 60) / 60, t % 60)


def ToDicts(node, name):
  """Converts a Node tree to an object tree usable by webtreemap."""
  d = {
    'name': "'%s' %s" % (name, FormatTime(node.size)),
    'data': { '$area': int(node.size*1000.) }
  }
  if node.children:
    d['children'] = [ToDicts(v, k) for k, v in node.children.items()]
  return d

def load(filename):
  with open(filename, 'r') as handle:
    stuff = handle.read()
  return stuff

def loadCSS():
  return load('webtreemap/webtreemap.css')

def loadJavaScript():
  return load('webtreemap/webtreemap.js')

def ToJson(logfile, **kwargs):
  '''Convert ninja build log to a json object suitable for webtreemap'''
  data = Node(size=0)
  times = set()
  did_policy = False
  for line in logfile.readlines()[1:]:
    start, finish, _, output, _ = line.split('\t')
    duration = (int(finish) - int(start)) / 1000.0

    # Multiple outputs with exactly the same timestamps were very likely part
    # of a single multi-output edge. Count these only once.
    if (start, finish) in times:
      continue
    times.add((start, finish))

    # Massage output paths a bit.
    if output.startswith('obj/') or output.startswith('gen/'):
      output = output[4:]
    if output.endswith('_unittest.o') or output.endswith('Test.o'):
      output = 'test/' + output
    elif output.endswith('.o'):
      output = 'source/' + output

    Insert(data, output, duration)

  obj = ToDicts(data, 'everything')
  return json.dumps(obj, **kwargs)

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser('Converts a ninja build log to webtreemap based html report')
  parser.add_argument('logfile', metavar='ninjalogfile', type=argparse.FileType('r'),
                      help='Run `ninja -t recompact` first to make sure that no duplicate entries are in the build log')
  parser.add_argument('-o', '--output', dest='reportfile', default='report.html', type=argparse.FileType('w'), help='default=report.html')
  parser.add_argument('--compact-json', dest='prettyjson', action='store_false',
                      help='pretty printed json in report')
  parser.add_argument('--json', dest='jsononly', action='store_true',
                      help='write json document to output file')

  args = parser.parse_args()

  # convert the ninja report to a json document
  jsonargs = {}
  if args.prettyjson:
    jsonargs['indent'] = 2
  data = ToJson(args.logfile, **jsonargs)
  if args.jsononly:
    args.reportfile.write(data)
    print('wrote results to "%s"' % args.reportfile.name)
    sys.exit(0)
  data = 'var kTree = ' + data

  # put together the output text
  template = string.Template(HTML_TEMPLATE)
  html_text = template.substitute(webtreemapcss=loadCSS(),
                                  webtreemapjs=loadJavaScript(),
                                  ninjalogtree = data,
  )

  # write out the result
  args.reportfile.write(html_text)
  print('wrote results to "%s"' % args.reportfile.name)
