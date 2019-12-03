# Topic Mining for HierOverheid

## Initial Setup
Create an `oauth_credentials.py` file in the project root with the following structure:

```python
client_id       = "my_TAPI_client_id"
client_secret   = "my_TAPI_client_secret"
```

## Abbreviation Mining

```shell script
$ python make_abbreviation_hoards.py -h
usage: make_abbreviation_hoards.py [-h] [--all] [doc_id [doc_id ...]]

Update word hoards with abbreviation topics.

positional arguments:
  doc_id      Any number of orid:<doc_id>s

optional arguments:
  -h, --help  show this help message and exit
  --all       update the hoards for all existing documents 
      |       (instead of for <doc_id>s)
```

A prerequisite for abbreviation mining is that documents have been uploaded to the TAPI.
The `new_batches.py` script can be used to identify batches of documents that have not yet been loaded.
This can be used as the basis of a loading and mining pipeline.

The following shell command uses GNU Parallel. 
On Ubuntu, it can be installed with `sudo apt install parallel`.
This has only been tested on Ubuntu 18.04.
```shell script
./new_batches.py | parallel --jobs=2 --colsep=' ' --lb './upload_document.py --quiet {} && ./make_abbreviation_hoards.py {}' > osi-hoards.log
```

> O. Tange (2011): GNU Parallel - The Command-Line Power Tool, 
> ;login: The USENIX Magazine, February 2011:42-47.

## Definition Mining

Run `python extract_texts.py` to extract texts first.

### Extracting the glossaries

- Install `evince` pdf viewer using `sudo snap install evince`

- Then use `find_glossary_in_texts.py` to find the glossaries


### Commands in app

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
