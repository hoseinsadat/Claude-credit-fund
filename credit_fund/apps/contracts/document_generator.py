import io
import logging
from pathlib import Path

from django.template import Context, Template
from django.utils import timezone

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generate PDF documents from HTML templates using WeasyPrint."""

    BASE_CSS = """
    @font-face {
        font-family: 'Vazirmatn';
        src: url('file:///static/fonts/Vazirmatn-Regular.woff2') format('woff2');
    }
    body {
        font-family: 'Vazirmatn', Tahoma, Arial, sans-serif;
        direction: rtl;
        unicode-bidi: embed;
        font-size: 12pt;
        line-height: 1.8;
    }
    @page {
        size: A4;
        margin: 2cm;
    }
    table { width: 100%; border-collapse: collapse; }
    table th, table td { border: 1px solid #333; padding: 6px 10px; text-align: right; }
    table th { background: #f0f0f0; }
    """

    @staticmethod
    def generate(template_content, context_data):
        """Render HTML template and convert to PDF bytes."""
        try:
            from weasyprint import HTML
        except ImportError:
            logger.error('WeasyPrint not installed')
            return None

        # Render Django template
        template = Template(template_content)
        html_content = template.render(Context(context_data))

        # Wrap with CSS
        full_html = f"""
        <!DOCTYPE html>
        <html lang="fa" dir="rtl">
        <head><meta charset="UTF-8"><style>{PDFGenerator.BASE_CSS}</style></head>
        <body>{html_content}</body>
        </html>
        """

        pdf_bytes = HTML(string=full_html).write_pdf()
        return pdf_bytes


class DOCXGenerator:
    """Generate DOCX documents from .docx templates using python-docx-template."""

    @staticmethod
    def generate(template_file_path, context_data):
        """Render a .docx template with Jinja2 context and return bytes."""
        try:
            from docxtpl import DocxTemplate
        except ImportError:
            logger.error('python-docx-template not installed')
            return None

        doc = DocxTemplate(template_file_path)
        doc.render(context_data)

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.read()


class DocumentService:
    """Facade for document generation."""

    @staticmethod
    def generate_guarantee_letter(guarantee, format='pdf'):
        """Generate a guarantee letter and save to GuaranteeLetter."""
        from apps.guarantees.models import GuaranteeLetter
        from .models import DocumentTemplate

        context = DocumentService._build_guarantee_context(guarantee)

        template = DocumentTemplate.objects.filter(
            template_type=DocumentTemplate.TemplateType.GUARANTEE_LETTER,
            format=format.upper(),
            is_active=True,
        ).first()

        if not template:
            logger.warning('No active template found for guarantee letter (%s)', format)
            return None

        if format == 'pdf' and template.template_content:
            content = PDFGenerator.generate(template.template_content, context)
        elif format == 'docx' and template.file:
            content = DOCXGenerator.generate(template.file.path, context)
        else:
            logger.warning('Template content/file missing for %s', template.code)
            return None

        # Create or update GuaranteeLetter
        letter, created = GuaranteeLetter.objects.get_or_create(
            guarantee=guarantee,
            defaults={
                'letter_date': timezone.now().date(),
                'template_used': template.code,
            },
        )

        if content:
            from django.core.files.base import ContentFile
            filename = f'{guarantee.guarantee_number}.{format}'
            if format == 'pdf':
                letter.generated_pdf.save(filename, ContentFile(content), save=True)
            else:
                letter.generated_docx.save(filename, ContentFile(content), save=True)

        return letter

    @staticmethod
    def generate_contract(contract, format='pdf'):
        """Generate a contract document."""
        from .models import DocumentTemplate

        context = DocumentService._build_contract_context(contract)

        template = DocumentTemplate.objects.filter(
            template_type=DocumentTemplate.TemplateType.CONTRACT,
            format=format.upper(),
            is_active=True,
        ).first()

        if not template:
            return None

        if format == 'pdf' and template.template_content:
            return PDFGenerator.generate(template.template_content, context)
        elif format == 'docx' and template.file:
            return DOCXGenerator.generate(template.file.path, context)
        return None

    @staticmethod
    def generate_fee_statement(client, date_from=None, date_to=None, format='pdf'):
        """Generate a fee statement for a client."""
        from apps.guarantees.models import FeeSchedule
        from .models import DocumentTemplate

        fees = FeeSchedule.objects.filter(guarantee__client=client)
        if date_from:
            fees = fees.filter(due_date__gte=date_from)
        if date_to:
            fees = fees.filter(due_date__lte=date_to)

        context = {
            'client': client,
            'fees': fees,
            'date_from': date_from,
            'date_to': date_to,
            'generated_at': timezone.now(),
        }

        template = DocumentTemplate.objects.filter(
            template_type=DocumentTemplate.TemplateType.FEE_STATEMENT,
            format=format.upper(),
            is_active=True,
        ).first()

        if not template or not template.template_content:
            return None

        return PDFGenerator.generate(template.template_content, context)

    @staticmethod
    def _build_guarantee_context(guarantee):
        return {
            'guarantee': guarantee,
            'client': guarantee.client,
            'beneficiary': guarantee.beneficiary,
            'guarantee_type': guarantee.guarantee_type,
            'amount': guarantee.amount,
            'issue_date': guarantee.issue_date,
            'expiry_date': guarantee.expiry_date,
            'purpose': guarantee.purpose,
            'generated_at': timezone.now(),
        }

    @staticmethod
    def _build_contract_context(contract):
        return {
            'contract': contract,
            'client': contract.client,
            'contract_number': contract.contract_number,
            'start_date': contract.start_date,
            'end_date': contract.end_date,
            'total_value': contract.total_value,
            'generated_at': timezone.now(),
        }
