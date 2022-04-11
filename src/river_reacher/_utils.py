import re
from typing import Optional, Union

from html2text import html2text


def html_to_markdown(html_string: Optional[str] = None) -> Union[str, None]:

    # ensure something to work with
    if html_string is None:
        md_str =  html_string

    else:

        # convert to markdown first, so any reasonable formatting is retained
        md_str = html2text(html_string)

        # since people love to hit the space key multiple times in stupid places, get rid of multiple space, but leave
        # newlines in there since they actually do contribute to formatting
        md_str = re.sub(r'\s{2,}', ' ', md_str)

        # apparently some people think it is a good idea to hit return more than twice...account for this foolishness
        md_str = re.sub(r'\n{3,}', '\n\n', md_str)
        md_str = re.sub('(.)\n(.)', '\g<1> \g<2>', md_str)

        # get rid of any trailing newlines at end of entire text block
        md_str = re.sub(r'\n+$', '', md_str)

        # correct any leftover standalone links
        md_str = md_str.replace('<', '[').replace('>', ']')

        # get rid of any leading or trailing spaces
        md_str = md_str.strip()

    # finally call it good
    return md_str


def get_if_match_length(match_string):
    if match_string and len(match_string):
        return match_string
    else:
        return None