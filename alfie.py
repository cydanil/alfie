import quart.flask_patch  # noqa, required by Quart.

import io
import zipfile

from flaskext.markdown import Markdown
from quart import Quart, request, render_template, send_file

app = Quart(__name__)
app.config['SECRET_KEY'] = 'devel'

Markdown(app)

projects = {'icepap-ipassign':
            {'README': '/home/cydanil/icepap-ipassign/README.md',
             'GUI README': '/home/cydanil/icepap-ipassign/ipa_gui/gui.md'},
            'alfie':
            {'Github': 'https://github.com/cydanil/alfie'},
            'h5py':
            {'Groups': '/home/cydanil/h5py/docs/high/group.rst',
             'Files': '/home/cydanil/h5py/docs/high/file.rst',
             'Build': '/home/cydanil/h5py/docs/build.rst'},
            'rook': {},
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
    if not filename.startswith('/'):
        filename = '/' + filename

    if filename.endswith('.md'):
        with open(filename, 'r') as fin:
            mkd = fin.read()
        html = await render_template('render_md.html', mkd=mkd)
    else:
        html = await render_template('base.html')
        html += filename
    return html


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
                zf.write(location, fname)

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
