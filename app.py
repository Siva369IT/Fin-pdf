import streamlit as st
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from fpdf import FPDF
import fitz  # PyMuPDF
import os
from PIL import Image
from docx import Document
from pptx import Presentation
import zipfile
import io

st.set_page_config(page_title="All-in-One PDF Tool", layout="centered")
st.image("logo1.png", width=120)
st.title("**All-in-One PDF Converter**")

# Initialize session state
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "operation_selected" not in st.session_state:
    st.session_state.operation_selected = ""

operations = [
    "Select an operation",
    "Generate Empty PDF",
    "Convert Any File to PDF",
    "Images to PDF",
    "Extract Pages from PDF",
    "Merge PDFs",
    "Split PDF",
    "Compress PDF",
    "Insert Page Numbers"
]

file_instructions = {
    "Convert Any File to PDF": "PDF, PNG, JPG, JPEG, TXT, DOCX, PPTX",
    "Images to PDF": "PNG, JPG, JPEG",
    "Extract Pages from PDF": "PDF",
    "Merge PDFs": "PDF",
    "Split PDF": "PDF",
    "Compress PDF": "PDF",
    "Insert Page Numbers": "PDF"
}

if st.session_state.uploaded_files:
    st.info("**You have uploaded files. Please remove them before changing the operation.**")
else:
    operation = st.selectbox("Choose what you'd like to do:", operations)
    if operation != "Select an operation":
        st.session_state.operation_selected = operation

if st.session_state.operation_selected:
    st.markdown(f"### 👉 Allowed files: {file_instructions.get(st.session_state.operation_selected, '')}")

if st.session_state.uploaded_files:
    if st.button("Remove Uploaded Files ❌"):
        st.session_state.uploaded_files = []
        st.session_state.operation_selected = ""
        st.experimental_rerun()

if st.session_state.operation_selected and not st.session_state.uploaded_files:
    file_types_map = {
        "Convert Any File to PDF": ["pdf", "png", "jpg", "jpeg", "txt", "docx", "pptx"],
        "Images to PDF": ["png", "jpg", "jpeg"],
        "Extract Pages from PDF": ["pdf"],
        "Merge PDFs": ["pdf"],
        "Split PDF": ["pdf"],
        "Compress PDF": ["pdf"],
        "Insert Page Numbers": ["pdf"]
    }
    allowed_types = file_types_map.get(st.session_state.operation_selected, [])
    uploaded = st.file_uploader("Upload file(s):", type=allowed_types, accept_multiple_files=True)
    if uploaded:
        st.session_state.uploaded_files = uploaded
        st.experimental_rerun()

# Generate Empty PDF
if st.session_state.operation_selected == "Generate Empty PDF":
    num_pages = st.number_input("Enter number of pages: max-100k", min_value=1, max_value=100000, value=1)
    file_name = st.text_input("Enter file name (without extension):", "empty_pdf")
    if st.button("Generate PDF"):
        pdf = FPDF()
        for i in range(num_pages):
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Page {i + 1}", ln=True, align="C")
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        st.success("PDF generated successfully.")
        st.download_button("Download Empty PDF", pdf_output, f"{file_name}.pdf", mime="application/pdf")

# Convert Any File to PDF (improved)
def convert_file_to_pdf(uploaded_file):
    pdf_bytes = io.BytesIO()
    file_name = uploaded_file.name.lower()

    if uploaded_file.type.startswith("image/"):
        image = Image.open(uploaded_file)
        image.convert("RGB").save(pdf_bytes, format="PDF")
        pdf_bytes.seek(0)
        return pdf_bytes

    elif file_name.endswith(".txt"):
        content = uploaded_file.read().decode()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in content.split("\n"):
            pdf.cell(200, 10, txt=line, ln=True)
        pdf.output(pdf_bytes)
        pdf_bytes.seek(0)
        return pdf_bytes

    elif file_name.endswith(".docx"):
        try:
            doc = Document(uploaded_file)
            pdf = FPDF()
            pdf.set_font("Arial", size=12)
            for para in doc.paragraphs:
                pdf.add_page()
                pdf.multi_cell(0, 10, para.text)
            pdf.output(pdf_bytes)
            pdf_bytes.seek(0)
            return pdf_bytes
        except Exception as e:
            st.error(f"Error converting DOCX: {e}")
            return None

    elif file_name.endswith(".pptx"):
        try:
            prs = Presentation(uploaded_file)
            pdf = FPDF()
            pdf.set_font("Arial", size=12)
            for i, slide in enumerate(prs.slides):
                pdf.add_page()
                pdf.cell(200, 10, txt=f"Slide {i+1}:", ln=True)
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        pdf.multi_cell(0, 10, shape.text)
            pdf.output(pdf_bytes)
            pdf_bytes.seek(0)
            return pdf_bytes
        except Exception as e:
            st.error(f"Error converting PPTX: {e}")
            return None

    elif file_name.endswith(".pdf"):
        return uploaded_file

    else:
        st.warning("Unsupported file type.")
        return None

if st.session_state.operation_selected == "Convert Any File to PDF" and st.session_state.uploaded_files:
    file_name = st.text_input("Enter custom PDF name (without extension):", "converted_file")
    if st.button("Convert and Download"):
        for file in st.session_state.uploaded_files:
            converted_pdf = convert_file_to_pdf(file)
            if converted_pdf:
                st.download_button(f"Download {file_name}.pdf", converted_pdf, f"{file_name}.pdf", mime="application/pdf")

# Images to PDF
if st.session_state.operation_selected == "Images to PDF" and st.session_state.uploaded_files:
    file_name = st.text_input("Enter merged PDF name (without extension):", "images_pdf")
    if st.button("Merge Images and Download"):
        pdf_writer = PdfWriter()
        for image_file in st.session_state.uploaded_files:
            image = Image.open(image_file)
            pdf_bytes = io.BytesIO()
            image.convert("RGB").save(pdf_bytes, format="PDF")
            pdf_bytes.seek(0)
            pdf_reader = PdfReader(pdf_bytes)
            pdf_writer.append(pdf_reader)
        pdf_output = io.BytesIO()
        pdf_writer.write(pdf_output)
        pdf_output.seek(0)
        st.download_button("Download PDF", pdf_output, f"{file_name}.pdf", mime="application/pdf")

# Extract Pages from PDF
if st.session_state.operation_selected == "Extract Pages from PDF" and st.session_state.uploaded_files:
    page_nums = st.text_input("Enter pages to extract (e.g., 1,3,5-7):")
    file_name = st.text_input("Enter extracted PDF name (without extension):", "extracted_pages")
    if st.button("Extract and Download"):
        for file in st.session_state.uploaded_files:
            reader = PdfReader(file)
            writer = PdfWriter()
            pages = []
            for part in page_nums.split(","):
                if "-" in part:
                    start, end = part.split("-")
                    pages.extend(range(int(start), int(end) + 1))
                else:
                    pages.append(int(part))
            for p in pages:
                writer.add_page(reader.pages[p - 1])
            pdf_output = io.BytesIO()
            writer.write(pdf_output)
            pdf_output.seek(0)
            st.download_button("Download Extracted PDF", pdf_output, f"{file_name}.pdf", mime="application/pdf")

# Merge PDFs
if st.session_state.operation_selected == "Merge PDFs" and st.session_state.uploaded_files:
    file_name = st.text_input("Enter merged PDF name (without extension):", "merged_pdf")
    if st.button("Merge and Download"):
        merger = PdfMerger()
        for pdf_file in st.session_state.uploaded_files:
            merger.append(pdf_file)
        merged_output = io.BytesIO()
        merger.write(merged_output)
        merged_output.seek(0)
        st.download_button("Download Merged PDF", merged_output, f"{file_name}.pdf", mime="application/pdf")

# Split PDF
if st.session_state.operation_selected == "Split PDF" and st.session_state.uploaded_files:
    if st.button("Split and Download as ZIP"):
        for file in st.session_state.uploaded_files:
            reader = PdfReader(file)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a") as zip_file:
                for i, page in enumerate(reader.pages):
                    writer = PdfWriter()
                    writer.add_page(page)
                    single_pdf = io.BytesIO()
                    writer.write(single_pdf)
                    single_pdf.seek(0)
                    zip_file.writestr(f"page_{i + 1}.pdf", single_pdf.read())
            zip_buffer.seek(0)
            st.download_button("Download Split PDFs (ZIP)", zip_buffer, "split_pages.zip", mime="application/zip")

# Compress PDF
if st.session_state.operation_selected == "Compress PDF" and st.session_state.uploaded_files:
    file_name = st.text_input("Enter compressed PDF name (without extension):", "compressed_pdf")
    if st.button("Compress and Download"):
        for file in st.session_state.uploaded_files:
            doc = fitz.open(stream=file.read(), filetype="pdf")
            compressed = io.BytesIO()
            doc.save(compressed, garbage=4, deflate=True)
            compressed.seek(0)
            st.download_button("Download Compressed PDF", compressed, f"{file_name}.pdf", mime="application/pdf")

# Insert Page Numbers
if st.session_state.operation_selected == "Insert Page Numbers" and st.session_state.uploaded_files:
    file_name = st.text_input("Enter PDF name with page numbers (without extension):", "page_numbered_pdf")
    if st.button("Insert Numbers and Download"):
        for file in st.session_state.uploaded_files:
            doc = fitz.open(stream=file.read(), filetype="pdf")
            for page in doc:
                page.insert_text((50, 50), f"Page {page.number + 1}", fontsize=10)
            numbered_pdf = io.BytesIO()
            doc.save(numbered_pdf)
            numbered_pdf.seek(0)
            st.download_button("Download Numbered PDF", numbered_pdf, f"{file_name}.pdf", mime="application/pdf")

# Footer
st.markdown("""<hr style="margin-top: 50px;"/>
<small>Developed by  
**Pavan Sri Sai Mondem, Siva Satyamsetti, Uma Satyam Mounika Sapireddy,  
Bhuvaneswari Devi Seru, Chandu Meela, Trainees from techwing 🧡**</small>""", unsafe_allow_html=True)
