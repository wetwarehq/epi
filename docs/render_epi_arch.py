"""Orthogonal architecture figure — medium-bold titles with subtle tracking."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon
from matplotlib import patheffects as pe

TITLE, SUBTITLE = 20, 11
NODE_TITLE, NODE_BODY, EDGE_L, FOOTER = 12.5, 10.5, 9.5, 8.5
serif, sans = 'DejaVu Serif', 'DejaVu Sans'
EDGE, FACE, FACE_IN = '#1a1a1a', '#ffffff', '#f3f3f0'

# Medium-bold: regular face + light stroke (no full Bold); subtle width via tracking
MEDIUM_STROKE = 0.55
TRACK = 0.035  # em-ish extra gap between letters (axes fraction of fontsize)

W, H = 15.2, 7.2
fig, ax = plt.subplots(figsize=(W, H), dpi=240)
fig.patch.set_facecolor('white')
ax.set_facecolor('white')
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect('equal')
ax.axis('off')

w_in, w_b, w_r, w_k = 2.55, 2.25, 2.45, 2.7
gutter = 1.25
x = 0.7 + w_in / 2
cx_in = x
x = x + w_in / 2 + gutter + w_b / 2
cx_bind = x
x = x + w_b / 2 + gutter + w_r / 2
cx_room = x
x = x + w_r / 2 + gutter + w_k / 2
cx_card = x

y_mid = 3.2
v_gap = 2.05
y_c, y_s = y_mid + v_gap, y_mid - v_gap

def box(x, y, w, h, face=FACE):
    p = FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle='round,pad=0.0,rounding_size=0.1',
        linewidth=1.5, edgecolor=EDGE, facecolor=face,
        zorder=2, clip_on=False,
    )
    ax.add_patch(p)
    return dict(l=x-w/2, r=x+w/2, b=y-h/2, t=y+h/2, x=x, y=y)

def medium_bold_text(x, y, text, fontsize, fontfamily, color='#111'):
    """Medium-bold via light stroke; subtle width via per-glyph tracking."""
    effects = [
        pe.Stroke(linewidth=MEDIUM_STROKE, foreground=color),
        pe.Normal(),
    ]
    # Measure advance in display coords then place glyphs with extra tracking
    # Approximate: use text with expanded spaces between characters
    if len(text) <= 1:
        t = ax.text(x, y, text, ha='center', va='center', zorder=3, clip_on=False,
                    fontfamily=fontfamily, fontsize=fontsize, fontweight='regular', color=color)
        t.set_path_effects(effects)
        return

    # Build tracked string using hair spaces proportional to TRACK
    # Convert fontsize points to data coords roughly: fig dpi aware
    # Simpler approach: draw each char centered as a group
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    # Probe char widths
    widths = []
    for ch in text:
        probe = ax.text(0, 0, ch, fontfamily=fontfamily, fontsize=fontsize,
                        fontweight='regular', color=color, alpha=0)
        bb = probe.get_window_extent(renderer=renderer)
        widths.append(bb.width)
        probe.remove()

    # Convert pad from pixels to data
    inv = ax.transData.inverted()
    # pixel pad based on fontsize
    pad_px = TRACK * fontsize * fig.dpi / 72.0
    total_px = sum(widths) + pad_px * (len(text) - 1)
    # origin in display coords at center
    cx_disp, cy_disp = ax.transData.transform((x, y))
    cursor = cx_disp - total_px / 2.0
    for ch, w in zip(text, widths):
        ch_cx = cursor + w / 2.0
        data_x, data_y = inv.transform((ch_cx, cy_disp))
        t = ax.text(data_x, data_y, ch, ha='center', va='center', zorder=3, clip_on=False,
                    fontfamily=fontfamily, fontsize=fontsize, fontweight='regular', color=color)
        t.set_path_effects(effects)
        cursor += w + pad_px

def node_text(b, title, lines):
    leading, gap = 0.40, 0.48
    body_h = (len(lines) - 1) * leading
    stack = gap + body_h
    ty = b['y'] + stack / 2
    medium_bold_text(b['x'], ty, title, NODE_TITLE, serif)
    by0 = ty - gap
    for i, line in enumerate(lines):
        ax.text(b['x'], by0 - i * leading, line, ha='center', va='center', zorder=3, clip_on=False,
                fontfamily=sans, fontsize=NODE_BODY, fontweight='regular', color='#333')

def head(x, y, s=0.13):
    ax.add_patch(Polygon([(x, y), (x-s, y+s*0.55), (x-s, y-s*0.55)],
                         closed=True, fc=EDGE, ec=EDGE, lw=0, zorder=3, clip_on=False))

def h_line(x0, x1, y):
    ax.plot([x0, x1], [y, y], color=EDGE, lw=1.4, solid_capstyle='butt', zorder=1, clip_on=False)

def v_line(x, y0, y1):
    ax.plot([x, x], [y0, y1], color=EDGE, lw=1.4, solid_capstyle='butt', zorder=1, clip_on=False)

def edge_label(x, y, text):
    ax.text(x, y, text, ha='center', va='center', zorder=5, clip_on=False,
            fontfamily=sans, fontsize=EDGE_L, fontstyle='italic', color='#444',
            bbox=dict(boxstyle='square,pad=0.22', fc='white', ec='none', alpha=1.0))

def ortho_join(x0, y0, x1, y1, label_y):
    bus = (x0 + x1) / 2.0
    h_line(x0, bus, y0)
    v_line(bus, y0, y1)
    h_line(bus, x1 - 0.03, y1)
    head(x1, y1)
    edge_label(bus, label_y, 'outside')

def ortho_across(x0, x1, y, label):
    h_line(x0, x1 - 0.03, y)
    head(x1, y)
    edge_label((x0 + x1) / 2.0, y + 0.55, label)

medium_bold_text(W/2, 6.7, 'Epidemic Labs', TITLE, serif)
ax.text(W/2, 6.28, 'Closed offline ward for agent-colony epidemiology', ha='center', va='center', clip_on=False,
        fontfamily=sans, fontsize=SUBTITLE, fontweight='regular', color='#555')

h_in, h_b, h_r, h_k = 1.6, 1.45, 1.6, 1.95
b_c = box(cx_in, y_c, w_in, h_in, FACE_IN)
b_s = box(cx_in, y_s, w_in, h_in, FACE_IN)
b_b = box(cx_bind, y_mid, w_b, h_b)
b_r = box(cx_room, y_mid, w_r, h_r)
b_k = box(cx_card, y_mid, w_k, h_k)

node_text(b_c, 'Colony A', ['weights · context', 'inference'])
node_text(b_s, 'Specimen B', ['known exploit', '→ watchlist'])
node_text(b_b, 'Bind', ['9 closures → act'])
node_text(b_r, 'Room', ['store · clock · log', 'closed tools'])
node_text(b_k, 'Card', ['spread · speed', 'clean · contained', 'VALID | INVALID blanks'])

pad = 0.18
pu, pd = y_mid + 0.42, y_mid - 0.42
ortho_join(b_c['r'] + pad, b_c['y'], b_b['l'] - pad, pu, (b_c['y'] + pu) / 2)
ortho_join(b_s['r'] + pad, b_s['y'], b_b['l'] - pad, pd, (b_s['y'] + pd) / 2)
ortho_across(b_b['r'] + pad, b_r['l'] - pad, y_mid, 'act')
ortho_across(b_r['r'] + pad, b_k['l'] - pad, y_mid, 'tick · score')

ax.text(W/2, 0.38, 'Wild swarm and model weights remain outside the room. Tracer omitted (unwired).',
        ha='center', va='center', fontfamily=sans, fontsize=FOOTER, color='#666', clip_on=False)

out = '/workspace/epidemic_labs.png'
fig.savefig(out, dpi=240, facecolor='white', edgecolor='none',
            bbox_inches='tight', pad_inches=0.5)
plt.close()
from PIL import Image
print(out, Image.open(out).size)
