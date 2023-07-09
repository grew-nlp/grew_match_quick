# **Grew-match quick**

This repository contains a Python script which configures and starts a local Grew-match instance on a corpus or a list of corpora.

## Prerequisite

To run locally Grew-match you first need to:

 - install Ocaml & opam: see steps 1 and 2 on [Grew install page](https://grew.fr/usage/install)
 - ⚠️ only for Mac (see [#16](https://github.com/ocaml/dbm/pull/16)): 
   - `opam pin dbm https://github.com/ocaml/dbm.git#master`
 - install needed opam packages:
   - `opam install ssl ocsipersist-dbm fileutils eliom dep2pictlib grew`


## Running **Grew-match quick**

There are three ways to start **Grew-match quick**:
 - with a folder describing a corpus
 - with a JSON configuration file describing one corpus
 - with a JSON configuration file describing a list of corpora

### 1. with a folder

Use one of the two commands:
```
./start.py corpus_folder
```
or
```
python3 start.py corpus_folder 
```

If you are lucky, a local Grew-match is available on http://localhost:8000.

The corpus contains the data from all the files with extention `.conll` or `.conllu` at the root of the folder (files in subfolders are not taken into account).

By default the corpus is considered to be UD data (for the snippets and the Grew handling of edge labels).
The option `--config=sud` shoud be added for SUD data.

#### Example

To start **Grew-match quick** on **UD_English-PUD**:

```
git clone https://github.com/UniversalDependencies/UD_English-PUD.git
python3 start.py UD_English-PUD
```

### 2. with a JSON file describing one corpus

A corpus can be described by a JSON object with the following keys:
 - `id`: the identifier of the corpus (the name used in the interface and some URLs)
 - `directory`: the path of the directory where the corpus is stored (prefer full path rather than realtive ones)
 - `config`: either `ud` or `sud`, indicates to Grew how edge labels should be handled
 - `snippets`: either `ud` or `sud`, defines the set of snippets shown on the right

#### Example

with a file `ex.json`:

```json
{
  "id": "SUD_English-PUD",
  "config": "sud",
  "snippets": "sud",
  "directory": "/Users/guillaum/github/bguil/SUD_English-PUD"
}
```

The command below starts **Grew-match quick** (the `--config` option is not needed as the config is given in the JSON description).

```
python3 start.py ex.json
```

### 3. with a JSON file describing a list or corpora

The expected JSON file must contains an object with the `corpora` key associated to a list of corpus, each one discribed as above.

See file [ud_2.12.json](https://gitlab.inria.fr/grew/grew_match_config/-/blob/master/corpora/ud_2.12.json) in the online Grew-match config for an example.


## In case of troubles

### Already used PORT

The application uses two ports, one for the frontend (`8000` by default) and one for the backend (`8899` by default). If one of these port is already used, the script will fail. In this case, you can use one of the two argument:
 - `--backend_port xxx` with a new availabe port number `xxx`
 - `--frontend_port yyy` with a new availabe port number `yyy` (the URL will be [http://localhost:yyy](http://localhost:yyy))

### Other troubles

If the script does not work as expected, you can have a look at files in `local_files/log`, mainly `backend.stderr` and `frontend.stderr` which contains the stderr of the two subprocesses.
If this does not solve the issue, report your problem [here](https://github.com/grew-nlp/grew_match_quick/issues) (please join the file `local_files/log/backend.stderr` to make debugging easier).