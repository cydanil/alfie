import quart.flask_patch  # noqa, required by Quart.

from asyncio import get_event_loop
import os
from typing import Optional

import pypandoc
from quart import (flash, Quart, redirect, request, render_template, send_file,
                   url_for)

from definitions import (MEDIA_EXTENSIONS, OFFICE_EXTENSIONS,
                         PANDOC_EXTENTIONS)

app = Quart(__name__)
app.config['SECRET_KEY'] = os.environ['ALFIE_SECRET']


@app.route('/', defaults={'filename': None}, methods=['GET', 'POST'])
@app.route('/show/', defaults={'filename': None}, methods=['GET', 'POST'])
@app.route('/show/<path:filename>')
async def show(filename: Optional[str] = None) -> str:
    """Render a file from a URL."""

    if filename is None:  # Check if the data was received over POST
        form = await request.form
        filename = form.get('filename', None)
        if filename is not None:
            return redirect(f'{url_for("show")}/{filename}')

    if filename is None:  # It was a GET request, with no arguments
        html = await render_template('show.html')
        return html

    deg_doc = "https://deg-doc.esrf.fr/"

    if not filename.startswith(deg_doc):
        await flash(f'Only files from {deg_doc} are supported')
        html = await render_template('base.html')
        return html

    fname = filename[len(deg_doc):]
    if not fname:
        await flash('Cheeky you, not giving me a filename...')
        html = await render_template('base.html')
        return html

    fname = "/var/www/docs/" + fname
    html = await retrieve(fname)
    return html


async def retrieve(filename: str) -> str:
    """Retrieve the files from a project.

    The filename consists of a path to the file.

    Various strategies are used depending on the file type:
        - file types supported by pandoc are converted to html;
        - PDFs are rendered using an iframe, letting the browser do the work;
        - .doc files are either converted to docx (if soffice is available)
          then converted using pandoc, or else served as files to download;
        - media files are served as files.
    """
    print(filename)
    if not filename.startswith('/'):
        filename = '/' + filename

    extension = filename.split('.')[-1].lower()
    if extension in PANDOC_EXTENTIONS:
        loop = get_event_loop()
        try:
            content = await loop.run_in_executor(None,
                                                 pypandoc.convert_file,
                                                 filename,
                                                 'html')
            ret = await render_template('render.html', content=content)
        except RuntimeError as e:
            ret = await render_template('base.html')
            ret += str(e)

    elif extension in OFFICE_EXTENSIONS or extension in MEDIA_EXTENSIONS:
        ret = await send_file(filename, attachment_filename=filename)

    elif extension == 'pdf':
        await flash('This is not done yet!')
        url = url_for('pdf', filename=filename)
        content = f'<embed src="{url}" type="application/pdf#view=FitH" width="actual-width.px" height="actual-height.px"></embed>'  # noqa
        ret = await render_template('render.html', content=content)

    elif extension in ['html', 'txt']:
        try:
            with open(filename, 'r') as fin:
                content = fin.read()
            ret = await render_template('render.html', content=content)
        except FileNotFoundError:
            await flash(f'{filename}: not found!')
            ret = await render_template('base.html')

    else:
        await flash(f"{filename}: don't know what to do with this!")
        ret = await render_template('base.html')

    return ret


if __name__ == '__main__':
    app.run(host='0.0.0.0')
