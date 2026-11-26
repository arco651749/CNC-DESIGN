# -*- coding: utf-8 -*-
"""Artifact-ready version of the 3D page (theme tokens, no html/head/body wrapper).  python3 column_box/build_artifact.py"""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
p = open(os.path.join(HERE, 'column_box_3d.html'), encoding='utf-8').read()
style = re.search(r'<style>(.*?)</style>', p, re.S).group(1)
body = p[p.index('<body>') + 6:p.rindex('</body>')]
style = (style.replace('background:#eef1f4', 'background:var(--bg)').replace('color:#1d2630', 'color:var(--fg)').replace('#ffffffe6', 'var(--panel)')
         .replace('#c9d1da', 'var(--line)').replace('background:#fff;cursor', 'background:var(--panel);color:var(--fg);cursor').replace('border:1px solid #9aa6b3', 'border:1px solid var(--line)')
         .replace('left:12px', 'left:max(16px,env(safe-area-inset-left,0px))').replace('#1d2630', 'var(--fg)'))
tokens = ''':root{--bg:#eef1f4;--fg:#1d2630;--panel:#ffffffe6;--line:#c3ccd6;--sceneBg:0xeef1f4}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#171c22;--fg:#e6ebf0;--panel:#222a33e6;--line:#3a4552;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#171c22;--fg:#e6ebf0;--panel:#222a33e6;--line:#3a4552;color-scheme:dark}
html,body{height:100%}body{background:var(--bg);color:var(--fg)}
'''
body = body.replace('scene.background=new THREE.Color(0xeef1f4)', "scene.background=new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()||'#eef1f4')")
out = '<title>立柱電箱 3D</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n<style>' + tokens + style + '</style>\n' + body
open(os.path.join(HERE, 'column_box_3d_artifact.html'), 'w', encoding='utf-8').write(out)
print('MB %.1f' % (len(out) / 1e6))
