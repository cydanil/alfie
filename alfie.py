import quart.flask_patch  # noqa, required by Quart.

from asyncio import get_event_loop
import io
import os
import zipfile

import pypandoc
from quart import (flash, Quart, redirect, request, render_template, send_file,
                   url_for)

from definitions import (MEDIA_EXTENSIONS, OFFICE_EXTENSIONS,
                         PANDOC_EXTENTIONS)

app = Quart(__name__)
app.config['SECRET_KEY'] = os.environ['ALFIE_SECRET']

projects = {'icepap-ipassign':
            {'README': '/home/cydanil/icepap-ipassign/README.md',
             'GUI README': '/home/cydanil/icepap-ipassign/ipa_gui/gui.md'},
            'alfie':
            {'Github': 'https://github.com/cydanil/alfie',
             'Page': '/home/cydanil/Downloads/Alfie.html'},
            'h5py':
            {'Groups': '/home/cydanil/h5py/docs/high/group.rst',
             'Files': '/home/cydanil/h5py/docs/high/file.rst',
             'Build': '/home/cydanil/h5py/docs/build.rst'},
            'librashpa':
            {'librashpa.pdf': '/home/cydanil/alfie/site/librashpadoc/librashpadoc.pdf',
             'librashpa.html': '/home/cydanil/alfie/site/librashpadoc/html/index.html'},
            'rook':
            {'Sample docx file': '/home/cydanil/alfie/tests/test_data/file-sample_1MB.docx',
             'Sample doc file': '/home/cydanil/alfie/tests/test_data/file-sample_1MB.doc'},
            'seagull': {},
            'bluejay': {},
            'pelican': {},
            'ostrich': {},
            }


@app.route('/')
async def index():
    html = await render_template('index.html', projects=projects)
    return html


@app.route('/retrieve/<path:filename>')
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
        content = f'<embed src="{url}" type="application/pdf#view=FitH" width="actual-width.px" height="actual-height.px"></embed>'
        ret = await render_template('render.html', content=content)

    elif extension == 'html':
        with open(filename, 'r') as fin:
            content = fin.read()
        ret = await render_template('render.html', content=content)
    else:
        return

    return ret


@app.route('/add', methods=['POST'])
async def add():
    """Add an entry to a project."""

    content = await request.form

    try:
        project_name = content['project']
        name = content['name']
        location = content['location']
        # description = content['description']
    except KeyError:
        print(content, content.keys())
        await flash('Could not add content')
    else:
        projects[project_name][name] = location

    # TODO: redirect to the correct card in accordion
    ret = redirect(url_for('index'))
    return ret


@app.route('/pdf/<path:filename>')
async def pdf(filename=None):
    if filename is None:
        return
    if not filename.startswith('/'):
        filename = '/' + filename

    ret = await send_file(filename,
                          attachment_filename=filename,
                          mimetype='application/pdf',
                          as_attachment=False)
    return ret


@app.route('/export')
async def export():
    """Export the project for download.

    This url expect the project name as `project`, and an optional `zip`
    boolean.

    If `zip` is set, zip the files from the storage path.
    External resources (ie. link) are then compiled into an
    `external_resources.txt` file, itself appended to the archive.
    Its format will be 'resource_name: resource_location'.

    If `zip` is unset, then all resources in the project will be listed in
    a text file in the same format as above, and this text file will be served
    to the user.
    """
    project_name = request.args.get('project')
    zip_files = request.args.get('zip', default=True)
    zip_files = True if zip_files in ['True', True] else False

    project = projects[project_name]
    attachment_filename = project_name
    file_ = io.BytesIO()

    if zip_files:
        attachment_filename += '.zip'
        mimetype = 'application/zip'
        externals = []
        with zipfile.ZipFile(file_, 'w') as zf:
            for filename, location in project.items():
                if location.startswith('http'):
                    externals.append((filename, location))
                    continue
                # Sanitize the file name
                fname = filename.replace(' ', '_')
                fname_ext = fname.split('.')[-1]
                loc_ext = location.split('.')[-1]
                if fname_ext != loc_ext:
                    fname = f'{fname}.{loc_ext}'
                # Write the file
                try:
                    zf.write(location, fname)
                except FileNotFoundError:
                    continue  # TODO: flash a message

            # Handle external resources
            if externals:
                zf.writestr('external_resources.txt',
                            '\n'.join(f'{n}: {uri}' for n, uri in externals))
    else:
        attachment_filename += '.txt'
        content = '\n'.join([f'{fname}: {loc}' for fname, loc
                             in project.items()])
        file_.write(content.encode())
        mimetype = 'text/csv'

    file_.seek(0)
    ret = await send_file(file_,
                          attachment_filename=attachment_filename,
                          mimetype=mimetype,
                          as_attachment=True)
    return ret


if __name__ == '__main__':
    app.run(host='0.0.0.0')
