# -*- encoding: utf-8 -*-

from __future__ import unicode_literals, print_function
import argparse
import re
import os
try:
    from typing import List, Tuple, Optional
except ImportError:
    pass

INDEX_RE = re.compile('([\d\.]*\d)  (.*)')


class IndexCursor:
    def __init__(self):
        self.data = [0]
        self.level = 2
        self.cursor = 0

    def encount(self, level):
        if level == 1:
            return ''
        if level == self.level:
            self.more()
        elif level > self.level:
            self.into()
        else:
            self.out()
        self.level = level
        return self.get_index()

    def into(self):
        self.data.append(1)
        self.cursor += 1

    def out(self):
        self.data.pop(-1)
        self.cursor -= 1
        self.more()

    def more(self):
        self.data[self.cursor] += 1

    def get_index(self):
        return '.'.join(map(lambda x: str(x), self.data))

def init_parser():
    """init a standard parser for this script"""
    parser = argparse.ArgumentParser(description='Add Index to markdown titles.')
    parser.add_argument('--rm', action='store_true', dest='rm',
                        help='remove index, instead of adding it.')
    parser.add_argument('--cover', action='store_true', dest='cover',
                        help='cover the original file, use with caution.')
    parser.add_argument('markdown', nargs='+',
                        help='markdown files to modify')
    return parser

def parse_title(line):
    """if this is title, return Tuple[level, content],

    @type line: str
    @return: Optional[Tuple[level, content]]
    """
    line = line.strip()
    if not line.startswith('#'):
        return None
    sharp_count = 0
    for c in line:
        if c == '#':
            sharp_count += 1
        else:
            break
    if sharp_count == len(line):
        return None
    title = line[sharp_count:].strip()
    return sharp_count, title

def parse_index(title):
    """if a title is start with a index, return Tuple[Optional[index], content]
    else return None
    
    @type title: str
    @return: Tuple[Optional[index], content]
    """
    match = INDEX_RE.match(title)
    if not match:
        return None, title
    return match.groups()


def handle_lines(lines, args):
    """given lines of content, handle them and return new lines
    
    @type lines: List[str]
    @type args: Any
    """
    result = []
    cursor = IndexCursor()
    for line in lines:
        line = line.strip('\n\r')
        parsed = parse_title(line)
        if parsed is None:
            result.append(line)
            continue
        level, title = parsed  # type: int, str
        index, title = parse_index(title)
        if args.rm:
            result.append('#' * level  + ' ' + title)
        else:
            result.append('#' * level + ' ' + cursor.encount(level) + '  ' + title)
    return result

def choose_avaliable_path(path):
    """choose a avaliable path based on given path
    
    @type path: str
    """
    lead, ext = os.path.splitext(path)
    count = 0
    
    while True:
        count += 1
        result = "{}-{}{}".format(lead, count, ext)
        if not os.path.exists(result):
            return result


def save_to(path, lines):
    """save lines to path of file
    
    @type path: str
    @type lines: List[str]
    """
    with open(path, 'w') as f:
        f.write('\n'.join(lines))


def handle_markdown(path, args):
    """

    @type path: str
    @type args: Any
    """
    try:
        with open(path, 'r') as f:
            lines = f.readlines()  # type: List[str]
    except FileNotFoundError:
        print("file {} not exist, skipping...")
        return False
    except PermissionError:
        print("file {} no permission to read, skipping...")
        return False
    handled = handle_lines(lines, args)
    save_path = (path if args.cover else choose_avaliable_path(path))
    save_to(save_path, handled)
    return True
    

def main():
    parser = init_parser()
    args = parser.parse_args()
    success = True
    for markdown in args.markdown:
        if not handle_markdown(markdown, args):
            success = False
    if not success:
        exit(1)

if __name__ == '__main__':
    main()