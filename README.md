# Alfie

A List of Facts and Information ('til I find a better backronym).

Alfie is a web-application that centralises eclectic documentation and
resources in one user-friendly page.

At first glance, it may seem like a good old web directory.  
However, in places where it can, Alfie will render the documents properly.
Alfie will allow to export all documents related to a project in one click.

The aim is to hook [pandoc](https://pandoc.org/) up to convert and store the
documents in one unified format.

# Jinja, HTML, and CSS Conventions

The `static/css/master.css` file should be alphabetically ordered.

Object IDs in html should be formatted as `{objecttype}-{name}`, eg. `collapse-icepap-ipassign`; `collapse-h5py`;

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
