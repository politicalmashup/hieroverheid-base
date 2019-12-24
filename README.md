# Topic Mining for HierOverheid

## Initial Setup
Requires Python version >= 3.7.

Clone this repository and install packages with `pip install -r requirements.txt`.

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

### Loading new documents from scratch
A prerequisite for abbreviation mining is that documents have been uploaded to the TAPI.
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

### Updating hoards for existing documents
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

To achieve roughly the same as with `./make_abbreviation_hoards.py --index`,
but in parallel:

```shell script
cat index-state/<index-name>.ids | parallel --jobs=4 --colsep=' ' --lb './make_abbreviation_hoards.py {}'
```
