import re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = (HERE/'emblem_src.svg').read_text()
EMBLEM_D = re.search(r'd="([^"]+)"', SRC).group(1)
WORD = (HERE/'wordmark_src.svg').read_text()
WORD_D = re.search(r'd="([^"]+)"', WORD).group(1)

INK   = '#20242a'   # Helder: text
LIGHT = '#f4f5f7'   # Helder: bg
ACCENT= '#4d738f'   # Helder: accent

def _w_path(sw=104, bars=(340,715), bottom=1100, apex=(527,560), rbottom=975, k=0.3226, c=450):
    from shapely.geometry import LineString, Polygon
    L,R = bars
    line = LineString([(L,0),(L,bottom),apex,(R,rbottom),(R,-400)])
    shape = line.buffer(sw/2, cap_style=2, join_style=2, mitre_limit=10)
    clip = Polygon([(0,c),(765,c-k*765),(765,1135),(0,1135)])
    g = shape.intersection(clip)
    polys = [g] if g.geom_type=='Polygon' else list(g.geoms)
    d=''
    for pg in polys:
        for ring in [pg.exterior, *pg.interiors]:
            pts=list(ring.coords)[:-1]
            d+='M'+' L'.join(f'{x:.1f},{y:.1f}' for x,y in pts)+' Z '
    return d.strip()

def small_geom(fill):
    """Simplified emblem in original 765x1135 units: thicker band, wider gaps, no curl."""
    return f'''<g fill="{fill}">
  <path d="M0,300 H200 V1135 H150 A150,150 0 0 1 0,985 Z"/>
  <path d="M0,245 L620,45 L620,155 L0,355 Z"/>
  <path d="{_w_path()}"/>
</g>'''

def full_geom(fill):
    return f'<path fill="{fill}" d="{EMBLEM_D}"/>'

def square(inner, size=1200, scale=1.0, tile=None, radius=None):
    """Center the 765x1135 emblem on a square canvas."""
    h = 1135*scale; w = 765*scale
    tx = (size-w)/2; ty = (size-h)/2
    bg = ''
    if tile:
        r = radius if radius is not None else size*0.2
        bg = f'<rect width="{size}" height="{size}" rx="{r:.0f}" fill="{tile}"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">'
            f'{bg}<g transform="translate({tx:.2f},{ty:.2f}) scale({scale})">{inner}</g></svg>')

def wordmark(fill):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1939 487" width="1939" height="487">'
            f'<path fill="{fill}" d="{WORD_D}"/></svg>')

def emblem_plain(fill):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 765 1135" width="765" height="1135">'
            f'<path fill="{fill}" d="{EMBLEM_D}"/></svg>')
