import lexer
import parser

""" 
Test
"""
tokens = lexer.lex('<html> lol </html>')
dom = parse(tokens)
print(dom)
""" 
Test
"""