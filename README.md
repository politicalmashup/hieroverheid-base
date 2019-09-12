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

Then use `find_glossary_in_texts.py` to find the glossarys