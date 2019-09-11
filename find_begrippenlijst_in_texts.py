import json
import re
import os
import subprocess

with open('extracted_texts.json', 'r') as f:
    extracted_texts = json.load(f)

extracted_texts = extracted_texts[5:6]

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
        value = None

    return (cur_key, value)


alphabetic_regex = re.compile('[^a-zA-Z0-9\s]')

# Continue where you last left off (TODO: make this work with topics/scp solution)
texts_to_evaluate = []
if os.path.exists("glossarys.json"):
    with open("glossarys.json", 'r') as f:
        current_glossarys = json.load(f)
    current_glossarys_ids = [g["id"] for g in current_glossarys]
    for doc in extracted_texts:
        if doc["id"] not in current_glossarys_ids:
            texts_to_evaluate.append(doc)
else:
    texts_to_evaluate = extracted_texts
    current_glossarys = []

all_glossarys = current_glossarys


for x in texts_to_evaluate:
    text = x["text"]
    print('\n========================================================================')
    print(x["name"], '\n')
    text2 = text[len(text)//2:]

    first_occ_index = text2.find("begrippenlijst")
    if first_occ_index == -1:
        first_occ_index = text2.find("Begrippenlijst")
    begrippenlijst_text = text2[first_occ_index:]
    begrippenlijst_text = begrippenlijst_text[begrippenlijst_text.find('\n'):]

    line = 0
    glossary = {}
    new_begrip_upcoming = False
    cur_key = None
    text_available = True
    while text_available:
        this_line = begrippenlijst_text[:begrippenlijst_text.find("\n")]
        remaining_text = begrippenlijst_text[begrippenlijst_text.find("\n")+1:]
        begrippenlijst_text = remaining_text
        print('  ', line, this_line)

        if cur_key is not None:
            cleaned_key = clean_key(cur_key)
            if glossary.get(cleaned_key) is None:
                glossary[cleaned_key] = this_line
            else:
                glossary[cleaned_key] += this_line


        if new_begrip_upcoming and this_line == next_line:
            if len(re.findall("[a-zA-Z0-9]+", this_line)) > 0:
                cur_key, value = find_key_in_line(this_line)
                if value:
                    cleaned_key = clean_key(cur_key)
                    glossary[cleaned_key] = value
                new_begrip_upcoming = False

        if len(re.findall("[a-zA-Z0-9]", this_line)) >= 0 and not new_begrip_upcoming:
            # print("< ", re.findall("[a-zA-Z0-9 ]+", begrippenlijst_text)[0], " >")
            print("")
            next_text_match = re.search("[a-zA-Z0-9(]", begrippenlijst_text)
            if next_text_match:
                after_text = begrippenlijst_text[next_text_match.start():next_text_match.start()+50].replace('\n','')

                next_text = begrippenlijst_text[next_text_match.start():]
                next_line = next_text[:next_text.find("\n")]

                print("         Context: ", after_text)
                print("<", clean_key(next_line), ">")
                choice = input("Is this a new key? (Press Enter to say accept, if its part of the description enter \"d\", if you think this is the end of the begrippenlijst enter \"q\", otherwhise anything else): ")
                if choice == "":
                    new_begrip_upcoming = True
                    cur_key = None
                elif choice == "d":
                    pass
                elif choice == "q":
                    text_available = False
                else:
                    print(">>> Retry")
                    next_line_key, _ = find_key_in_line(next_line)
                    print("<", clean_key(next_line_key), ">")
                    choice = input("Is this a new key? (Press Enter to say Yes, anything else for No): ")
                    if choice == "":
                        new_begrip_upcoming = True
                        cur_key = None
            else:
                # End of text
                text_available = False
        line += 1

    print("Begrippenlijst extracted looks like: ")
    for begrip in glossary.keys():
        print(begrip, ' - ', glossary[begrip], '\n')

    all_glossarys.append({
        "id": int(x["id"]),
        "doc_name": x["name"],
        "pdf_url": x["url"],
        "glossary": glossary
    })


    # Use a seperate file for each document
    with open("glossarys.json", 'w') as f:
        json.dump(all_glossarys, f, indent=2)













    # subprocess.call("scp glossarys.json topics:/home/cc/hieroverheid/def-extraction/glossarys.json".split())


    # x=0
    # begrippenlijst = {}
    # while x<50:
    #     (val, begrippenlijst_text) = next_new_line(begrippenlijst_text)
    #     print(x, val)
    #
    #     if len(val) < 50 and len(val) > 5:
    #         begrippenlijst[val] = next_new_line(begrippenlijst_text)[1]
    #
    #     x+=1
    #
    # print(begrippenlijst.keys())

    # while True:
    #     begrippenlijst_text = next_new_line(begrippenlijst_text)
    #     print(begrippenlijst_text)
    #
    #
    #
    #
    # alphabetic_rx = re.compile('^[a-zA-Z\s\"]+', re.MULTILINE)
    # result = alphabetic_rx.findall(begrippenlijst_text)

    #
    # print(result)
    #
    # begrippenlijst = {}
    #
    # for i, match in enumerate(alphabetic_rx.finditer(begrippenlijst_text)):
    #     if i % 2 == 0:
    #         begrippenlijst[]
    #
