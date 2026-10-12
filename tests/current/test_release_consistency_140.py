from pathlib import Path

import quietwriter


def test_stable_release_metadata():
    version = quietwriter.__version__
    assert version == '1.4.0'
    assert f'## {version} ' in Path('documents/CHANGELOG.md').read_text(encoding='utf-8')
    assert f'Application version: {version}' in Path('SNAPSHOT_INFO.txt').read_text(encoding='utf-8')
    assert f'# QuietWriter {version}' in Path('documents/RELEASE_NOTES_1.4.0.md').read_text(encoding='utf-8')


def test_public_branding_references_exist():
    import re
    for readme in ('README.md', 'README_EN.md'):
        body = Path(readme).read_text(encoding='utf-8')
        for target in re.findall(r'!\[[^]]*\]\((branding/[^)#]+)\)', body):
            assert Path(target).is_file(), f'{readme}: missing {target}'
    assert Path('CONTRIBUTING.md').is_file()
    assert Path('documents/RELEASE_PROCESS.md').is_file()
