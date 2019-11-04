import re
import os

alphabetic_regex = re.compile('[^a-zA-Z0-9\s]')

def next_new_line(text):
    new_line = text.find("\n")
    while new_line == 0:
        text = text[new_line + 1:]
        new_line = text.find("\n")
    return (text[:new_line], text[new_line:])

def clean_key(key):
    return alphabetic_regex.sub('', key).strip()

def find_key_in_line(line):
    if "\u2013" in line:
        cur_key = line.split("\u2013")[0]
        value = line.split("\u2013")[1].strip()
    elif ":" in line:
        cur_key = line.split(":")[0]
        value = line.split(":")[1].strip()
    elif re.search(r"\s{2,}", line):
        splitted = re.split(r"\s{2,}", line)
        cur_key = splitted[0]
        value = splitted[-1]
    else:
        cur_key = line
        value = ''
    value += " "
    return (cur_key, value)

def find_value_in_line(line, custom_key):
    ind = line.find(custom_key)
    if ind == -1:
        return ' '
    else:
        return line[ind + len(custom_key):]

def clear_terminal():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def remove_linebreaks(text):
    return text.replace("\n", "")


def guess_begrippenlijst_page_number(text):
    pagenumber_search = re.search('\s+\d+\s+', text)
    if pagenumber_search is None:
        return None
    pn_text = text[pagenumber_search.start():]
    pn_search = re.search('\d+', pn_text)
    # print(pn_text[pn_search.start(): pn_search.start() + 20])
    pn_search_end = pn_text[pn_search.start():].find("\n")
    pn_search_end = re.search('\s', pn_text[pn_search.start():])
    # print(pn_search.start(), " - ", pn_search_end)
    pagenumber  = pn_text[pn_search.start() : pn_search.start() + pn_search_end.start()]
    pagenumber = int(pagenumber.strip())
    return pagenumber