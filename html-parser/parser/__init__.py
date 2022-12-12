from .lexer import *

RAW_TAG_NAMES = [
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'p',
    'a',
    'div',
]

class ParseException(Exception):
    pass
    
class Node:
    pass

class Parser:
    tokens: List[Token]

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        
    def consume(self, token_kind: TokenKind):
        """
        Consumes a token and returns it
        """
        token = self.tokens[0]
        self.tokens = self.tokens[1:]
        return token
        
    def tag_name(self):
        token: Token = consume(TokenKind.NAME)
        if not token.value in RAW_TAG_NAMES:
            raise ParseException(f"Unkown Tag: `{token.value}`")
        else:
            return token
        
    def open_tag(self):
        consume(TokenKind.OPEN_BRACKET)
        token = self.tag_name()
        # TODO parse attributes
        consume(TokenKind.CLOSE_BRACKET)

def parse(tokens: List[Token]) -> List[Node]:
    parser = Parser(tokens)
    pass
