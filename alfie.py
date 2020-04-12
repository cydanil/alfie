import quart.flask_patch  # noqa
import base64
import io
import zipfile

from flaskext.markdown import Markdown
from quart import Quart, render_template, send_file

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


@app.route('/download/<project_name>')
async def download(project_name: str):
    """Create a zip archive of a project.

    Zip the files from the storage path.
    External resources (ie. link) are compiled into a external_resources.txt
    file.
    """
    documents = projects[project_name]

    file_ = io.BytesIO()
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
            content = '\n'.join(f'{name}: {uri}' for name, uri in externals)
            zf.writestr('external_resources.txt', content)

    file_.seek(0)
    ret = await send_file(file_,
                          attachment_filename=f'{project_name}.zip',
                          as_attachment=True)
    return ret


if __name__ == '__main__':
    app.run(host='0.0.0.0')
