"""Genera el informe PDF desde el Markdown. Requiere reportlab."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'output/pdf/Documentacion_PF2025.pdf'
DEST.parent.mkdir(parents=True, exist_ok=True)
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyPF',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=7,textColor=colors.HexColor('#243447')))
styles.add(ParagraphStyle(name='TitlePF',fontName='Helvetica-Bold',fontSize=20,leading=24,spaceAfter=12,textColor=colors.HexColor('#143953')))
styles.add(ParagraphStyle(name='H2PF',fontName='Helvetica-Bold',fontSize=15,leading=19,spaceAfter=10,textColor=colors.HexColor('#143953')))
styles.add(ParagraphStyle(name='H3PF',fontName='Helvetica-Bold',fontSize=11,leading=15,spaceBefore=7,spaceAfter=7,textColor=colors.HexColor('#16717a')))
styles.add(ParagraphStyle(name='CellPF',fontName='Helvetica',fontSize=9,leading=12))
styles.add(ParagraphStyle(name='CodePF',fontName='Courier',fontSize=8.2,leading=11,spaceBefore=5,spaceAfter=9,backColor=colors.HexColor('#f1f5f8'),borderPadding=7))

def inline(text):
    text = escape(text.replace('\u200b',''))
    text = re.sub(r'`([^`]+)`',r'<font name="Courier">\1</font>',text)
    return re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',text)

story=[]
lines=(ROOT/'documentacion_semantica.md').read_text(encoding='utf-8-sig').splitlines()
i=0
while i<len(lines):
    line=lines[i]
    if not line.strip():
        i+=1;continue
    if line=='<!-- pagebreak -->':
        story.append(PageBreak());i+=1;continue
    if line.startswith('```'):
        code=[];i+=1
        while i<len(lines) and not lines[i].startswith('```'):
            code.append(lines[i]);i+=1
        story.append(Preformatted('\n'.join(code),styles['CodePF']));i+=1;continue
    if line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].startswith('|'):
            cells=[c.strip() for c in lines[i].strip('|').split('|')]
            if not all(re.fullmatch(r'[-: ]+',c) for c in cells):
                rows.append([Paragraph(inline(c),styles['CellPF']) for c in cells])
            i+=1
        width=A4[0]-96
        widths=[width*.33,width*.67] if len(rows[0])==2 else [width*.38,width*.39,width*.23]
        table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcebf0')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f9')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#8ca6b4'))]))
        story.extend([table,Spacer(1,9)]);continue
    style='BodyPF'
    for prefix,name in [('### ','H3PF'),('## ','H2PF'),('# ','TitlePF')]:
        if line.startswith(prefix):
            line=line[len(prefix):];style=name;break
    if line.startswith('- '):line='• '+line[2:]
    story.append(Paragraph(inline(line),styles[style]));i+=1

def footer(canvas,doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#ccd7df'));canvas.line(48,42,A4[0]-48,42)
    canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#526676'))
    canvas.drawString(48,29,'PF2025 | Análisis léxico y semántico')
    canvas.drawRightString(A4[0]-48,29,str(doc.page))
    canvas.restoreState()

SimpleDocTemplate(str(DEST),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=40,bottomMargin=55,
                  title='Analizador léxico y semántico PF2025',author='Proyecto PF2025').build(story,onFirstPage=footer,onLaterPages=footer)
print(DEST)
