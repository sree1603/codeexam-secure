import io
import keyword
import tokenize


def normalize_tokens(source):
    """
    Convert Python source code into normalized tokens.

    Comments, whitespace, newlines and indentation are ignored.
    Variable names, numbers and strings are replaced with placeholders.
    Python keywords and operators are preserved.
    """
    normalized = []

    ignored = {
        tokenize.COMMENT,
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENDMARKER,
        tokenize.ENCODING,
    }

    tokens = tokenize.generate_tokens(io.StringIO(source).readline)

    for token in tokens:
        if token.type in ignored:
            continue

        if token.type == tokenize.NAME:
            if keyword.iskeyword(token.string):
                normalized.append(token.string)
            else:
                normalized.append("ID")

        elif token.type == tokenize.NUMBER:
            normalized.append("NUM")

        elif token.type == tokenize.STRING:
            normalized.append("STR")

        elif token.type == tokenize.OP:
            normalized.append(token.string)

    return normalized


def safe_tokens(source):
    """Like normalize_tokens, but returns [] when the code cannot be tokenized.

    Students may submit broken code (an unclosed bracket, bad indentation).
    One broken submission must not crash the whole similarity report.
    """
    try:
        return normalize_tokens(source)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return []


def ngrams(tokens, n=5):
    """Return a set of consecutive n-token groups."""
    if n <= 0:
        raise ValueError("n must be greater than zero")

    return {
        tuple(tokens[i:i + n])
        for i in range(len(tokens) - n + 1)
    }


def similarity(a, b):
    """Calculate Jaccard similarity between two token sequences."""
    set_a = ngrams(a)
    set_b = ngrams(b)

    union = set_a | set_b

    if not union:
        return 0.0

    return len(set_a & set_b) / len(union)
