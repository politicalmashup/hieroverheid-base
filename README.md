# PDF Extraction for WaarOverheid

## How to use
Create a `credentials.json` file in the project root with the following structure:

```
{
    "username": "my_tapi_username",
    "password": "my_tapi_password"
}
```

Run `python extract_texts.py` to extract texts first.

### Extracting the glossarys

- Install `evince` pdf viewer using `sudo snap install evince`

- Then use `find_glossary_in_texts.py` to find the glossarys


## Commands in app

```
Menu commands:
    y - yes.
    n - no.
    q - skip this document.
    r - redo last glossary item.
    h - print these commands.
    x - exit the program.

Text evaluation commands:
    q - identify end of glossary.
    d - add current line to current glossary item.
    c - print text surrounding the current line when in doubt.
    h - print these commands.

    n (or any other) - reject current text as a new glossary item. Will lead to retry.
    y (or no input) - accept current text as a new glossary item.

Retry commands:
    n (or any other) - reject current text as a new glossary item. Will skip this line.
    y (or no input) - accept current text as a new glossary item.
```