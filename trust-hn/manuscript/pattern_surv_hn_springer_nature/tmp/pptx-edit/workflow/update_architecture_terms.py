from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path('trust-hn/manuscript/pattern_surv_hn_springer_nature')
source = root / 'figures/figure1_pattern_surv_hn_framework.pptx'
build_dir = root / 'tmp/pptx-edit'
build_dir.mkdir(parents=True, exist_ok=True)
output = build_dir / 'figure1_pattern_surv_hn_framework.pptx'

replacements = [
    ('a  Inputs and encoders', 'a  Inputs and evidence contract', 1),
    ('b  Residual Deep Sets', 'b  Permutation-invariant residual', 1),
    ('c  Residual fusion and training', 'c  Nested shrinkage control', 1),
    ('d  Prediction paths', 'd  Governed prediction paths', 1),
    ('Cox V0', 'Cox CAM', 1),
    ('V0', 'CAM', 3),
    ('Raw V1R score', 'Raw SCRF score', 1),
    ('V1R', 'SCRF', 1),
    ('Primary raw V1R', 'Primary raw SCRF', 1),
    ('Planned reliability router', 'Exploratory reliability router', 1),
    ('V0 EXACT', 'CAM EXACT', 1),
    ('primary path', 'primary raw-SCRF path', 1),
    ('optional/development layer', 'optional evidence pathway', 1),
    ('exact fallback', 'exact CAM fallback', 1),
]

with ZipFile(source, 'r') as zin:
    slide_xml = zin.read('ppt/slides/slide1.xml').decode('utf-8')
    for old, new, expected in replacements:
        old_xml = f'<a:t>{old}</a:t>'
        new_xml = f'<a:t>{new}</a:t>'
        occurrences = slide_xml.count(old_xml)
        if occurrences != expected:
            raise RuntimeError(f'Expected {expected} occurrences of {old!r}, found {occurrences}')
        slide_xml = slide_xml.replace(old_xml, new_xml)

    subscript_replacements = {
        '<a:t>S</a:t>': '<a:t>M</a:t>',
        '<a:t>|S</a:t>': '<a:t>|M</a:t>',
        '<a:t>⊕ addition · × shrinkage · S</a:t>': '<a:t>⊕ addition · × shrinkage · M</a:t>',
    }
    for old, new in subscript_replacements.items():
        occurrences = slide_xml.count(old)
        if occurrences != 1:
            raise RuntimeError(f'Expected exactly one occurrence of {old!r}, found {occurrences}')
        slide_xml = slide_xml.replace(old, new)

    with ZipFile(output, 'w', compression=ZIP_DEFLATED, compresslevel=9) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == 'ppt/slides/slide1.xml':
                data = slide_xml.encode('utf-8')
            zout.writestr(item, data)

print(output)
