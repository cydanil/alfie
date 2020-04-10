import base64

from quart import flash, Quart, render_template

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
    html = await render_template('home.html', projects=projects)
    await flash('oi blin!')
    return html


@app.route('/retrieve/<filename>')
async def retrieve(filename: bytes) -> str:
    fname = base64.b64decode(filename)
    html = await render_template('base.html')
    html += fname.decode()
    return html


if __name__ == '__main__':
    app.run()
