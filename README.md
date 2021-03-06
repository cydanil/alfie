# Alfie

![tests](https://github.com/cydanil/alfie/workflows/tests/badge.svg)

A List of Facts and Information ('til I find a better backronym).

Alfie is a web-application that centralises eclectic documentation and
resources in one user-friendly page.

At first glance, it may seem like a good old web directory.  
However, in places where it can, Alfie will render the documents properly.
Alfie will allow to export all documents related to a project in one click.

The aim is to hook [pandoc](https://pandoc.org/) to render documentation
written with markup languages.

## Setup

The dependencies are listed in `requirements.txt`, and should be installed
using pip:

```bash
pip install -r requirements.txt
```

The application secret should be set in the `ALFIE_SECRET` environment variable.
A good way to generate one is:

```bash
export ALFIE_SECRET=`shuf -zer -n20 {A..Z} {a..z} {0..9}`
export QUART_APP=alfie:app
```

The application is then launched using `quart`:

```bash
quart run
```

## Development

### Jinja, HTML, and CSS Conventions

The `static/css/master.css` file should be alphabetically ordered.

Object IDs in html should be formatted as `{objecttype}-{name}`, eg. `collapse-icepap-ipassign`;  `collapse-h5py`;

Jinja variables respect the Python style and are `with_underscores`, eg. `encoded_name`. When used, there should be a space between the curly-braces and the variable name: `{{ encoded_name }}`.

Closing div tags that are further than 3 lines away for the opening tag should have a comment describing which tag they refer to:

```html
<div id='flashes'>
    {% for messages in get_flashed_messages() %}
        <p class="lead">{{ message }}</p>
    {% endfor %}
</div> <!-- flashes -->
```

HTML files should be lint using [jinja-lint](https://github.com/motet-a/jinjalint)

### Testing

Testing is done with pytest and pytest-asyncio:

```bash
ALFIE_SECRET='pytest' pytest -vv --disable-pytest-warnings
```

pytest warning are disabled, as documented in [pytest-asyncio issue #141](https://github.com/pytest-dev/pytest-asyncio/issues/141)

### Sample test files source

doc and docx files come from: https://file-examples.com/index.php/sample-documents-download/sample-doc-download/

### Database

Alfie makes use of sqlite, its schema and more details are documented in [doc/database.md](doc/database.md)
