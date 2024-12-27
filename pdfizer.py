import re
from pprint import pprint
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

def parse_text_to_structure(data):
    """
    Parses structured text with hierarchical numbering into a list of dictionaries.
    Groups entries with the same identifier by concatenating their content.
    
    Args:
        data (str): The input text containing sections and subsections.
    
    Returns:
        list: A list of dictionaries representing the structured data.
    """
    import re
    data = re.sub("Score:.*", "", data, flags=re.DOTALL)
    data = re.sub(r"\s+\-", "\n&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;", data)
    data = re.sub(r"Sentence\s*\d+:\s*", "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-&nbsp;", data)
    data = re.sub(r"\n\nTranscription\(s\):", "<br/>", data, flags=re.DOTALL)
    data = re.sub(r"Recommendation\(s\):", "<br/>Recommendation(s):", data)
    
    # Define regex patterns for main sections and subsections
    main_section_pattern = re.compile(r'^([A-Z]\.)\s+(.*)')
    subsection_pattern = re.compile(r'^([A-Z]\.\d+)\s+(.*)')
    
    # Initialize the structured list
    structured_data = []
    current_main = None
    current_subsection = None
    
    # Split the input data into lines (do not strip them, to preserve indentation/format)
    lines = data.splitlines()
    
    for line_num, line in enumerate(lines, start=1):
        stripped_line = line
        if not stripped_line:
            continue  # Skip empty lines
        
        # Check for main section (e.g., A.)
        main_match = main_section_pattern.match(stripped_line)
        if main_match:
            main_number = main_match.group(1)
            main_text = main_match.group(2)
            # Check if this main section already exists
            existing_main = next((section for section in structured_data if section['number'] == main_number), None)
            if existing_main:
                current_main = existing_main
            else:
                # Create a new main section entry
                current_main = {
                    'number': main_number,
                    'text': main_text,
                    'subsections': []
                }
                structured_data.append(current_main)
            current_subsection = None  # Reset current subsection
            continue
        
        # Check for subsection (e.g., A.1)
        sub_match = subsection_pattern.match(stripped_line)
        if sub_match and current_main:
            sub_number = sub_match.group(1)
            sub_text = sub_match.group(2)
            # Check if this subsection already exists
            existing_sub = next((sub for sub in current_main['subsections'] if sub['number'] == sub_number), None)
            if existing_sub:
                # Append content to existing subsection
                existing_sub['text'] += f'\n{sub_text}'
                current_subsection = existing_sub
            else:
                # Create a new subsection
                current_subsection = {
                    'number': sub_number,
                    'text': sub_text
                }
                current_main['subsections'].append(current_subsection)
            continue
        
        # If the line doesn't match main or subsection, append it to the current subsection or main section
        if current_subsection:
            current_subsection['text'] += f'\n{stripped_line}'
        elif current_main:
            current_main['text'] += f'\n{stripped_line}'
        else:
            print(f"Warning: Line {line_num} is outside of any section or subsection: {stripped_line}")
    
    return structured_data

def create_table_data(structured_data):
    """
    Converts structured data into table data with Paragraphs.
    
    Args:
        structured_data (list): Parsed structured data.
    
    Returns:
        list: Table data suitable for ReportLab's Table.
    """
    import re
    
    table_data = []
    
    for section in structured_data:
        # Create a 'header row'
        header_text = f"{section['number']} {section['text']}".replace('\n', '<br/>')
        header_para = Paragraph(header_text, header_para_style)
        table_data.append([header_para])
        
        # Now process each subsection
        for subsection in section['subsections']:
            content_text = f"{subsection['number']} {subsection['text']}"
            # Optional: bold any "Xyz:" lines
            pattern = r'^(.*?:.*)$'
            content_text = re.sub(pattern, r'<b>\1</b>', content_text, flags=re.MULTILINE | re.IGNORECASE)
            # Replace newlines with <br/> for multiline rendering
            content_text = content_text.replace('\n', '<br/>')
            # Add extra spacing
            content_text = f"<br/>{content_text}<br/><br/>"
            
            content_para = Paragraph(content_text, content_para_style)
            table_data.append([content_para])
    
    return table_data

def generate_pdf_in_memory(table_data, table_style):
    """
    Generates a PDF with a simple header and the given table data and styles, returning PDF bytes.
    
    Args:
        table_data (list): Data for the table (list of lists).
        table_style (TableStyle): Styles to apply to the table.
    
    Returns:
        bytes: The generated PDF in bytes.
    """
    from reportlab.platypus import SimpleDocTemplate, Table
    
    buffer = BytesIO()
    
    # Create a PDF document in memory
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        name='HeaderStyle',
        parent=styles['Title'],  # Inherits from 'Title' style
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=22,
        alignment=1,  # Center
        spaceAfter=20,
        textColor=colors.gray
    )
    
    # Create the header Paragraph
    header_text = "<u>CALL QUALITY MONITORING FORM</u>"
    header = Paragraph(header_text, header_style)
    elements.append(header)
    
    # Create the table (single column width 500)
    tbl = Table(table_data, colWidths=[500])
    tbl.setStyle(table_style)
    
    # Add the table to the elements
    elements.append(tbl)
    
    # Build the PDF
    pdf.build(elements)
    
    # Retrieve the PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# -- Initialize ReportLab styles --
styles = getSampleStyleSheet()

# Define a style for header rows
header_para_style = ParagraphStyle(
    'HeaderStyle',
    parent=styles['Normal'],
    fontName='Times-Bold',
    fontSize=12,
    textColor=colors.white,
    alignment=TA_LEFT
)

# Define a style for content rows
content_para_style = ParagraphStyle(
    'ContentStyle',
    parent=styles['Normal'],
    fontName='Times-Roman',
    fontSize=10,
    textColor=colors.black,
    alignment=TA_LEFT
)

# Define table styles
table_style = TableStyle([
    # Grid lines for all cells
    ('GRID', (0,0), (-1,-1), 1, colors.black),
    
    # Alignment for all cells
    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    
    # Padding for all cells
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING', (0,0), (-1,-1), 5),
    ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ('TOPPADDING', (0,0), (-1,-1), 5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
])

# Define the header background color
header_background = colors.Color(0/255, 51/255, 102/255)  # RGB (0, 51, 102)

def pdfizer(text):
    """
    Generates the PDF in-memory (returns bytes).
    
    Args:
        text (str): The raw input text to be parsed and converted into a PDF.
    
    Returns:
        bytes: The PDF bytes, suitable for downloading or further processing.
    """
    # 1. Parse the text
    parsed_structure = parse_text_to_structure(text)
    print("Parsed Structure:")
    pprint(parsed_structure)
    
    # 2. Create table data
    table_data = create_table_data(parsed_structure)
    
    # 3. Style the rows (header vs. default)
    #    We detect header rows by checking the 'HeaderStyle' in the Paragraph
    for idx, row in enumerate(table_data):
        if row and len(row) > 0:
            # Check if 'HeaderStyle' is in the Paragraph style name
            if 'HeaderStyle' in row[0].style.name:
                table_style.add('BACKGROUND', (0, idx), (-1, idx), header_background)
            else:
                table_style.add('BACKGROUND', (0, idx), (-1, idx), colors.white)
    
    # 4. Generate PDF in memory
    pdf_bytes = generate_pdf_in_memory(table_data, table_style)
    
    print("\nPDF was generated in memory successfully.")
    return pdf_bytes
