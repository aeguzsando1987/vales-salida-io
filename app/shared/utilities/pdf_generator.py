"""
Generador de PDF - ReportLab 
Genera documentos PDF profesionales usando ReportLab con diseño similar a plantillas HTML.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.platypus import PageBreak, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from pathlib import Path
from datetime import datetime
from typing import Any
import logging

logger = logging.getLogger(__name__)


class PDFGenerator:
    """
    Generador de PDFs profesionales para vouchers usando ReportLab.

    Diseño inspirado en plantillas HTML con:
    - Banda lateral derecha de color (2.5cm de ancho)
    - Badges de estado y tipo con colores específicos
    - Layout moderno y limpio
    - Tablas con filas alternadas
    - Firmas con líneas elegantes

    Colores por tipo:
    - ENTRY → VERDE (#28a745)
    - EXIT con retorno → ROJO (#dc3545)
    - EXIT sin retorno → AMARILLO (#ffc107)
    """

    # Colores para cada tipo de voucher (banda lateral)
    COLORS = {
        'ENTRY': colors.HexColor('#28a745'),          # VERDE
        'EXIT_RETURN': colors.HexColor('#dc3545'),    # ROJO
        'EXIT_NO_RETURN': colors.HexColor('#ffc107')  # AMARILLO
    }

    # Colores más suaves para gradiente (simulado)
    COLORS_LIGHT = {
        'ENTRY': colors.HexColor('#20c997'),          # VERDE claro
        'EXIT_RETURN': colors.HexColor('#c82333'),    # ROJO oscuro
        'EXIT_NO_RETURN': colors.HexColor('#ff9800')  # NARANJA
    }

    LABELS = {
        'ENTRY': 'ENTRADA DE MATERIAL',
        'EXIT_RETURN': 'SALIDA CON RETORNO',
        'EXIT_NO_RETURN': 'SALIDA SIN RETORNO'
    }

    # Colores de badges de estado (del CSS)
    STATUS_COLORS = {
        'PENDING': {
            'bg': colors.HexColor('#e2e3e5'),
            'fg': colors.HexColor('#383d41')
        },
        'APPROVED': {
            'bg': colors.HexColor('#d4edda'),
            'fg': colors.HexColor('#155724')
        },
        'IN_TRANSIT': {
            'bg': colors.HexColor('#fff3cd'),
            'fg': colors.HexColor('#856404')
        },
        'CLOSED': {
            'bg': colors.HexColor('#cce5ff'),
            'fg': colors.HexColor('#004085')
        },
        'OVERDUE': {
            'bg': colors.HexColor('#f8d7da'),
            'fg': colors.HexColor('#721c24')
        },
        'CANCELLED': {
            'bg': colors.HexColor('#f5c6cb'),
            'fg': colors.HexColor('#721c24')
        }
    }

    def __init__(self, template_dir: str, temp_dir: str):
        """
        Inicializa el generador de PDF.

        Args:
            template_dir: No usado en ReportLab (mantenido por compatibilidad)
            temp_dir: Directorio temporal para PDFs generados
        """
        self.template_dir = Path(template_dir)  # No usado pero mantenido
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Configurar estilos de texto
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configura estilos personalizados para el documento."""
        self.styles.add(ParagraphStyle(
            name='ComprobanteTitle',
            parent=self.styles['Heading1'],
            fontSize=8,
            leading=9,
            textColor=colors.black,
            spaceAfter=0,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=7,
            leading=8,
            textColor=colors.black,
            spaceAfter=0,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='Folio',
            parent=self.styles['Normal'],
            fontSize=6,
            leading=7,
            textColor=colors.HexColor('#333333'),
            spaceAfter=0,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='TypeBadge',
            parent=self.styles['Normal'],
            fontSize=6,
            textColor=colors.white,
            spaceBefore=0,
            spaceAfter=0,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='StatusBadge',
            parent=self.styles['Normal'],
            fontSize=6,
            spaceBefore=0,
            spaceAfter=0,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='MetadataLabel',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#666666'),
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='MetadataValue',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#333333'),
            fontName='Helvetica'
        ))

        self.styles.add(ParagraphStyle(
            name='Body_Custom',
            parent=self.styles['Normal'],
            fontSize=7,
            leading=10,
            alignment=TA_LEFT
        ))

        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#333333'),
            fontName='Helvetica-Bold',
            spaceAfter=2,
            spaceBefore=3
        ))

    def generate_voucher_pdf(self, voucher: Any, qr_image_path: str) -> str:
        """
        Genera un PDF profesional para un voucher específico.

        Args:
            voucher: Objeto voucher con todos sus datos
            qr_image_path: Ruta a la imagen QR generada

        Returns:
            Ruta absoluta del PDF generado

        Raises:
            Exception: Si hay error al generar el PDF
        """
        # Determinar tipo de voucher para color
        voucher_type_key = self._get_voucher_type_key(voucher.voucher_type, voucher.with_return)
        color = self.COLORS[voucher_type_key]
        color_light = self.COLORS_LIGHT[voucher_type_key]
        label = self.LABELS[voucher_type_key]

        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"voucher_{voucher.id}_{timestamp}.pdf"
        pdf_path = self.temp_dir / filename

        try:
            # Banda QR: 0.5 in de alto + 0.12 in de gap = 0.62 in de topMargin
            QR_BAND_H = 0.5 * inch

            # Crear documento PDF con función de dibujo de banda lateral
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                rightMargin=2.2*cm,  # Espacio para banda de color (1.5cm + 0.7cm margen)
                leftMargin=2*cm,
                topMargin=QR_BAND_H + 0.12*inch,
                bottomMargin=1.5*cm,
            )

            # Construir contenido
            story = []

            # Sección de título compacta
            story.extend(self._build_header(
                label,
                color,
                voucher.folio,
                voucher.status,
                voucher.voucher_type
            ))

            # Información del voucher (metadata)
            story.extend(self._build_voucher_info(voucher))

            if hasattr(voucher, 'details') and voucher.details and len(voucher.details) > 0:
                story.append(Spacer(1, 0.07*inch))
                story.extend(self._build_details_table(voucher.details))

            # Notas/observaciones
            if voucher.notes:
                story.append(Spacer(1, 0.05*inch))
                story.extend(self._build_notes(voucher.notes))

            # Firmas digitales
            story.append(Spacer(1, 0.07*inch))
            story.extend(self._build_signatures())

            def _on_page(c, d):
                self._draw_qr_band(c, d, qr_image_path, QR_BAND_H)
                self._draw_color_band(c, d, color, color_light)

            # Construir PDF con callbacks para banda lateral y banda QR
            doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)

            logger.info(f"PDF generado exitosamente: {pdf_path}")
            return str(pdf_path.absolute())

        except Exception as e:
            logger.error(f"Error generando PDF: {str(e)}", exc_info=True)
            # Limpiar archivo parcial si existe
            if pdf_path.exists():
                pdf_path.unlink()
            raise

    # Ancho de la banda lateral (usado también para ajustar tablas)
    BAND_WIDTH = 1.5 * cm

    def _draw_color_band(self, canvas_obj: canvas.Canvas, doc: Any, color: colors.Color, color_light: colors.Color):
        """Dibuja la banda lateral de color en el lado derecho de la página."""
        canvas_obj.saveState()

        bw = self.BAND_WIDTH

        # Mitad inferior — color base
        canvas_obj.setFillColor(color)
        canvas_obj.setStrokeColor(color)
        canvas_obj.rect(
            letter[0] - bw,
            0,
            bw,
            letter[1] * 0.5,
            stroke=0,
            fill=1
        )

        # Mitad superior — color más claro (efecto gradiente)
        canvas_obj.setFillColor(color_light)
        canvas_obj.setStrokeColor(color_light)
        canvas_obj.rect(
            letter[0] - bw,
            letter[1] * 0.5,
            bw,
            letter[1] * 0.5,
            stroke=0,
            fill=1
        )

        canvas_obj.restoreState()

    def _draw_qr_band(self, canvas_obj: canvas.Canvas, doc: Any, qr_image_path: str, band_height: float):
        """Dibuja la banda superior full-width: QR a la izquierda, caption + timestamp al centro."""
        canvas_obj.saveState()

        page_w = letter[0]
        page_h = letter[1]
        y_band = page_h - band_height  # y inferior de la banda
        mid_y = y_band + band_height / 2

        # Fondo gris claro
        canvas_obj.setFillColor(colors.HexColor('#f2f2f2'))
        canvas_obj.rect(0, y_band, page_w, band_height, stroke=0, fill=1)

        # Línea inferior
        canvas_obj.setStrokeColor(colors.HexColor('#cccccc'))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(0, y_band, page_w, y_band)

        # QR: esquina izquierda, centrado verticalmente
        qr_size = band_height * 0.72
        margin_left = 0.18 * inch
        qr_x = margin_left
        qr_y = y_band + (band_height - qr_size) / 2

        if qr_image_path and Path(qr_image_path).exists():
            canvas_obj.drawImage(
                qr_image_path,
                qr_x, qr_y,
                width=qr_size, height=qr_size,
                preserveAspectRatio=True, mask='auto'
            )

        # Texto caption + timestamp a la derecha del QR
        text_x = qr_x + qr_size + 0.12 * inch
        canvas_obj.setFont('Helvetica', 5.5)
        canvas_obj.setFillColor(colors.HexColor('#555555'))
        canvas_obj.drawString(text_x, mid_y + 4, 'Escanea para verificar la autenticidad del comprobante.')
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        canvas_obj.setFont('Helvetica', 5)
        canvas_obj.setFillColor(colors.HexColor('#888888'))
        canvas_obj.drawString(text_x, mid_y - 5, f'Generado: {generated_at}')

        canvas_obj.restoreState()

    def _get_voucher_type_key(self, voucher_type: str, with_return: bool) -> str:
        """Determina la clave de tipo para obtener color y etiqueta."""
        if voucher_type == 'ENTRY':
            return 'ENTRY'
        elif voucher_type == 'EXIT':
            return 'EXIT_RETURN' if with_return else 'EXIT_NO_RETURN'
        else:
            return 'ENTRY'  # Default

    def _build_qr_band(self, qr_image_path: str):
        """Banda superior delgada con QR y texto explicativo, estilo encabezado de Word."""
        elements = []

        qr_path = Path(qr_image_path) if qr_image_path else None

        if qr_path and qr_path.exists():
            qr_img = Image(str(qr_path), width=0.45*inch, height=0.45*inch)
            qr_cell = Table([[qr_img]], colWidths=[0.55*inch])
            qr_cell.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
        else:
            qr_cell = Spacer(0.55*inch, 0.1*inch)

        caption = Paragraph(
            '<font size="6" color="#555555">Escanea este código para verificar la autenticidad '
            'de este comprobante en el sistema.</font>',
            self.styles['Body_Custom']
        )
        text_cell = Table([[caption]], colWidths=[4.55*inch])
        text_cell.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))

        band_table = Table([[qr_cell, text_cell]], colWidths=[0.55*inch, 4.55*inch])
        band_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f2f2f2')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ]))
        elements.append(band_table)
        elements.append(Spacer(1, 0.04*inch))

        return elements

    def _build_header(self, label: str, color: colors.Color, folio: str, status: str, voucher_type: str):
        """Sección de título compacta: grupo, tipo de comprobante, folio, badges."""
        elements = []

        status_map = {
            'PENDING': 'PENDIENTE',
            'APPROVED': 'APROBADO',
            'IN_TRANSIT': 'EN TRÁNSITO',
            'OVERDUE': 'VENCIDO',
            'CLOSED': 'CERRADO',
            'CANCELLED': 'CANCELADO'
        }
        status_texto = status_map.get(status, status)
        comprobante_tipo = "ENTRADA" if voucher_type == "ENTRY" else "SALIDA"

        title_rows = [
            [Paragraph("<b>GRUPO GPA</b>", self.styles['ComprobanteTitle'])],
            [Paragraph(f"<b>COMPROBANTE DE {comprobante_tipo}</b>", self.styles['CompanyName'])],
            [Paragraph(f"FOLIO: {folio}", self.styles['Folio'])],
        ]

        title_block = Table(title_rows, colWidths=[5.1*inch])
        title_block.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(title_block)

        # Badges de tipo y estado
        type_badge = Paragraph(f"<b>{label}</b>", self.styles['TypeBadge'])
        type_cell = Table([[type_badge]], colWidths=[2.4*inch])
        type_cell.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        status_config = self.STATUS_COLORS.get(status, {
            'bg': colors.HexColor('#e2e3e5'),
            'fg': colors.HexColor('#383d41')
        })
        status_style = ParagraphStyle(
            name='StatusBadgeColored',
            parent=self.styles['StatusBadge'],
            textColor=status_config['fg'],
            fontSize=7
        )
        status_badge = Paragraph(f"<b>ESTADO: {status_texto}</b>", status_style)
        status_cell = Table([[status_badge]], colWidths=[1.7*inch])
        status_cell.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), status_config['bg']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        badges_row = Table([[type_cell, status_cell]], colWidths=[2.5*inch, 1.8*inch])
        badges_row.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        centered_badges = Table([[badges_row]], colWidths=[5.1*inch])
        centered_badges.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
        elements.append(centered_badges)

        elements.append(Spacer(1, 0.04*inch))
        line_table = Table([['']], colWidths=[5.1*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#555555')),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 0.03*inch))

        return elements

    def _build_voucher_info(self, voucher: Any):
        """Construye la sección de metadata del voucher en 3 columnas."""
        elements = []

        tipo_map = {'ENTRY': 'ENTRADA', 'EXIT': 'SALIDA'}
        tipo_texto = tipo_map.get(voucher.voucher_type, voucher.voucher_type)

        def lbl(text):
            return Paragraph(f'<b>{text}</b>', self.styles['MetadataLabel'])

        def val(text):
            return Paragraph(str(text) if text else '—', self.styles['MetadataValue'])

        # --- Datos de creador y aprobador ---
        creator_name = '—'
        creator_individual = getattr(voucher, '_creator_individual', None)
        if creator_individual:
            creator_name = (
                getattr(creator_individual, 'full_name', None)
                or f"{getattr(creator_individual, 'first_name', '')} {getattr(creator_individual, 'last_name', '')}".strip()
                or '—'
            )
        elif hasattr(voucher, 'creator') and voucher.creator:
            creator_name = getattr(voucher.creator, 'name', '—') or '—'

        approver_name = '—'
        if hasattr(voucher, 'approved_by') and voucher.approved_by:
            approver_name = (
                getattr(voucher.approved_by, 'full_name', None)
                or f"{getattr(voucher.approved_by, 'first_name', '')} {getattr(voucher.approved_by, 'last_name', '')}".strip()
                or '—'
            )

        company_name = '—'
        if hasattr(voucher, 'company') and voucher.company:
            company_name = (
                getattr(voucher.company, 'company_name', None)
                or getattr(voucher.company, 'legal_name', '—')
                or '—'
            )

        intercompany_text = 'Sí' if getattr(voucher, 'is_intercompany', False) else 'No'

        # Columna 1: fechas y tipo
        col1 = [
            [lbl('Fecha Creación:'), val(voucher.created_at.strftime("%d/%m/%Y %H:%M"))],
            [lbl('Tipo:'),           val(tipo_texto)],
            [lbl('Con retorno:'),    val('Sí' if voucher.with_return else 'No')],
        ]
        if voucher.estimated_return_date and voucher.with_return:
            col1.append([lbl('Retorno estimado:'), val(str(voucher.estimated_return_date))])

        # Columna 2: origen/destino e intercompañía
        col2 = [
            [lbl('Empresa:'),       val(company_name)],
            [lbl('Intercompañía:'), val(intercompany_text)],
        ]
        if hasattr(voucher, 'origin_branch') and voucher.origin_branch:
            col2.append([lbl('Origen:'), val(getattr(voucher.origin_branch, 'branch_name', '—'))])
        if hasattr(voucher, 'destination_branch') and voucher.destination_branch:
            col2.append([lbl('Destino:'), val(getattr(voucher.destination_branch, 'branch_name', '—'))])
        else:
            col2.append([lbl('Destino:'), val('—')])
        col2.append([lbl('Dest. Externo:'), val(getattr(voucher, 'outer_destination', None) or '—')])

        # Columna 3: personas involucradas
        col3 = [
            [lbl('Creado por:'),   val(creator_name)],
            [lbl('Aprobado por:'), val(approver_name)],
        ]

        col_style = TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ])

        t1 = Table(col1, colWidths=[1.0*inch, 1.3*inch])
        t1.setStyle(col_style)
        t2 = Table(col2, colWidths=[1.0*inch, 1.3*inch])
        t2.setStyle(col_style)
        t3 = Table(col3, colWidths=[0.9*inch, 1.3*inch])
        t3.setStyle(col_style)

        metadata_table = Table([[t1, t2, t3]], colWidths=[2.3*inch, 2.3*inch, 2.2*inch])
        metadata_table.setStyle(TableStyle([
            ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
            ('LINEAFTER',    (0, 0), (1, 0),   0.5, colors.HexColor('#cccccc')),
            ('LEFTPADDING',  (1, 0), (2, 0),   6),
        ]))

        elements.append(metadata_table)
        return elements

    def _build_details_table(self, details: list):
        """Construye la tabla de detalles/líneas del voucher con filas alternadas."""
        elements = []

        # Título de sección
        elements.append(Paragraph('<b>Artículos / Material</b>', self.styles['SectionTitle']))

        # Encabezados de tabla
        table_data = [[
            Paragraph('<b>#</b>', self.styles['Body_Custom']),
            Paragraph('<b>Artículo</b>', self.styles['Body_Custom']),
            Paragraph('<b>Cantidad</b>', self.styles['Body_Custom']),
            Paragraph('<b>Unidad</b>', self.styles['Body_Custom']),
            Paragraph('<b>Observaciones</b>', self.styles['Body_Custom'])
        ]]

        # Filas de datos
        for detail in details:
            table_data.append([
                Paragraph(str(detail.line_number), self.styles['Body_Custom']),
                Paragraph(detail.item_name, self.styles['Body_Custom']),
                Paragraph(str(detail.quantity), self.styles['Body_Custom']),
                Paragraph(detail.unit_of_measure or 'PZA', self.styles['Body_Custom']),
                Paragraph(detail.notes or '', self.styles['Body_Custom'])
            ])

        # Crear tabla
        details_table = Table(table_data, colWidths=[0.35*inch, 2.8*inch, 0.85*inch, 0.85*inch, 1.75*inch])

        # Estilos base
        style_commands = [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),  # Header
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Header centrado
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # # centrado
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Cantidad centrada
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]

        # Filas alternadas (del CSS: nth-child(even))
        for row_idx in range(2, len(table_data), 2):  # Empezar en 2 (después de header)
            style_commands.append(
                ('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#f9f9f9'))
            )

        details_table.setStyle(TableStyle(style_commands))

        elements.append(details_table)
        return elements

    def _build_signatures(self):
        """
        Construye la sección de firmas con 4 espacios fijos.
        Cada espacio tiene una línea negra y texto estático debajo.
        Las firmas son estáticas y no dependen de datos del voucher.
        """
        elements = []

        elements.append(Paragraph('<b>Firmas</b>', self.styles['SectionTitle']))
        elements.append(Spacer(1, 0.03*inch))

        # 4 ESPACIOS FIJOS (sin importar si hay datos o no)
        signatures = [
            'Nombre y firma de quien entrega',
            'Nombre y firma de quien recibe',
            'Nombre y firma de quien autoriza la salida',
            'Nombre y firma de control patrimonial'
        ]

        # Ancho total extendido para aprovechar el espacio horizontal disponible
        total_width = 6.6 * inch
        col_width = total_width / 4

        # Crear las 4 celdas de firma
        sig_cells = []
        for label in signatures:
            line_table = Table([['']], colWidths=[col_width - 0.12*inch])
            line_table.setStyle(TableStyle([
                ('LINEABOVE', (0, 0), (0, 0), 1, colors.black),
            ]))

            cell_content = [
                Spacer(1, 0.15*inch),
                line_table,
                Paragraph(
                    f'<font size="7" color="#333333">{label}</font>',
                    self.styles['Body_Custom']
                ),
            ]

            sig_cells.append(cell_content)

        cells_as_tables = []
        for cell_content in sig_cells:
            mini_table = Table([[item] for item in cell_content], colWidths=[col_width - 0.08*inch])
            mini_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('VALIGN', (0, 0), (0, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            cells_as_tables.append(mini_table)

        sig_table = Table([cells_as_tables], colWidths=[col_width] * 4)
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(sig_table)
        return elements

    def _build_qr_section(self, qr_image_path: str):
        """Construye la sección con la imagen QR centrada y con borde."""
        elements = []

        if Path(qr_image_path).exists():
            # Cargar imagen QR
            qr_img = Image(qr_image_path, width=1.5*inch, height=1.5*inch)

            # Tabla para centrar QR con borde
            qr_data = [[qr_img]]
            qr_table = Table(qr_data, colWidths=[1.6*inch])
            qr_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#333333')),  # Borde
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ]))

            # Centrar tabla en página
            center_table = Table([[qr_table]], colWidths=[5.1*inch])
            center_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))

            elements.append(center_table)
            elements.append(Spacer(1, 0.05*inch))

            # Texto descriptivo
            qr_text = Paragraph(
                '<font color="#666666" size="9">Código de Identificación</font>',
                self.styles['Body_Custom']
            )
            qr_text_table = Table([[qr_text]], colWidths=[5.1*inch])
            qr_text_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            elements.append(qr_text_table)
        else:
            elements.append(Paragraph(
                '<b>Código QR no disponible</b>',
                self.styles['Body_Custom']
            ))

        return elements

    def _build_notes(self, notes: str):
        """Construye la sección de observaciones con caja de fondo."""
        elements = []

        elements.append(Paragraph('<b>Observaciones</b>', self.styles['SectionTitle']))

        # Caja de notas con fondo gris claro
        notes_para = Paragraph(notes, self.styles['Body_Custom'])
        notes_table = Table([[notes_para]], colWidths=[5.1*inch])
        notes_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(notes_table)
        return elements

    def _build_footer(self):
        """Construye el footer con solo el timestamp de generación."""
        elements = []

        line_table = Table([['']], colWidths=[5.1*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#cccccc')),
        ]))
        elements.append(line_table)

        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer_para = Paragraph(
            f'<font color="#999999" size="7">Generado: {generated_at} UTC</font>',
            self.styles['Body_Custom']
        )
        footer_table = Table([[footer_para]], colWidths=[5.1*inch])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(footer_table)

        return elements
