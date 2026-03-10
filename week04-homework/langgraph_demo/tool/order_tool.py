
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from langchain.tools import tool

from langgraph_demo.order_repo import get_order_by_id

@tool
def get_order_detail(order_id: str) -> str:
    """
    获取订单详情
    """

    print(f"--- [工具调用] 正在查询订单号: {order_id} ---")
    order_info = get_order_by_id(order_id)
    # return order_info
    if not order_info:
        return f"未找到订单号: {order_id},请检查订单号是否正确"
        
    return f"""订单号: {order_id},
        订单编号: {order_info['order_id']},
        订单名称: {order_info['order_name']},
        订单状态: {order_info['status']},
        物流状态: {order_info['logistics_status']}"""


@tool
def generate_invoice(order_id: str, name: str = "个人", tax_number: str = "") -> str:
    """
    根据订单信息生成发票。

    说明:
    - 采用 reportlab 生成 PDF, 轻量且无需外部服务。
    - 生成路径: data/invoices/invoice_<order_id>_<timestamp>.pdf
    """

    print(f"--- [工具调用] 正在为订单号生成发票PDF: {order_id} ---")
    order_info = get_order_by_id(order_id)
    if not order_info:
        return f"未找到订单号: {order_id},无法生成发票"

    if not order_info.get("can_invoice"):
        return f"订单号: {order_id} 当前不可开票"

    out_dir = Path("data/invoices")
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_order_id = "".join(ch for ch in order_id if ch.isalnum() or ch in ("-", "_")) or "unknown"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    pdf_path = out_dir / f"invoice_{safe_order_id}_{timestamp}.pdf"

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    c.setAuthor("智能客服系统")
    c.setTitle(f"电子发票_{order_info['order_id']}")

    width, height = A4
    y = height - 60
    line_gap = 28

    c.setFont("STSong-Light", 18)
    c.drawCentredString(width / 2, y, "电子发票")
    y -= line_gap * 1.4

    c.setFont("STSong-Light", 11)
    invoice_no = f"INV{timestamp}{safe_order_id[-6:]}"
    order_date = order_info.get("order_date")
    order_date_str = order_date.strftime("%Y-%m-%d %H:%M:%S") if order_date else "-"

    lines = [
        f"发票号码: {invoice_no}",
        f"开票时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"订单编号: {order_info.get('order_id', '-')}",
        f"订单名称: {order_info.get('order_name', '-')}",
        f"订单状态: {order_info.get('status', '-')}",
        f"下单时间: {order_date_str}",
        f"购方名称: {name or '个人'}",
        f"税号: {tax_number or '个人无需税号'}",
        "金额(含税): 见订单结算详情",
    ]

    for line in lines:
        c.drawString(72, y, line)
        y -= line_gap

    c.setFont("STSong-Light", 10)
    c.drawString(72, 90, "备注: 此发票为系统自动生成的演示电子发票。")
    c.drawString(72, 70, "开票方: 智能客服系统(演示)")
    c.showPage()
    c.save()

    return f"发票已生成: {pdf_path.resolve()}"
