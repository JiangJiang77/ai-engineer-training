import sys
import types


def install_reportlab_stub() -> None:
    if "reportlab" in sys.modules:
        return

    reportlab = types.ModuleType("reportlab")
    lib = types.ModuleType("reportlab.lib")
    pagesizes = types.ModuleType("reportlab.lib.pagesizes")
    pagesizes.A4 = (595.27, 841.89)

    pdfbase = types.ModuleType("reportlab.pdfbase")
    pdfmetrics = types.ModuleType("reportlab.pdfbase.pdfmetrics")
    pdfmetrics.registerFont = lambda *_args, **_kwargs: None

    cidfonts = types.ModuleType("reportlab.pdfbase.cidfonts")

    class UnicodeCIDFont:  # pragma: no cover
        def __init__(self, _name: str):
            self.name = _name

    cidfonts.UnicodeCIDFont = UnicodeCIDFont

    pdfgen = types.ModuleType("reportlab.pdfgen")
    canvas_mod = types.ModuleType("reportlab.pdfgen.canvas")

    class Canvas:  # pragma: no cover
        def __init__(self, *_args, **_kwargs):
            pass

        def setAuthor(self, *_args, **_kwargs):
            pass

        def setTitle(self, *_args, **_kwargs):
            pass

        def setFont(self, *_args, **_kwargs):
            pass

        def drawCentredString(self, *_args, **_kwargs):
            pass

        def drawString(self, *_args, **_kwargs):
            pass

        def showPage(self):
            pass

        def save(self):
            pass

    canvas_mod.Canvas = Canvas

    sys.modules["reportlab"] = reportlab
    sys.modules["reportlab.lib"] = lib
    sys.modules["reportlab.lib.pagesizes"] = pagesizes
    sys.modules["reportlab.pdfbase"] = pdfbase
    sys.modules["reportlab.pdfbase.pdfmetrics"] = pdfmetrics
    sys.modules["reportlab.pdfbase.cidfonts"] = cidfonts
    sys.modules["reportlab.pdfgen"] = pdfgen
    sys.modules["reportlab.pdfgen.canvas"] = canvas_mod
