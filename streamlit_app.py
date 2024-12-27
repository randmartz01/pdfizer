import streamlit as st
from openai import OpenAI
from pdfizer import pdfizer
from io import BytesIO

# Show title and description.
st.title("💬 PDFizer")
st.write(
    "QA Result to PDF"
)

text_input = st.text_area(
    "📋 Enter Your Structured Text Here:",
    height=300)

# Button to generate PDF
if st.button("🖨️ Generate PDF"):
    if not text_input.strip():
        st.error("❌ Please enter some text to generate a PDF.")
    else:
        try:
            # Generate PDF using the pdfizer function
            pdf_bytes = pdfizer(text_input)
            
            # Ensure pdfizer returns bytes. If it returns a file path, read the file.
            if isinstance(pdf_bytes, str):
                with open(pdf_bytes, "rb") as f:
                    pdf_bytes = f.read()
            
            # Create a BytesIO buffer from the PDF bytes
            pdf_buffer = BytesIO(pdf_bytes)
            
            # Inform the user that PDF was generated successfully
            st.success("✅ PDF generated successfully!")
            
            # Provide a download button for the PDF
            st.download_button(
                label="📥 Download PDF",
                data=pdf_buffer,
                file_name="generated_output.pdf",
                mime="application/pdf"
            )
        
        except Exception as e:
            st.error(f"❌ An error occurred while generating the PDF: {e}")