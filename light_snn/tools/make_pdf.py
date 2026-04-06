from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from datetime import datetime
import os

def load_sections(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = [l.rstrip('\n') for l in f]
    headings = {
        'Scope',
        'Architecture Overview',
        'Arduino Frame Format',
        'Serial Ingestion',
        'SNNController: State and Parameters',
        'Weight Initialization',
        'Sensor → Spike Encoding',
        'Synaptic Current and LIF',
        'Training',
        'Prototype Bias and Decision Selection',
        'Calibration Gating',
        'UI and Direction Output',
        'CLI Parameters (main.py)',
        'Execution Flow (main.py)',
        'Memristor Model',
        'Design Rationale',
        'Known Behaviors',
        'File References',
    }
    sections = []
    cur_title = None
    cur_body = []
    for line in lines:
        if line.strip() in headings:
            if cur_title is not None:
                sections.append((cur_title, '\n'.join(cur_body).strip()))
            cur_title = line.strip()
            cur_body = []
        else:
            cur_body.append(line)
    if cur_title is not None:
        sections.append((cur_title, '\n'.join(cur_body).strip()))
    return sections

def build_pdf(in_path, out_path):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleCenter', parent=styles['Title'], alignment=1, fontSize=22, spaceAfter=18))
    styles.add(ParagraphStyle(name='Heading', parent=styles['Heading2'], spaceBefore=14, spaceAfter=6))
    styles.add(ParagraphStyle(name='Body', parent=styles['BodyText'], leading=14, spaceAfter=8))
    doc = SimpleDocTemplate(out_path, pagesize=A4, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    story.append(Paragraph('LDR SNN: System Architecture and Methods', styles['TitleCenter']))
    story.append(Paragraph(datetime.now().strftime('%Y-%m-%d'), styles['Body']))
    story.append(Spacer(1, 0.25*inch))
    with open(in_path, 'r', encoding='utf-8') as f:
        text = f.read()
    abstract = 'This report summarizes the light_snn system, including sensor acquisition, serial framing, spiking neural network dynamics, training procedures, prototype-based similarity readout, hysteresis, visualization UI, and robot actuation via ESP32. Source references are provided to enable reproducibility and precise navigation of the implementation.'
    story.append(Paragraph('Abstract', styles['Heading']))
    story.append(Paragraph(abstract, styles['Body']))
    story.append(Spacer(1, 0.2*inch))
    sections = load_sections(in_path)
    for title, body in sections:
        story.append(Paragraph(title, styles['Heading']))
        for para in [p for p in body.split('\n') if p.strip()]:
            story.append(Paragraph(para, styles['Body']))
        story.append(Spacer(1, 0.1*inch))
    doc.build(story)

if __name__ == '__main__':
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    in_path = os.path.join(root, 'review.txt')
    out_path = os.path.abspath(os.path.join(root, '..', 'ldr_snn.pdf'))
    build_pdf(in_path, out_path)
