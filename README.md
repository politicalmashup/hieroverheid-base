# Topic Mining for HierOverheid

## Initial Setup
Requires Python version >= 3.7.

Clone this repository and install packages with `pip install -r requirements.txt`.

Create a `.env` file in the project root with the following structure:

```shell script
TAPI_CLIENT_ID="my_TAPI_client_id"
TAPI_CLIENT_SECRET="my_TAPI_client_secret"
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

### Load new documents from scratch
A prerequisite for abbreviation mining is that documents have been uploaded to the Topics API (TAPI).
The `new_batches.py` script can be used to identify batches of documents that have not yet been loaded.
This can be used as the basis of a loading and mining pipeline.

The following shell command uses GNU Parallel. 
On Ubuntu, it can be installed with `sudo apt install parallel`.
This has only been tested on Ubuntu 18.04.

```shell script
{ ./new_batches.py 'osi_*' | parallel --jobs=2 --colsep=' ' --lb './upload_document.py --quiet {} && ./make_abbreviation_hoards.py {}'; } 2> >(tee "logs/osi-load-$(date +"%Y%m%dT%H%M").err.log") > "logs/osi-hoards-$(date +"%Y%m%dT%H%M").log"
```

> O. Tange (2011): GNU Parallel - The Command-Line Power Tool, 
> ;login: The USENIX Magazine, February 2011:42-47.

In the example above, the output of the command is redirected to log files.
The `stderr` output is simultaneously written to the terminal and to a `.err.log` file.
The `stdout` output is only written to a log file.

After running this command multiple times, log files will accumulate.
For convenience, the following commands are provided to check on the latest log/progress:
 ```shell script
tail -f $(ls -t logs/osi-hoards* | head -1)
tail -f $(ls -t logs/osi-load* | head -1)
```

The following sections deal with each individual process in the pipeline.

### Find batches of new documents

```shell script
$ ./new_batches.py -h
usage: new_batches.py [-h] [--revisit] [index_filter]

Update index state and return ORIDs of documents that are not in the TAPI.

positional arguments:
  index_filter  Elasticsearch index filter (also used for index-state glob)

optional arguments:
  -h, --help    show this help message and exit
  --revisit     check if old batches are present in the TAPI, and print their
                non-loaded tails
```

This program scans the Open Raadsinformatie search indexes, and writes IDs of all
usable documents to files in the `index-state/` directory. The format used for these files
is plain text, and separates IDs by whitespace and batches of documents by newlines.
To qualify, documents must contain at least one page of extracted text.

Subsequently, for each state file that matches the given index filter,
the desired end result is that for each listed ID, there exists a corresponding
document in the TAPI. Each batch (i.e. line) in the state file is tested to
find out how much of it has already been imported. The (parts of) batches that
have not been loaded are printed to stdout for use in other programs.

By default, only identifiers with a higher numerical value than the ones
already present in the TAPI will be printed. If batches other than the last (within one file)
may have not fully loaded (e.g. due to a failure while loading in parallel),
the option `--revisit` can be used to identify and print them.

The simple format of the index state files allows for the use of existing tools
to inspect them. The `wc` utility, for example, can be used to count the number of
valid document IDs per index:

```shell script
$ wc -w index-state/osi_*.ids
 19955 index-state/osi_limburg.29266.ids
 19587 index-state/osi_noord-holland.33622.ids
  4813 index-state/osi_overijssel.9496.ids
 16799 index-state/osi_zuid-holland.27450.ids
 61154 total
```

### Upload documents to the TAPI
The documents provided by openraadsinformatie.nl and openstateninformatie.nl need to
be uploaded to the Topics API (TAPI). The following program downloads the plain text
body of documents with known identifiers, and inserts them into the TAPI while preserving their IDs. 

```shell script
$ ./upload_document.py -h
usage: upload_document.py [-h] [--quiet] doc_id [doc_id ...]

Upload Open Raadsinformatie documents to the TAPI.

positional arguments:
  doc_id      One or more orid:<doc_id>s

optional arguments:
  -h, --help  show this help message and exit
  --quiet     suppress messages to stdout; only write error output
```

### Update hoards for existing documents
When all documents from an index have been uploaded to the TAPI,
their corresponding word hoards may be updated with the following command:

```shell script
./make_abbreviation_hoards.py --index='osi_*'
```

Logging the output to files can be approached in the same way
as for the loading and mining pipeline.
When inspecting the error log, the output of the progress bar may cause visual clutter.
A cleaner version of this log can be viewed with `col -b < my-errors.err.log | less`.


## Power User Recipes
This is a collection of commands that have proven useful,
but which should also be approached with caution.

### Delete word hoards and topics
To delete Word Hoards and their contained topics for all documents
listed in an index-state file:

```shell script
cat index-state/<index-name>.ids | parallel --jobs=4 --colsep=' ' --lb './delete_doc_hoards.py --and-topics --non-interactive {}'
```

Particular care should be taken with the `--and-topics` argument:
since topics can be designated in multiple hoards, deleting all
topics that are designated in a hoard that is meant to be deleted,
may also cause topics to disappear from hoards that are preserved.

### Parallel abbreviation hoard updates

To achieve roughly the same as with `./make_abbreviation_hoards.py --index`,
but in parallel:

```shell script
cat index-state/<index-name>.ids | parallel --jobs=4 --colsep=' ' --lb './make_abbreviation_hoards.py {}'
```
