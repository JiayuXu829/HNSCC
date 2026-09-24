import re
p=r'trust-hn\manuscript\pattern_surv_hn_springer_nature\tmp\pptx-edit\figure1_bbox.html'
s=open(p,'rb').read().decode('utf-8','ignore')
for line in s.splitlines():
    m=re.search(r'xMin="([0-9.]+)" yMin="([0-9.]+)" xMax="([0-9.]+)" yMax="([0-9.]+)">([^<]+)<',line)
    if m and any(k in m.group(5) for k in ['contract','Permutation-invariant','Nested','Governed','Exploratory','reliability','raw-SCRF','pathway','fallback','usable']):
        print(m.groups())
