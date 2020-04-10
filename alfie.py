import base64
import io
import zipfile

from quart import Quart, render_template, send_file

app = Quart(__name__)
app.config['SECRET_KEY'] = 'devel'

app.add_template_filter(base64.b64encode, 'b64encode')

projects = {'icepap-ipassign':
            {'README.md': '/home/cydanil/icepap-ipassign/README.md',
             'GUI README': '/home/cydanil/icepap-ipassign/ipa_gui/gui.md'},
            'alfie': {}
            }


@app.route('/')
async def hello():
    html = await render_template('index.html', projects=projects)
    return html


@app.route('/retrieve/<filename>')
async def retrieve(filename: bytes) -> str:
    fname = base64.b64decode(filename)
    html = await render_template('base.html')
    html += fname.decode()
    return html


@app.route('/download/<project_name>')
async def download(project_name: str):
    documents = projects[project_name]

    file_ = io.BytesIO()
    with zipfile.ZipFile(file_, 'w') as zf:
        for filename, location in documents.items():
            fname = filename.replace(' ', '_')
            fname_ext = fname.split('.')[-1]
            loc_ext = location.split('.')[-1]
            if fname_ext != loc_ext:
                fname = f'{fname}.{loc_ext}'
            zf.write(location, fname)
    file_.seek(0)
    ret = await send_file(file_,
                          attachment_filename=f'{project_name}.zip',
                          as_attachment=True)
    return ret


if __name__ == '__main__':
    app.run()
