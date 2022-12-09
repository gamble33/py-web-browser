"""

WARNING:
    WIP lexer for HTML, it is not up to standard.

TODO: Look into the Standard Generalized Markup Language (SGML)
* SGML is used to define HTML

TODO: Look into DTD (it declares elements)

"""

from typing import List
from enum import Enum


def is_name(c: chr):
    return c.isalpha() or c.isnumeric() or (c == '.') or (c == '-')


class LexException(Exception):
    pass


class TokenKind(Enum):
    OPEN_BRACKET = 1
    CLOSE_BRACKET = 2
    EQ = 3
    DOUBLE_QUOTE = 4
    SINGLE_QUOTE = 5
    FORWARD_SLAH = 6
    WHITESPACE = 7

    NAME = 8
    """ A letter followed by any number of letters, digits, periods or hyphens """

    EOF = 9


class Token:
    token_kind: TokenKind
    value: str | None

    def __init__(self, token_kind: TokenKind, value: str | None = None):
        self.token_kind = token_kind
        self.value = value

    def __str__(self):
        return f"{self.token_kind}" + (f"`{self.value}`" if self.value is not None else "")

    def __repr__(self):
        return f"{self.token_kind}" + (f": `{self.value}`" if self.value is not None else "")


class Lexer:
    src: str
    src_index: int

    def __init__(self, src: str):
        self.src = src
        self.src_index = -1

    def scan_next_token(self) -> Token:
        if self.src_index >= len(self.src) - 1:
            return Token(TokenKind.EOF)

        first_char: chr = self.consume()
        token_kind: TokenKind
        value: str | None = None
        match first_char:
            case '<':
                token_kind = TokenKind.OPEN_BRACKET
            case '>':
                token_kind = TokenKind.CLOSE_BRACKET
            case '=':
                token_kind = TokenKind.EQ
            case '\'':
                token_kind = TokenKind.SINGLE_QUOTE
            case '\"':
                token_kind = TokenKind.DOUBLE_QUOTE
            case '/':
                token_kind = TokenKind.FORWARD_SLAH
            case ' ':
                token_kind = TokenKind.WHITESPACE
                self.skip_whitespace()
            case _:
                if first_char.isalpha():
                    value = self.parse_name(first_char)
                    token_kind = TokenKind.NAME
                else:
                    raise LexException(f"Unexpected character in HTML: `{first_char}`")

        if value is not None:
            return Token(token_kind, value)
        else:
            return Token(token_kind)

    def parse_name(self, first_char: chr):
        name: str = first_char
        while is_name(self.peek()):
            name += self.consume()
        return name

    def skip_whitespace(self) -> None:
        while self.peek() == ' ':
            self.consume()

    def peek(self) -> chr:
        """
        Returns the next character in the `src` without moving the cursor.
        If there is no next character, `None` is returned.
        """
        return self.src[self.src_index + 1] if self.src_index < len(self.src) - 1 else None

    def consume(self) -> chr:
        """
        Advances the cursor and returns the next character.
        """
        self.src_index += 1
        return self.src[self.src_index]


def lex(src: str) -> List[Token]:
    lexer: Lexer = Lexer(src)
    tokens: List[Token] = []
    next_token: Token = lexer.scan_next_token()
    while next_token.token_kind is not TokenKind.EOF:
        tokens.append(next_token)
        next_token = lexer.scan_next_token()
    return tokens
