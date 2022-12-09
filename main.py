from __future__ import annotations
import curses
import pprint
import socket
import ssl
import sys
from url import *
from typing import List

TEST_URL = "nerdygames.org/george.html"
WHITELISTED_TAGS = ["a", "img", "p", "h1", "h2", "h3", "h4", "h5", "h6"]
TAGS_SPACE_BEFORE = ["h1", "h2", "h3", "h4", "h5", "h6", "p"]
TAGS_SPACE_AFTER = ["h1", "h2", "h3", "h4", "h5", "h6", "p"]
USE_CURSES = True

you_can_navigate_to_these_elements: List[Element] = []

current_render_x = 0
current_render_y = 0


class Element:
    inner_content: str = ""
    x: int = None
    y: int = None

    def __init__(self,
                 name: str,
                 children: List[Element] = [],
                 attributes: dict = {},
                 ):
        self.name = name
        self.children = children
        self.attributes = attributes

        self.format_flags = {
            "in_a": False
        }

    def draw(self, stdscr, cursor_on_self=False):
        global current_render_x, current_render_y

        if self.name in TAGS_SPACE_BEFORE:
            current_render_y += 1
            current_render_x = 0

        if (self.x is None) or (self.y is None):
            self.x = current_render_x
            self.y = current_render_y

            if self.name == "a":
                you_can_navigate_to_these_elements.append(self)

        format = curses.A_STANDOUT if cursor_on_self else curses.A_NORMAL
        if self.format_flags["in_a"]:

            if not cursor_on_self:
                format = curses.A_BOLD

        if self.name == "text":
            stdscr.addstr(self.y, self.x, self.inner_content, format)
            current_render_x += len(self.inner_content) + 1
        elif self.name == "img":
            if "alt" in self.attributes:
                stdscr.addstr(self.y, self.x, self.attributes["alt"], format)
                current_render_x += len(self.attributes["alt"]) + 1
            else:
                stdscr.addstr(self.y, self.x, "no img alt", format)
                current_render_x += len("no img alt") + 1

        for child_el in self.children:
            child_el.draw(stdscr, cursor_on_self=cursor_on_self)

        if self.name in TAGS_SPACE_AFTER:
            current_render_y += 1
            current_render_x = 0

    def print(self, depth=0):
        print("--" * depth + f"<{self.name}> {self.inner_content} IN_A={self.format_flags['in_a']}")
        for child_el in self.children:
            child_el.print(depth + 1)


def parse_response(res: str):
    """

    Parses headers and html and returns an array in the format:

    [HEADERS, HTML]

    :arg res: Response from webserver.
    :return: An array where the first element is a string containing the headers,
     the second element is a string containing the html.
    """

    res_headers: str
    res_html: str

    [res_headers, res_html] = res.split("\r\n\r\n")
    return res_html


def replace_entity_codes(text: str):
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&nbsp;", " ")
    text = text.replace("&quot;", '"')
    return text


def extract_html_content(raw: str, parent: Element):
    """
    Builds an array of strings of the useful content from the html raw string.
    """

    while True:
        tag_indeces = []
        min_tag_index = -1
        min_html_index = len(raw)
        found_tag = False
        for i in range(len(WHITELISTED_TAGS)):
            tag_indeces.append(raw.find('<' + WHITELISTED_TAGS[i]))

            if tag_indeces[i] == -1:
                tag_indeces[i] = len(raw)
                continue
            else:
                found_tag = True

            if tag_indeces[i] < min_html_index:
                min_html_index = tag_indeces[i]
                min_tag_index = i

        if not found_tag:
            text_el = Element("text")
            text_el.inner_content = raw
            text_el.format_flags = parent.format_flags
            parent.children.append(text_el)
            return

        tag_name: str = WHITELISTED_TAGS[min_tag_index]
        raw = raw[min_html_index:]

        if WHITELISTED_TAGS[min_tag_index] == "img":
            closing_tag_index = raw.find('>')
            img_properties = raw[:closing_tag_index]
            alt_tag_index = img_properties.find('alt')
            img_el = Element("img", children=[], attributes={})

            if alt_tag_index == -1:
                raw = raw[closing_tag_index:]
            else:
                img_el.attributes["alt"] = img_properties[alt_tag_index + 5:-1]
                raw = raw[closing_tag_index:]

            parent.children.append(img_el)

        elif WHITELISTED_TAGS[min_tag_index] == "a":
            closing_bracket_index = raw.find('>')
            a_properties = raw[:closing_bracket_index]
            href_tag_index = a_properties.find('href')
            a_el = Element("a", children=[], attributes={})
            a_el.format_flags["in_a"] = True

            if href_tag_index == -1:
                raw = raw[raw.find('</a>') + 3:]
            else:
                link = a_properties[href_tag_index + 6:-1]
                a_el.attributes["href"] = link

            raw = raw[closing_bracket_index:]
            closing_tag_index = raw.find('</a>')
            inner_content = raw[1:closing_tag_index]
            a_el.inner_content = inner_content
            raw = raw[closing_tag_index:]
            extract_html_content(inner_content, a_el)
            parent.children.append(a_el)
        else:
            raw = raw[raw.find('>') + 1:]
            closing_tag_index = raw.find(f"</{WHITELISTED_TAGS[min_tag_index]}>")

            text_content = raw[:closing_tag_index]
            txt_el = Element("text", children=[], attributes={})
            txt_el.inner_content = replace_entity_codes(text_content)

            el = Element(tag_name, children=[txt_el], attributes={})

            el.format_flags = parent.format_flags
            txt_el.format_flags = el.format_flags

            parent.children.append(el)
            raw = raw[closing_tag_index:]
            raw = raw[raw.find(">") + 1:]


def receieve(s, bytes):
    try:
        return s.recv(bytes)
    except socket.timeout:
        return False


def get_all_data(s: socket.socket):
    """
    :param s: Socket
    :return:
    """

    out = ""
    s.settimeout(0.5)
    res = receieve(s, 1024)
    while res:
        out += res.decode(encoding='latin-1')
        res = receieve(s, 1024)
        s.gettimeout()
    return out


def connect_to_server(hostname):
    context = ssl.create_default_context()
    try:
        s = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname=hostname)
    except socket.error as err:
        print(f"Socket Creation Error: {err}")

    try:
        # host_ip = socket.gethostbyname(hostname)
        pass
    except socket.gaierror:
        print("Error resolving host.")
        sys.exit(0)

    s.connect((hostname, 443))
    # cert = s.getpeercert()
    # import pprint
    # pprint.pprint(cert)
    return s


def render_page(url):
    s = connect_to_server(url.hostname)

    headers = "HTTP/1.1\r\n" \
              f"Host: {url.hostname}\r\n" \
 \
              "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
              "Chrome/79.0.3945.88 Safari/537.36\r\n" \
 \
              "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8," \
              "application/signed-exchange;v=b3;q=0.9\r\n" \
 \
              "Accept-Language: en-US,en;q=0.9\r\n" \
              "Accept-Encoding: identity\r\n\r\n"

    req = str.encode(f"GET {url.resource} {headers}")
    s.send(req)
    res = get_all_data(s)
    html = parse_response(res)

    document = Element("document", children=[], attributes={})
    extract_html_content(raw=html, parent=document)

    document.print()

    prev_index = -1
    cursor_index = -1

    if USE_CURSES:
        stdscr.clear()

        key: str = ""

        for i in range(len(document.children)):
            child = document.children[i]
            child.draw(stdscr, cursor_on_self=False)

        while True:
            KEY_ESC = "^[ "
            KEY_CONFIRM = ["\n\r", "a"]
            key = stdscr.getkey()

            if key == "j" or key == "KEY_DOWN":

                if cursor_index < len(you_can_navigate_to_these_elements) - 1:
                    prev_index = cursor_index
                    cursor_index += 1
                else:
                    continue

            elif key == "k" or key == "KEY_UP":

                if cursor_index > 0:
                    prev_index = cursor_index
                    cursor_index -= 1
                else:
                    continue

            elif key in KEY_CONFIRM:
                return URL(you_can_navigate_to_these_elements[cursor_index].attributes["href"])

            elif key in KEY_ESC:
                return None

            else:
                continue

            stdscr.addstr(20, 5, str(cursor_index), curses.A_NORMAL)
            stdscr.addstr(21, 5, str(len(you_can_navigate_to_these_elements)), curses.A_NORMAL)

            if prev_index != -1:
                you_can_navigate_to_these_elements[prev_index].draw(stdscr, cursor_on_self=False)
            you_can_navigate_to_these_elements[cursor_index].draw(stdscr, cursor_on_self=True)


if __name__ == '__main__':
    if USE_CURSES:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)

    url_input = ''
    if len(sys.argv) > 1:
        url_input = sys.argv[1]
        if url_input == "test":
            url_input = TEST_URL
    else:
        url_input = input("Hostname: ")
    url = URL(url_input)

    while url is not None:
        url = render_page(url)
        current_render_x = 0
        current_render_y = 0
        you_can_navigate_to_these_elements = []

    # Terminating
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
