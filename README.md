# Topic Mining for HierOverheid

## Initial Setup
Create an `oauth_credentials.py` file in the project root with the following structure:

```python
client_id       = "my_TAPI_client_id"
client_secret   = "my_TAPI_client_secret"
```

## Abbreviation Mining

```shell script
$ ./make_abbreviation_hoards.py -h
usage: make_abbreviation_hoards.py [-h] [--index INDEX] [doc_id [doc_id ...]]

Update word hoards with abbreviation topics.

positional arguments:
  doc_id         Any number of orid:<doc_id>s

optional arguments:
  -h, --help     show this help message and exit
  --index INDEX  update all hoards for the given index filter
```

A prerequisite for abbreviation mining is that documents have been uploaded to the TAPI.
The `new_batches.py` script can be used to identify batches of documents that have not yet been loaded.
This can be used as the basis of a loading and mining pipeline.

The following shell command uses GNU Parallel. 
On Ubuntu, it can be installed with `sudo apt install parallel`.
This has only been tested on Ubuntu 18.04.

```shell script
./new_batches.py 'osi_*' | parallel --jobs=2 --colsep=' ' --lb './upload_document.py --quiet {} && ./make_abbreviation_hoards.py {}' 2> >(tee "logs/osi-load-$(date +"%Y%m%dT%H%M").err.log") > "logs/osi-hoards-$(date +"%Y%m%dT%H%M").log"
```

> O. Tange (2011): GNU Parallel - The Command-Line Power Tool, 
> ;login: The USENIX Magazine, February 2011:42-47.

In the example above, the output of the command is redirected to log files.
The `stderr` output is simultaneously written to the terminal and to a `.err.log` file.
The `stdout` output is only written to a log file.

When inspecting the error log, the output of the progress bar may cause visual clutter.
A cleaner version of this log can be viewed with `col -b < my-errors.err.log | less`.

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

## Power User Recipes

This is a collection of commands that have proven useful,
but which should also be approached with caution.

### Abbreviation mining

To delete Word Hoards and their contained topics for all documents
listed in an index-state file:

```shell script
cat index-state/<index-name>.ids | parallel --jobs=4 --colsep=' ' --lb './delete_doc_hoards.py --and-topics --non-interactive {}'
```

Particular care should be taken with the `--and-topics` argument:
since topics can be designated in multiple hoards, deleting all
topics that are designated in a hoard that is meant to be deleted,
may also cause topics to disappear from hoards that are preserved.
