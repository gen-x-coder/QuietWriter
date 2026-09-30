"""Genereert alle QuietWriter-iconen opnieuw.

Gebruik:  pip install PySide6 shapely
          python bron/maak_iconen.py
Kleuren (INK, LIGHT, ACCENT) staan bovenin logo_geometrie.py.
"""
import sys, struct, io, shutil
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from pathlib import Path
from logo_geometrie import *
from PySide6.QtWidgets import QApplication
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QImage, QPainter, QColor, QFont
from PySide6.QtCore import QRectF, QByteArray, QBuffer, QIODevice, Qt
app=QApplication(sys.argv)

OUT=Path(__file__).resolve().parent.parent
for d in ('svg','png','in-app'): (OUT/d).mkdir(parents=True, exist_ok=True)
WHITE='#ffffff'
TILE_FULL  = lambda: square(full_geom(WHITE),  scale=0.74, tile=ACCENT)
TILE_SMALL = lambda: square(small_geom(WHITE), scale=0.78, tile=ACCENT)

svgs = {
 'svg/quietwriter-embleem-donker.svg': emblem_plain(INK),
 'svg/quietwriter-embleem-licht.svg':  emblem_plain(LIGHT),
 'svg/quietwriter-icoon-donker.svg':        square(full_geom(INK)),
 'svg/quietwriter-icoon-licht.svg':         square(full_geom(LIGHT)),
 'svg/quietwriter-icoon-klein-donker.svg':  square(small_geom(INK)),
 'svg/quietwriter-icoon-klein-licht.svg':   square(small_geom(LIGHT)),
 'svg/quietwriter-app-tegel.svg':        TILE_FULL(),
 'svg/quietwriter-app-tegel-klein.svg':  TILE_SMALL(),
 'svg/quietwriter-woordmerk-donker.svg': wordmark(INK),
 'svg/quietwriter-woordmerk-licht.svg':  wordmark(LIGHT),
 # in-app: fixed hex fill so icon_theme._recolour_svg recolours it per theme
 'in-app/quietwriter.svg':          square(full_geom(INK)),
 'in-app/quietwriter-small.svg':    square(small_geom(INK)),
 'in-app/quietwriter-wordmark.svg': wordmark(INK),
}
for p,s in svgs.items(): (OUT/p).write_text(s+'\n', encoding='utf-8')

def raster(svg, w, h=None):
    h = h or w
    r=QSvgRenderer(QByteArray(svg.encode())); im=QImage(w,h,QImage.Format_ARGB32); im.fill(0)
    p=QPainter(im); p.setRenderHint(QPainter.Antialiasing); p.setRenderHint(QPainter.SmoothPixmapTransform)
    r.render(p,QRectF(0,0,w,h)); p.end(); return im
def png_bytes(im):
    buf=QBuffer(); buf.open(QIODevice.WriteOnly); im.save(buf,'PNG'); return bytes(buf.data())

def app_icon(n):  # small design up to 24 px, full detail from 32 px
    return raster(TILE_SMALL() if n <= 24 else TILE_FULL(), n)

ICO_SIZES=[16,20,24,32,40,48,64,96,128,256]
def write_ico(path, images):
    data=[png_bytes(im) for im in images]
    hdr=struct.pack('<HHH',0,1,len(data)); off=6+16*len(data); ent=b''
    for im,d in zip(images,data):
        w=im.width(); ent+=struct.pack('<BBBBHHII', w%256, w%256, 0,0,1,32,len(d),off); off+=len(d)
    Path(path).write_bytes(hdr+ent+b''.join(data))
imgs=[app_icon(n) for n in ICO_SIZES]
write_ico(OUT/'quietwriter.ico', imgs)
for n,im in zip(ICO_SIZES+[512,1024], imgs+[app_icon(512),app_icon(1024)]):
    im.save(str(OUT/f'png/quietwriter-{n}.png'))
# transparent PNG emblems for docs/README
for tone,col in (('donker',INK),('licht',LIGHT)):
    raster(emblem_plain(col),382,567).save(str(OUT/f'png/quietwriter-embleem-{tone}.png'))
    raster(wordmark(col),970,244).save(str(OUT/f'png/quietwriter-woordmerk-{tone}.png'))
print('ok')
