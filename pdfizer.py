import re
from pprint import pprint
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
    
    # Split the input data into lines
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
            if any(section['number'] == main_number for section in structured_data):
                # If exists, set current_main to existing
                for section in structured_data:
                    if section['number'] == main_number:
                        current_main = section
                        break
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
                # If exists, append the content
                existing_sub['text'] += f'\n{sub_text}'
                current_subsection = existing_sub
            else:
                # Create a new subsection entry
                current_subsection = {
                    'number': sub_number,
                    'text': sub_text
                }
                current_main['subsections'].append(current_subsection)
            continue
        
        # If the line doesn't match any pattern, append it to the current subsection or main section
        if current_subsection:
            # Append to the current subsection's text with a newline
            current_subsection['text'] += f'\n{stripped_line}'
        elif current_main:
            # Append to the main section's text with a newline
            current_main['text'] += f'\n{stripped_line}'
        else:
            # If no current section, issue a warning
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
    table_data = []
    
    for section in structured_data:
        # Create header row
        header_text = f"{section['number']} {section['text']}".replace('\n', '<br/>')
        header_para = Paragraph(header_text, header_para_style)
        table_data.append([header_para])
        
        for subsection in section['subsections']:
            content_text = f"{subsection['number']} {subsection['text']}"
            pattern = r'^(.*?:.*)$'
            content_text = re.sub(pattern, r'<b>\1</b>', content_text, flags=re.MULTILINE | re.IGNORECASE)
            content_text = content_text.replace('\n', '<br/>')
            content_text = f"<br/>{content_text}<br/><br/>"
            content_para = Paragraph(content_text, content_para_style)
            table_data.append([content_para])
    
    return table_data

def generate_pdf(table_data, table_style, filename="styled_single_column_table.pdf"):
    """
    Generates a PDF with a simple header and the given table data and styles.
    
    Args:
        table_data (list): Data for the table.
        table_style (TableStyle): Styles to apply to the table.
        filename (str): Output PDF filename.
    """
    # Create a PDF document
    pdf = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom style for the header
    header_style = ParagraphStyle(
        name='HeaderStyle',
        parent=styles['Title'],  # Inherits from 'Title' style
        fontName='Helvetica-Bold',  # Bold font
        fontSize=10,  # Larger font size
        leading=22,  # Space between lines
        alignment=1,  # Center alignment
        spaceAfter=20,  # Space after the header
        textColor=colors.gray  # Header text color
    )
    
    # Create the header Paragraph
    header_text = "<u>CALL QUALITY MONITORING FORM</u>"
    header = Paragraph(header_text, header_style)
    elements.append(header)
    
    # Create the table
    table = Table(table_data, colWidths=[500])
    table.setStyle(table_style)
    
    # Add the table to the elements
    elements.append(table)
        
    # Build the PDF
    pdf.build(elements)

# Initialize ReportLab styles
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
    # Parse the text
    parsed_structure = parse_text_to_structure(text)

    # Display the parsed structure for verification
    print("Parsed Structure:")
    pprint(parsed_structure)

    # Create table data
    table_data = create_table_data(parsed_structure)

    # Iterate through table data and apply background colors
    for idx, row in enumerate(table_data):
        if 'HeaderStyle' in row[0].style.name:
            # Apply header background
            table_style.add('BACKGROUND', (0, idx), (-1, idx), header_background)
        else:
            # Apply default background
            table_style.add('BACKGROUND', (0, idx), (-1, idx), colors.white)

    # Generate the PDF
    generate_pdf(table_data, table_style, "styled_single_column_table.pdf")

    print("\nPDF 'styled_single_column_table.pdf' has been generated successfully.")
