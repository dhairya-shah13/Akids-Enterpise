import io
import requests
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def generate_invoice_pdf(order):
    buffer = io.BytesIO()
    
    # Page setup - 0.5 inch margins to maximize usable area
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#FF9933'), # Saffron
        alignment=2 # Right aligned
    )
    
    company_name_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#FF9933')
    )
    
    meta_style = ParagraphStyle(
        'InvoiceMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        alignment=2 # Right aligned
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#008080'), # Teal
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'InvoiceBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#414751')
    )
    
    bold_body_style = ParagraphStyle(
        'InvoiceBoldBody',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1C1C18')
    )
    
    header_cell_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )
    
    footer_style = ParagraphStyle(
        'InvoiceFooter',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#008080'),
        alignment=1 # Centered
    )

    story = []
    
    # --- HEADER SECTION (Logo & Title) ---
    logo_url = "https://lh3.googleusercontent.com/aida-public/AB6AXuA2SUWICEEV2KuppRGJwIxvv5M3-0vWkAQTe2q7DtuItSZM8IkSfhdqfnly_haUPDrmskE8bv1kUxA-6jZ5V3r81ndpeUL0wigMB2wwRHI8SEuNPM2jT-lkG8DjoW2NbHhF8rUDzcdXi5joEbaZv2JisZ2LdE7QK4dO4i2riQTTJ5yPnjP3QPqm2XrIjOdqw0F1QXo9qHTrM-CYJ0AnPKRPync29-qMcDY-fh-wN-ErFL4_S8av2QE3RvSTN3ChCbqVvqWKRc1Z7g"
    logo_img = None
    
    try:
        resp = requests.get(logo_url, timeout=2.5)
        if resp.status_code == 200:
            logo_data = io.BytesIO(resp.content)
            # Render logo image keeping constraints
            logo_img = Image(logo_data, width=1.1 * inch, height=0.35 * inch)
    except Exception:
        pass
        
    if logo_img:
        left_flow = logo_img
    else:
        left_flow = Paragraph("A kids", company_name_style)
        
    right_flow = Paragraph("SALES INVOICE", title_style)
    
    header_table = Table([[left_flow, right_flow]], colWidths=[4 * inch, 3.5 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(header_table)
    
    # --- META & INFO SECTION ---
    meta_text = f"""
    <b>Invoice No:</b> INV-{order.order_no}<br/>
    <b>Date:</b> {order.created_at.strftime('%d-%b-%Y')}<br/>
    <b>Order No:</b> {order.order_no}<br/>
    <b>Status:</b> {order.get_order_status_display()}<br/>
    <b>Payment Status:</b> PAID (Razorpay)<br/>
    """
    
    meta_p = Paragraph(meta_text, meta_style)
    
    company_details = """
    <b>Little Fingers India Pvt. Ltd.</b><br/>
    Plot No. 42, Industrial Area,<br/>
    Phase 1, New Delhi - 110020<br/>
    Email: hello@littlefingersindia.com<br/>
    Phone: +91 99243 43003
    """
    company_p = Paragraph(company_details, body_style)
    
    meta_table = Table([[company_p, meta_p]], colWidths=[4 * inch, 3.5 * inch])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#E0E0E0')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # --- BILL TO / SHIP TO SECTION ---
    customer_info = f"""
    <b>Name:</b> {order.customer_name}<br/>
    <b>Address:</b><br/>
    {order.shipping_address.replace(chr(10), '<br/>')}
    """
    customer_p = Paragraph(customer_info, body_style)
    
    address_table = Table([
        [Paragraph("SELLER DETAILS", section_title_style), Paragraph("BILL TO / SHIP TO", section_title_style)],
        [company_p, customer_p]
    ], colWidths=[3.75 * inch, 3.75 * inch])
    
    address_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,0), 2),
        ('BOTTOMPADDING', (0,1), (-1,-1), 10),
    ]))
    story.append(address_table)
    story.append(Spacer(1, 15))
    
    # --- PRODUCT TABLE SECTION ---
    # Column headings
    table_data = [[
        Paragraph("#", header_cell_style),
        Paragraph("Product Name", header_cell_style),
        Paragraph("Qty", header_cell_style),
        Paragraph("Unit Price (INR)", header_cell_style),
        Paragraph("Amount (INR)", header_cell_style),
    ]]
    
    # Add order items
    for idx, item in enumerate(order.items.all(), 1):
        table_data.append([
            Paragraph(str(idx), body_style),
            Paragraph(item.product_name, body_style),
            Paragraph(str(item.quantity), body_style),
            Paragraph(f"Rs.{item.unit_price:,.2f}", body_style),
            Paragraph(f"Rs.{item.subtotal:,.2f}", body_style),
        ])
        
    product_table = Table(table_data, colWidths=[0.5 * inch, 3.5 * inch, 0.7 * inch, 1.4 * inch, 1.4 * inch])
    
    # Apply modern table styles
    table_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FF9933')),
        ('ALIGN', (0,0), (1,-1), 'LEFT'),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E0E0E0')),
    ])
    
    # Alternating row background
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0,i), (-1,i), colors.HexColor('#FFFDF9'))
            
    product_table.setStyle(table_style)
    story.append(product_table)
    story.append(Spacer(1, 15))
    
    # --- TOTALS & GST BREAKUP SECTION ---
    # Inclusive 18% GST Calculations
    total = Decimal(str(order.total_amount))
    taxable_amount = total / Decimal('1.18')
    total_gst = total - taxable_amount
    cgst = total_gst / 2
    sgst = total_gst / 2
    
    totals_data = [
        [Paragraph("Taxable Amount (Excl. GST)", body_style), Paragraph(f"Rs.{taxable_amount:,.2f}", body_style)],
        [Paragraph("CGST (9%)", body_style), Paragraph(f"Rs.{cgst:,.2f}", body_style)],
        [Paragraph("SGST (9%)", body_style), Paragraph(f"Rs.{sgst:,.2f}", body_style)],
        [Paragraph("<b>TOTAL AMOUNT (Incl. GST)</b>", bold_body_style), Paragraph(f"<b>Rs.{total:,.2f}</b>", bold_body_style)],
    ]
    
    totals_table = Table(totals_data, colWidths=[2.5 * inch, 1.5 * inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,-1), (-1,-1), 1.5, colors.HexColor('#1C1C18')),
    ]))
    
    # Shift totals to the right by using a master table wrapper
    totals_wrapper = Table([[Spacer(1,1), totals_table]], colWidths=[3.5 * inch, 4 * inch])
    totals_wrapper.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(totals_wrapper)
    story.append(Spacer(1, 40))
    
    # --- FOOTER SECTION ---
    footer_p = Paragraph("Thank you for partnering with Little Fingers India!<br/><i>'Let Children Play Differently'</i>", footer_style)
    story.append(KeepTogether([footer_p]))
    
    # Build Document
    doc.build(story)
    
    pdf_val = buffer.getvalue()
    buffer.close()
    return pdf_val
