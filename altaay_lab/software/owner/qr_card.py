"""Draw a QR code as an SVG. The encoder is the vendored Nayuki library.

The picture is for the setup page. On the duck the same network is spoken.
"""

from __future__ import annotations

from . import qrcodegen


def qr_svg(text):
    qr = qrcodegen.QrCode.encode_text(text, qrcodegen.QrCode.Ecc.MEDIUM)
    border = 4
    n = qr.get_size()
    size = n + border * 2
    runs = []
    for y in range(n):
        x = 0
        while x < n:
            if not qr.get_module(x, y):
                x += 1
                continue
            x0 = x
            while x < n and qr.get_module(x, y):
                x += 1
            runs.append("M%d %dh%dv1h-%dz" % (x0 + border, y + border, x - x0, x - x0))
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
        'shape-rendering="crispEdges" role="img" aria-label="Setup network QR code">'
        '<rect width="%d" height="%d" fill="#ffffff"/>'
        '<path fill="#1c1915" d="%s"/></svg>'
    ) % (size, size, size, size, "".join(runs))
