from pathlib import Path

path = Path(__file__).parent.joinpath('..').resolve()


def test_css_ordered():
    master = path / 'static' / 'css' / 'master.css'

    with open(master, 'r') as fin:
        css = [l.strip('.') for l in fin.readlines() if '{' in l]

    print(sorted(css))

    print(css)

    assert sorted(css) == css
