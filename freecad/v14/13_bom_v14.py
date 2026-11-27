# -*- coding: utf-8 -*-
"""v14 bill of materials from the model (machine on the coolant base): one row per distinct part (same group + same spec),
quantity counted, category guessed from the part (CNC part with a DXF / standard fastener or pin / purchased / cast-in epoxy),
plus PURCHASE details (supplier, part number, link, notes) for bought items that the model only shows as an envelope.
Run:  freecadcmd freecad/v14/13_bom_v14.py      Out: output/v14/CNC_v14_BOM.csv (UTF-8 with BOM, opens in Excel)"""
import os, re, csv
import FreeCAD as App

ROOT = os.environ.get('CNC_ROOT') or r'D:\Claude\CNC DESIGN'
doc = App.openDocument(os.path.join(ROOT, 'output', 'v14', 'CNC_v14_base.FCStd'))
OUT = os.path.join(ROOT, 'output', 'v14', 'CNC_v14_BOM.csv')

# purchased items: model label -> details (kept here so a rebuild of the model never loses them)
PURCHASE = {
    'Probe_slide_body': {
        'supplier': 'SMC', 'part_no': 'MXH10-60Z-M9NW (2 x D-M9NW auto switch)',
        'link': 'https://motion.com/products/sku/06714549',
        'desc': 'compact slide bore 10, stroke 60 (MXH catalog p.31: section 20 x 47, body 95, overall 106.5 retracted, table 99 x 19, ports M5); vendor STEP in vendor/smc/MXH10-60Z',
        'note': 'owner-selected (replaces MXH2 10-60). SMC lists MXH-Z as discontinued end of March 2027: order spares in time, MXH2 10-60 is the '
                'successor (table 5 longer). Probe up / down, mounted on its side on the probe bracket. Extended = end of stroke; probe height set '
                'in the shank clamp. Valve: 5/2 single solenoid, spring return (retract on power loss)',
    },
    'Mirror_cover_actuator': {
        'supplier': 'SMC', 'part_no': 'CDQ2B12-30DZ (+ 1 x D-M9 auto switch = cover open)',
        'link': 'https://ca01.smcworld.com/catalog/en/actuator/CQ2-CDQ2-Z-E/6-2-1-p0763-0980-cq2_en/data/6-2-1-p0763-0980-cq2_en.pdf',
        'desc': 'compact cylinder bore 12, stroke 30, with magnet (catalog p.787: square 25 x 58, rod D6 / M3 internal thread, 2 x through-holes D3.5 on the diagonal, ports M5); vendor STEP in vendor/smc/CDQ2B12-30DZ',
        'note': 'slides the prism cover 30 toward +Y for tool setting; air via the Y drag chain',
    },
    'Camera_lens': {
        'supplier': 'MORITEX', 'part_no': 'MML04-HR120D', 'link': 'https://www.moritex.com/Lens/215_9580.html',
        'desc': 'object-side telecentric lens 0.4x, WD 120+-3.6, DOF 5.3, coaxial illumination port (D)',
        'note': 'owner-selected (replaces MML05-HR110D: 10 more WD -> camera 15 higher). Datasheet, drawing and STEP in vendor/moritex/MML04-HR120D',
    },
    'Probe_body': {
        'supplier': 'Amazon (XUNKUANER)', 'part_no': 'ASIN B0FWXWX7CT',
        'link': 'https://www.amazon.com/dp/B0FWXWX7CT',
        'desc': '3D touch probe / edge finder (尋邊器) for Mach3 / GRBL: repeatable, mm shank, tungsten-steel ball tip, DC 5-24 V, NPN NO',
        'note': 'owner-selected. NPN NO: a broken wire reads "not triggered" -> prefer an NC version if available, otherwise check '
                'the probe input before every probing cycle. Wire to the grblHAL probe input (not the MR-J4)',
    },
}

DXF_PARTS = set()
try:
    src = open(os.path.join(ROOT, 'freecad', 'v14', '09_dxf_extract_v14.py'), encoding='utf-8').read()
    DXF_PARTS = set(re.findall(r"\('([A-Za-z0-9_]+)', \d+\)", src[src.index('PARTS = ['):src.index(']', src.index('PARTS = ['))]))
except Exception:
    pass
group_of = {}
for g in doc.Objects:
    if g.TypeId == 'App::DocumentObjectGroup':
        for o in g.Group: group_of[o.Name] = g.Label

def category(o, spec):
    n = o.Label
    if n in PURCHASE: return '外購件'
    if n == 'Probe_slide_table': return '外購件（含於 MXH10-60Z，不另購）'
    if 'epoxy' in n.lower(): return '環氧樹脂（現場灌注）'
    if 'SPHC' in spec: return '自製鈑金件（見 DXF，雷射切割 + 折彎）'
    if n == 'Feeder_opbox_cable': return '電線（列在配電 session 的 BOM）'
    if n.startswith('Box_top_shim'): return '自製墊片（見 DXF，雷射切割）'
    if n in DXF_PARTS or re.sub(r'_\d+$', '', n) in DXF_PARTS: return '自製 CNC 件（見 DXF）'
    if re.search(r'(bolt|screw|_pin|dowel|stud|jack|_nut$|shim)', n, re.I) and not re.search(r'(ballscrew|ball_nut)', n): return '標準件 / 螺絲銷'
    if re.search(r'(MISUMI|SMC|Moritex|Basler|Mitsubishi|HG-KR|vendor STEP|C-TEK|C-TEF|C-KBS|SX2R|C-HLG|HFS8|CPJC|RBPB|TERAL|VKP|KSS)', spec + ' ' + n, re.I):
        return '外購件'
    if re.search(r'(extrusion|SUS|sheet|guard|pan|tank|hose|castor|foot|leg|filter|PC t4)', spec + ' ' + n, re.I): return '外購 / 板金 / 鋁擠'
    return '自製 / 其他'

rows = {}
for o in doc.Objects:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull(): continue
    spec = (o.Spec if 'Spec' in o.PropertiesList else '').strip()
    grp = group_of.get(o.Name, '')
    for g in doc.Objects:                                       # top-level A/B group in the base file: use the inner group
        if g.TypeId == 'App::DocumentObjectGroup' and o in g.Group: grp = g.Label
    key = (grp, spec if spec else o.Label)
    r = rows.setdefault(key, {'group': grp, 'items': [], 'spec': spec, 'obj': o})
    r['items'].append(o.Label)

def base(n): return re.sub(r'(_\d+(_\d+)*|_[LR]\d*|_\d+_[-\d]+)$', '', n)
out = []
for (grp, _), r in sorted(rows.items(), key=lambda kv: (kv[0][0], base(kv[1]['items'][0]))):
    o = r['obj']; items = sorted(r['items'])
    name = base(items[0]) if len(items) > 1 else items[0]
    p = next((PURCHASE[i] for i in items if i in PURCHASE), None)
    m = re.match(r'MISUMI (HFS8-4040-\d+) ', r['spec'])
    if not p and m:                                             # base frame extrusions: part number from the spec (length in the name)
        p = {'supplier': 'MISUMI', 'part_no': m.group(1), 'link': 'https://tw.misumi-ec.com/vona2/result/?Keyword=' + m.group(1), 'desc': '',
             'note': 'HFS8 series, 40 x 40, slot 8; vendor STEP (600 long) in vendor/misumi/HFS8-4040-600, the section is used for every length'}
    m2 = re.search(r'KSS (PAQ-\d+)', r['spec'])
    if not p and m2:                                            # KSS conduit adaptors: part number from the spec (catalog page in vendor/kss)
        p = {'supplier': 'KSS 凱士士', 'part_no': m2.group(1), 'link': 'https://www.kss.com.tw/', 'desc': '',
             'note': '型錄 0616 快速型浪管固定頭 p.152（vendor/kss/KSS_p152_PAQ_BGQ_conduit_adaptor.pdf）'}
    kit = 'Kit' in o.PropertiesList and o.Kit
    out.append({'群組': grp, '零件': name, '數量': len(items), '類別': category(o, r['spec']) + ('（校正工具組，可重複使用）' if kit else ''),
                '規格 / 說明': (p['desc'] + '. ' if p and p['desc'] else '') + r['spec'],
                '供應商': p['supplier'] if p else '', '料號': p['part_no'] if p else '', '連結': p['link'] if p else '',
                '備註': p['note'] if p else '', '模型件名': ', '.join(items) if len(items) <= 8 else ', '.join(items[:8]) + ' ...'})
# conduits (22: output/v14/conduits.json): one continuous length per run, cut allowance 10 %
import json, math
def plen(q): return sum(math.dist(a_, b_) for a_, b_ in zip(q[:-1], q[1:]))
try:
    cd = json.load(open(os.path.join(ROOT, 'output', 'v14', 'conduits.json'), encoding='utf-8'))
    L29 = plen(cd['moving']['Conduit_XA']['s'][10]) + plen(cd['static']['Conduit_carriage_run']['p']) \
          + plen(cd['moving']['Conduit_ZB']['s'][10])
    L23 = plen(cd['moving']['Conduit_Y']['s'][10])
    for size, L_, run in (('PA-29', L29, '頂板 PAQ-2929 → 頂板滾動環 → X 滑座 → 工具頭（一條連續）'), ('PA-23', L23, '立柱電控板 Y 支架 PAQ-2321 → Y 馬達支架（一條連續）')):
        out.append({'群組': '09 Conduits', '零件': 'Conduit_' + size.replace('-', ''), '數量': 1, '類別': '外購件',
                    '規格 / 說明': 'KSS 尼龍浪管 %s（密封型 PA，NYLON 6）：%s；模型長度 %.0f mm，下料 %.0f mm（+10%%）' % (size, run, L_, math.ceil(L_ * 1.1 / 10) * 10),
                    '供應商': 'KSS 凱士士', '料號': size, '連結': 'https://www.kss.com.tw/index.php?action=products3&fid=114&sid=120',
                    '備註': '固定頭 KSS PAQ 系列（vendor/kss 型錄 p.152）；浪管內外徑、最小彎曲半徑待 KSS PA 浪管頁確認，模型用外徑 28.5 / 34.5', '模型件名': ''})
except Exception as e:
    print('conduit rows skipped:', e)
with open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print('BOM rows %d, parts %d -> %s' % (len(out), sum(r['數量'] for r in out), OUT))
for r in out:
    if r['連結']: print('  purchase:', r['零件'], r['料號'], r['連結'])
