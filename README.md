# **Grew_match_quick** Documentation

## Overview

The `grew_match_quick` repository contains a Python script that configures and starts a local instance of **Grew-match** on a specified corpus or a list of corpora.

# Prerequisites

Before running **Grew-match** locally, ensure you have the following installed:

 - Git: [Git - Downloads](https://git-scm.com/downloads)
 - Ocaml & OPAM: Follow steps 1 and 2 on the [Grew installation page](https://grew.fr/usage/install).
 - Required OPAM Packages:
   - `opam remote add grew "http://opam.grew.fr"`  
   - `opam install dream dep2pictlib grew`

# Getting Started with **Grew_match_quick**

## Initial Installation

To clone the repository, run:

```
git clone https://github.com/grew-nlp/grew_match_quick.git
```

This command creates a local folder named `grew_match_quick`.

## Updating the Repository

To update your local repository with the latest changes, navigate to the `grew_match_quick` folder and run:

```
git pull
```

# Running **Grew_match_quick**

You can start **Grew_match_quick** in three ways:
 - Using a folder describing a corpus
 - Using a JSON configuration file for a single corpus
 - Using a JSON configuration file multiple corpora

Once started, the script enters a loop with a prompt for the user commands. The available commands are:
 - 's': Stop the script
 - 'r': Recompile the corpora (updates data if any corpus has been modified)
 - 'f': Force recompilation of all available corpora

## Starting with a Folder

To start **Grew-match** using a folder, run:

```
python3 grew_match_quick.py corpus_folder
```

If successful, a local Grew-match instance will be available at http://localhost:8000.

Note: The corpus should contain the data from all the files with extension `.conll` or `.conllu` at the root of the folder (files in subfolders are ignored).

By default the corpus is treated Universal Dependencies (UD) data (for the snippets and the Grew handling of edge labels).
The option `--config=sud` should be added for SUD data.

To specify right-to-left languages, add the --rtl option.

### Example

To start **Grew_match_quick** on a freshly cloned **UD_English-PUD**:

```
git clone https://github.com/UniversalDependencies/UD_English-PUD.git
python3 grew_match_quick.py UD_English-PUD
```

## Starting with a JSON File for One Corpus

A corpus can be described by a JSON object with the following keys:
 - `id`: Identifier of the corpus (used in the interface and URLs)
 - `directory`: Path of the directory where the corpus is stored (prefer absolute path)
 - `config`: Either `ud` or `sud`, indicating how edge labels should be handled

Optional keys:
 - `rtl`: Set to true for right-to-left languages
 - `audio`: Set to true for data aligned with an audio file

### Example

Using the file `examples/UD_English-ParTUT.json`:

```json
{
  "id": "UD_English-ParTUT",
  "config": "ud",
  "directory": "/Users/guillaum/resources/ud-treebanks-v2.15/UD_English-ParTUT"
}
```

Run the following command to start Grew_match_quick:

```
python3 grew_match_quick.py examples/UD_English-ParTUT.json
```

## Starting with a JSON File for Multiple Corpora

To describe multiple corpora, the JSON file should contain a list of corpus objects, each formatted as described above. Refer to the file [UD_2.15.json](https://github.com/grew-nlp/corpusbank/blob/main/UD_2.15.json) in the online Grew-match configuration for an example.

# Generated Files

 - When running the script, a local folder named `_build_grew` is created in the corresponding directory, storing all necessary files. This `_build_grew` folder can be safely deleted; it will be regenerated as needed.
 - In `grew_match_quick` folder, a subfolder named `local_files`
contains backend and frontend code, along with configuration files. This folder can be removed unless you are using the "Save" feature, as deleting it will also remove saved requests.

# Troubleshooting

## Corrupted CoNLL Data

If any CoNLL files contain errors, the corresponding sentences will be skipped, and the corpus will be built without those corrupted sentences. In such cases, a red button will appear in the interface, providing a link to a file that reports the errors.

**Example:** The folder `examples/UD_English-Error-PUD` cocontains 10 sentences, 3 of which have errors. To start Grew-match with the valid sentences, run:

```
python3 grew_match_quick.py examples/UD_English-Error-PUD
```

This command will start **Grew-match** with the 7 correct sentences and generate a log file at http://localhost:8000/meta/UD_English-Error-PUD.log containing error details, such as:

```json
{"message":"Cannot parse id zz","file":"/Users/guillaum/gitlab/grew/grew_match_quick/examples/UD_English-Error-PUD/10_sentences.conllu","sent_id":"n01001011","line":14,"library":"Conll"}
{"message":"Wrong number of fields: 9 instead of 10 expected","file":"/Users/guillaum/gitlab/grew/grew_match_quick/examples/UD_English-Error-PUD/10_sentences.conllu","sent_id":"n01003007","line":187,"library":"Conll"}
{"sent_id":"n01003013","file":"/Users/guillaum/gitlab/grew/grew_match_quick/examples/UD_English-Error-PUD/10_sentences.conllu","message":"Unknown src identifier `17`","line":258,"library":"Conll"}
```

## Port Conflicts

The application uses two ports by default:
 - Frontend: 8000
 - Backend: 8899

If either of these ports is already in use, the script will fail to start. To resolve this, you can specify alternative ports using the following arguments:
 - `--backend_port xxx`: Replace `xxx` with an available port number for the backend.
 - `--frontend_port yyy` Replace `yyy` with an available port number for the frontend (the URL will then be http://localhost:yyy).

## Additional Troubles

 - If you encounter issues, try adding the --hard option to recompile the backend from scratch.
 - :warning: stronger solution (but which erases saved patterns): `rm -rf local_files` and try again.

If the script does not work as expected, you can have a look at files in `local_files/log`, particularly `backend.stderr` and `frontend.stderr`, which contain the standard error output from the two subprocesses.

If this does not solve the issue, please report your problem [here](https://github.com/grew-nlp/grew_match_quick/issues) and include the content of `local_files/log/backend.stderr` to assist with debugging.
