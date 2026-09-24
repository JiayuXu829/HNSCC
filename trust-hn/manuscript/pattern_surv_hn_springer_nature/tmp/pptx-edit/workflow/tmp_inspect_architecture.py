import zipfile, xml.etree.ElementTree as ET
p=r'trust-hn\manuscript\pattern_surv_hn_springer_nature\tmp\pdfs\architecture\figure1_pattern_surv_hn_framework.pptx'
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with zipfile.ZipFile(p) as z:
    root=ET.fromstring(z.read('ppt/slides/slide1.xml'))
for sp in root.findall('.//p:sp',ns):
    name=sp.find('p:nvSpPr/p:cNvPr',ns).get('name')
    xfrm=sp.find('p:spPr/a:xfrm',ns); pos=''
    if xfrm is not None:
        off=xfrm.find('a:off',ns); ext=xfrm.find('a:ext',ns)
        pos=f"({int(off.get('x'))/914400:.2f},{int(off.get('y'))/914400:.2f}) {int(ext.get('cx'))/914400:.2f}x{int(ext.get('cy'))/914400:.2f}"
    texts=[''.join(t.text or '' for t in para.findall('.//a:t',ns)) for para in sp.findall('p:txBody/a:p',ns)]
    text=' | '.join(x for x in texts if x)
    if text:
        print(f"{name!r} {pos}: {text}")
