import zipfile, xml.etree.ElementTree as ET
p=r'trust-hn\manuscript\pattern_surv_hn_springer_nature\figures\figure1_pattern_surv_hn_framework.pptx'
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
targets={'PN_text_006_text','PN_text_007_text','PN_text_008_text','PN_text_009_text','PN_text_039_text','PN_text_042_text','PN_text_172_text','PN_text_190_text','PN_text_215_text','PN_text_216_text','PN_text_246_text','PN_text_262_text','PN_text_281_text','PN_text_289_text','PN_text_291_text','PN_text_293_text','PN_text_294_text'}
with zipfile.ZipFile(p) as z: root=ET.fromstring(z.read('ppt/slides/slide1.xml'))
for sp in root.findall('.//p:sp',ns):
    name=sp.find('p:nvSpPr/p:cNvPr',ns).get('name')
    if name not in targets: continue
    print('\n',name)
    for para in sp.findall('p:txBody/a:p',ns):
        print(' paragraph')
        for run in para.findall('a:r',ns):
            texts=[t.text or '' for t in run.findall('a:t',ns)]
            props=run.find('a:rPr',ns)
            baseline=props.get('baseline') if props is not None else None
            print('  run',repr(texts),'baseline',baseline)
