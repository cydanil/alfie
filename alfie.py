import quart.flask_patch  # noqa
import base64
import io
import zipfile

from flaskext.markdown import Markdown
from quart import Quart, request, render_template, send_file

app = Quart(__name__)
app.config['SECRET_KEY'] = 'devel'

Markdown(app)
app.add_template_filter(base64.b64encode, 'b64encode')

projects = {'icepap-ipassign':
            {'README.md': '/home/cydanil/icepap-ipassign/README.md',
             'GUI README': '/home/cydanil/icepap-ipassign/ipa_gui/gui.md'},
            'alfie':
            {'Github': 'https://github.com/cydanil/alfie'},
            'rookie': {},
            'rook': {},
            'seagull': {},
            'bluejay': {},
            'pelican': {},
            'ostrich': {},
            }


@app.route('/')
async def hello():
    html = await render_template('index.html', projects=projects)
    return html


@app.route('/retrieve/<filename>')
async def retrieve(filename: bytes) -> str:
    fname = base64.b64decode(filename).decode()
    if fname.endswith('.md'):
        with open(fname, 'r') as fin:
            mkd = fin.read()
        html = await render_template('render_md.html', mkd=mkd)
    else:
        html = await render_template('base.html')
        html += fname
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
    project = request.args.get('project')
    zip_files = request.args.get('zip', default=True)
    zip_files = True if zip_files in ['True', True] else False

    print(request.args, f'zip_files: {type(zip_files)}')

    documents = projects[project]
    attachment_filename = project
    file_ = io.BytesIO()

    if zip_files:
        attachment_filename += '.zip'
        mimetype = 'application/zip'
        externals = []
        with zipfile.ZipFile(file_, 'w') as zf:
            for filename, location in documents.items():
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
                             in documents.items()])
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
