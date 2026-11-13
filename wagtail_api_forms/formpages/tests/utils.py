import re


def page_title(html):
    """The text of the page's <title>, with whitespace collapsed."""
    title = re.search(r"<title>(.*?)</title>", html, re.DOTALL).group(1)
    return " ".join(title.split())
