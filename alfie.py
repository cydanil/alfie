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
            {'README': ('/home/cydanil/icepap-ipassign/README.md',
                        'Complete ipassign documentation'),
             'GUI README': ('/home/cydanil/icepap-ipassign/ipa_gui/gui.md',
                            'Qt Gui development documentation')},
            'alfie':
            {'Page': ('/home/cydanil/Downloads/Alfie.html',
                      'Alfie homepage')},
            'h5py':
            {'Groups': ('/home/cydanil/h5py/docs/high/group.rst',
                        'hdf5 groups manual'),
             'Files': ('/home/cydanil/h5py/docs/high/file.rst',
                       'hdf5 files manual'),
             'Build': ('/home/cydanil/h5py/docs/build.rst',
                       'hdf5 build how-to')},
            'librashpa':
            {'librashpa.pdf': ('/home/cydanil/alfie/site/librashpadoc/librashpadoc.pdf',
                               'librashpa output pdf documentation'),
             'librashpa.html': ('/home/cydanil/alfie/site/librashpadoc/html/index.html',
                                'librashpa html documentation')},
            'rook':
            {'Sample docx file': ('/home/cydanil/alfie/tests/test_data/file-sample_1MB.docx',
                                  'Test microsoft docx file handling'),
             'Sample doc file': ('/home/cydanil/alfie/tests/test_data/file-sample_1MB.doc',
                                 'Test legacy doc file handling')},
            'seagull': {'WHIST CE': ('https://alfresco.esrf.fr/share/page/site/ce-certification-wg/document-details?nodeRef=workspace://SpacesStore/789b28d6-6111-4fbd-b7dc-545406886f26',
                                     'WHIST certification documentation (alfresco)')},
            'bluejay': {},
            'pelican': {},
            'ostrich': {},
            }


@app.route('/')
@app.route('/index')
async def index():
    html = await render_template('index.html', projects=projects)
    return html


@app.route('/create', methods=['POST'])
async def create():
    """Create a new project in the database."""

    form = await request.form
    name = form.get('name')

    if name is None:
        await flash('Did not specify a project name')
    elif name in projects:
        await flash('This project already exists')
    else:
        projects[name] = {}
        await flash(f'{name} successfully added')

    ret = redirect(f'{url_for("index")}#{name}')
    return ret


@app.route('/add', methods=['POST'])
async def add():
    """Add an entry to a project.

    The arguments must be:
        project str: the name of the project where to add the new entry to
        name str: the name/key of the entry in the project.
                  This name will be used when exporting the project.
        location str: the document's URI
        description str: a short summary of the file. Typically used to get
                        a quick glance of the file. This is also used when
                        searching.
    """
    form = await request.form

    try:
        project = form['project']
        name = form['name']
        loc = form['location']
        description = form.get('description', '')
    except KeyError:
        await flash('Could not add content')
    else:
        projects[project][name] = (loc, description)

    ret = redirect(f'{url_for("index")}#{project}')
    return ret


@app.route('/remove', methods=['POST'])
async def remove():
    """Remove an entry from a project.

    This post method expects the keys `project` and `document` in it, both
    strings.
    The document should refer to a key within the project.
    """
    form = await request.form

    try:
        document = form['document']
        project = form['project']

        projects[project].pop(document)
    except KeyError:
        await flash('Could not remove document')
    else:
        await flash(f'{document} removed from {project}')

    ret = redirect(f'{url_for("index")}#{project}')
    return ret


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
            for filename, (location, description) in project.items():
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
        content = '\n'.join([f'{fname}: {loc}' for fname, (loc, _)
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
