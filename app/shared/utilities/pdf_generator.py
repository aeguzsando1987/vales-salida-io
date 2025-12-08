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
from datetime import datetime, timezone
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
        # Título principal (nombre de empresa)
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=colors.black,
            spaceAfter=5,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Folio
        self.styles.add(ParagraphStyle(
            name='Folio',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Badge de tipo (redondeado con fondo de color)
        self.styles.add(ParagraphStyle(
            name='TypeBadge',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.white,
            spaceBefore=5,
            spaceAfter=5,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Badge de estado
        self.styles.add(ParagraphStyle(
            name='StatusBadge',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceBefore=3,
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Labels de metadata
        self.styles.add(ParagraphStyle(
            name='MetadataLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            fontName='Helvetica-Bold'
        ))

        # Valores de metadata
        self.styles.add(ParagraphStyle(
            name='MetadataValue',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            fontName='Helvetica'
        ))

        # Texto normal
        self.styles.add(ParagraphStyle(
            name='Body_Custom',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_LEFT
        ))

        # Sección de título (Artículos, Firmas, etc.)
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            fontName='Helvetica-Bold',
            spaceAfter=8,
            spaceBefore=10
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
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"voucher_{voucher.id}_{timestamp}.pdf"
        pdf_path = self.temp_dir / filename

        try:
            # Crear documento PDF con función de dibujo de banda lateral
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                rightMargin=3*cm,  # Espacio para banda de color (2.5cm + margen)
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm,
            )

            # Construir contenido
            story = []

            # Encabezado con badges
            story.extend(self._build_header(
                label,
                color,
                voucher.folio,
                voucher.status,
                getattr(voucher.company, 'legal_name', 'N/A') if hasattr(voucher, 'company') and voucher.company else 'N/A'
            ))

            # Información del voucher (metadata)
            story.extend(self._build_voucher_info(voucher))

            # Detalles/líneas del voucher
            if hasattr(voucher, 'details') and voucher.details:
                story.append(Spacer(1, 0.3*inch))
                story.extend(self._build_details_table(voucher.details))

            # Notas/observaciones
            if voucher.notes:
                story.append(Spacer(1, 0.2*inch))
                story.extend(self._build_notes(voucher.notes))

            # Firmas digitales
            story.append(Spacer(1, 0.4*inch))
            story.extend(self._build_signatures(voucher, voucher_type_key))

            # Footer con QR y timestamp
            story.append(Spacer(1, 0.3*inch))
            story.extend(self._build_footer_with_qr(qr_image_path))

            # Construir PDF con callback para dibujar banda lateral
            doc.build(
                story,
                onFirstPage=lambda c, d: self._draw_color_band(c, d, color, color_light),
                onLaterPages=lambda c, d: self._draw_color_band(c, d, color, color_light)
            )

            logger.info(f"PDF generado exitosamente: {pdf_path}")
            return str(pdf_path.absolute())

        except Exception as e:
            logger.error(f"Error generando PDF: {str(e)}", exc_info=True)
            # Limpiar archivo parcial si existe
            if pdf_path.exists():
                pdf_path.unlink()
            raise

    def _draw_color_band(self, canvas_obj: canvas.Canvas, doc: Any, color: colors.Color, color_light: colors.Color):
        """
        Dibuja la banda lateral de color en el lado derecho de la página.
        Simula un gradiente usando dos rectángulos.
        """
        canvas_obj.saveState()

        # Banda de color principal - TODA LA ALTURA
        canvas_obj.setStrokeColor(color)
        canvas_obj.setFillColor(color)
        canvas_obj.rect(
            letter[0] - 2.5*cm,  # Posición X (lado derecho menos 2.5cm)
            0,                    # Posición Y (desde abajo)
            2.5*cm,              # Ancho de la banda
            letter[1],           # Alto (toda la altura de la página)
            stroke=1,            # CON borde para debug
            fill=1               # Relleno
        )

        # Banda de gradiente superior (más clara)
        canvas_obj.setFillColor(color_light)
        canvas_obj.setStrokeColor(color_light)
        canvas_obj.rect(
            letter[0] - 2.5*cm,
            letter[1] * 0.5,     # Desde la mitad de la página
            2.5*cm,
            letter[1] * 0.5,     # Hasta el final
            stroke=1,
            fill=1
        )

        canvas_obj.restoreState()

    def _get_voucher_type_key(self, voucher_type: str, with_return: bool) -> str:
        """Determina la clave de tipo para obtener color y etiqueta."""
        if voucher_type == 'ENTRY':
            return 'ENTRY'
        elif voucher_type == 'EXIT':
            return 'EXIT_RETURN' if with_return else 'EXIT_NO_RETURN'
        else:
            return 'ENTRY'  # Default

    def _build_header(self, label: str, color: colors.Color, folio: str, status: str, company_name: str):
        """Construye el encabezado del documento con badges."""
        elements = []

        # Mapeo de estados a español
        status_map = {
            'PENDING': 'PENDIENTE',
            'APPROVED': 'APROBADO',
            'IN_TRANSIT': 'EN TRÁNSITO',
            'OVERDUE': 'VENCIDO',
            'CLOSED': 'CERRADO',
            'CANCELLED': 'CANCELADO'
        }
        status_texto = status_map.get(status, status)

        # Nombre de empresa
        company_para = Paragraph(company_name, self.styles['CompanyName'])
        elements.append(company_para)
        elements.append(Spacer(1, 0.05*inch))

        # Folio
        folio_para = Paragraph(folio, self.styles['Folio'])
        elements.append(folio_para)
        elements.append(Spacer(1, 0.1*inch))

        # Badge de tipo de voucher (con color de fondo)
        type_badge_data = [[Paragraph(f"<b>{label}</b>", self.styles['TypeBadge'])]]
        type_badge_table = Table(type_badge_data, colWidths=[4.5*inch])
        type_badge_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ROUNDEDCORNERS', [5, 5, 5, 5]),  # Bordes redondeados
        ]))
        elements.append(type_badge_table)
        elements.append(Spacer(1, 0.05*inch))

        # Badge de estado (con color específico)
        status_config = self.STATUS_COLORS.get(status, {
            'bg': colors.HexColor('#e2e3e5'),
            'fg': colors.HexColor('#383d41')
        })

        status_style = ParagraphStyle(
            name='StatusBadgeColored',
            parent=self.styles['StatusBadge'],
            textColor=status_config['fg']
        )

        status_badge_data = [[Paragraph(f"<b>{status_texto}</b>", status_style)]]
        status_badge_table = Table(status_badge_data, colWidths=[2*inch])
        status_badge_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), status_config['bg']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('ROUNDEDCORNERS', [5, 5, 5, 5]),
        ]))
        elements.append(status_badge_table)

        # Línea divisoria
        elements.append(Spacer(1, 0.15*inch))
        line_data = [['']]
        line_table = Table(line_data, colWidths=[5.5*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 3, colors.HexColor('#333333')),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 0.15*inch))

        return elements

    def _build_voucher_info(self, voucher: Any):
        """Construye la sección de metadata del voucher."""
        elements = []

        # Definir las estructura del encabezado en 2 columnas
        col1_data = []
        col2_data = []

        # Mapeo de tipos a español
        tipo_map = {
            'ENTRY': 'ENTRADA',
            'EXIT': 'SALIDA'
        }
        
        tipo_texto = tipo_map.get(voucher.voucher_type, voucher.voucher_type)

        # Columna 1
        col1_data.append([
            Paragraph('<b>Fecha Creación:</b>', self.styles['MetadataLabel']),
            Paragraph(voucher.created_at.strftime("%Y-%m-%d %H:%M"), self.styles['MetadataValue'])
        ])
        col1_data.append([
            Paragraph('<b>Tipo:</b>', self.styles['MetadataLabel']),
            Paragraph(tipo_texto, self.styles['MetadataValue'])
        ])
        col1_data.append([
            Paragraph('<b>Destino:</b>', self.styles['MetadataLabel']),
            Paragraph(
                getattr(voucher.destination_branch, 'name', 'N/A') if hasattr(voucher, 'destination_branch') and voucher.destination_branch else 'N/A',
                self.styles['MetadataValue']
            )
        ])

        # Columna 2
        if hasattr(voucher, 'origin_branch') and voucher.origin_branch:
            col2_data.append([
                Paragraph('<b>Origen:</b>', self.styles['MetadataLabel']),
                Paragraph(getattr(voucher.origin_branch, 'name', 'N/A'), self.styles['MetadataValue'])
            ])

        col2_data.append([
            Paragraph('<b>Con retorno:</b>', self.styles['MetadataLabel']),
            Paragraph('Sí' if voucher.with_return else 'No', self.styles['MetadataValue'])
        ])

        if voucher.estimated_return_date and voucher.with_return:
            col2_data.append([
                Paragraph('<b>Retorno estimado:</b>', self.styles['MetadataLabel']),
                Paragraph(str(voucher.estimated_return_date), self.styles['MetadataValue'])
            ])

        # Crear tablas de columnas
        col1_table = Table(col1_data, colWidths=[1.2*inch, 1.5*inch])
        col1_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))

        col2_table = Table(col2_data, colWidths=[1.2*inch, 1.5*inch])
        col2_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))

        # Combinar columnas en tabla principal
        metadata_table = Table([[col1_table, col2_table]], colWidths=[2.7*inch, 2.7*inch])
        metadata_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
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
        details_table = Table(table_data, colWidths=[0.4*inch, 2.2*inch, 0.8*inch, 0.8*inch, 1.3*inch])

        # Estilos base
        style_commands = [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),  # Header
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Header centrado
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # # centrado
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Cantidad centrada
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
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

    def _build_signatures(self, voucher: Any, voucher_type_key: str):
        """Construye la sección de firmas digitales con líneas elegantes."""
        elements = []

        elements.append(Paragraph('<b>Firmas</b>', self.styles['SectionTitle']))

        # Entregó (siempre presente)
        delivered_name = getattr(voucher.delivered_by, 'name', 'N/A') if hasattr(voucher, 'delivered_by') and voucher.delivered_by else '_____________________'
        sig1 = [
            Paragraph('', self.styles['Body_Custom']),  # Espacio superior
            Paragraph('<b>' + delivered_name + '</b>', self.styles['Body_Custom']),
            Paragraph('<font color="#666666">Entregó</font>', self.styles['Body_Custom'])
        ]

        # Aprobó (si existe)
        if voucher.approved_by_id:
            approved_name = getattr(voucher.approved_by, 'name', 'N/A') if hasattr(voucher, 'approved_by') and voucher.approved_by else '_____________________'
            sig2 = [
                Paragraph('', self.styles['Body_Custom']),
                Paragraph('<b>' + approved_name + '</b>', self.styles['Body_Custom']),
                Paragraph('<font color="#666666">Aprobó</font>', self.styles['Body_Custom'])
            ]
        else:
            sig2 = None

        # Recibió (si existe - para retornos)
        if voucher.received_by_id:
            received_name = getattr(voucher.received_by, 'name', 'N/A') if hasattr(voucher, 'received_by') and voucher.received_by else '_____________________'
            sig3 = [
                Paragraph('', self.styles['Body_Custom']),
                Paragraph('<b>' + received_name + '</b>', self.styles['Body_Custom']),
                Paragraph('<font color="#666666">Recibió</font>', self.styles['Body_Custom'])
            ]
        else:
            sig3 = None

        # Construir fila de firmas (2 o 3 columnas según disponibilidad)
        sig_row = [sig1]
        col_widths = []

        if sig2:
            sig_row.append(sig2)
        if sig3:
            sig_row.append(sig3)

        # Calcular anchos de columnas
        num_sigs = len(sig_row)
        col_width = 5.5 * inch / num_sigs
        col_widths = [col_width] * num_sigs

        # Crear tabla de firmas
        sig_table = Table([sig_row], colWidths=col_widths)

        # Estilos con línea superior (simulando signature-line del CSS)
        style_commands = [
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#333333')),  # Línea de firma
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]

        sig_table.setStyle(TableStyle(style_commands))

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
            center_table = Table([[qr_table]], colWidths=[5.5*inch])
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
            qr_text_table = Table([[qr_text]], colWidths=[5.5*inch])
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
        notes_table = Table([[notes_para]], colWidths=[5.5*inch])
        notes_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))

        elements.append(notes_table)
        return elements

    def _build_footer_with_qr(self, qr_image_path: str):
        """Construye el footer con QR y timestamp."""
        elements = []

        # Línea divisoria superior
        line_data = [['']]
        line_table = Table(line_data, colWidths=[5.5*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#cccccc')),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 0.1*inch))

        # QR Code + Timestamp en dos columnas
        if Path(qr_image_path).exists():
            # QR pequeño (1 inch)
            qr_img = Image(qr_image_path, width=1*inch, height=1*inch)

            # Tabla con QR con borde
            qr_with_border = Table([[qr_img]], colWidths=[1.1*inch])
            qr_with_border.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#333333')),
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            # Texto de QR y timestamp
            generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            text_content = [
                Paragraph('<font color="#666666" size="9"><b>Código QR</b></font>', self.styles['Body_Custom']),
                Spacer(1, 0.05*inch),
                Paragraph(f'<font color="#999999" size="8">Generado: {generated_at} UTC</font>', self.styles['Body_Custom'])
            ]

            text_table = Table([[e] for e in text_content], colWidths=[4.3*inch])
            text_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            # Combinar QR y texto
            footer_content = Table([[qr_with_border, text_table]], colWidths=[1.2*inch, 4.3*inch])
            footer_content.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            elements.append(footer_content)
        else:
            # Solo timestamp si no hay QR
            generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            footer_para = Paragraph(
                f'<font color="#999999" size="8">Generado: {generated_at} UTC</font>',
                self.styles['Body_Custom']
            )
            footer_table = Table([[footer_para]], colWidths=[5.5*inch])
            footer_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            elements.append(footer_table)

        return elements
