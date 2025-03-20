import streamlit as st
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from fpdf import FPDF
import fitz  # PyMuPDF
from PIL import Image
import zipfile
import io

st.set_page_config(page_title="All-in-One PDF Tool", layout="centered")
st.image("assets/logo1.png", width=120)
st.title("**All-in-One PDF Converter**")

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

if not st.session_state.uploaded_files:
    operation = st.selectbox("Choose what you'd like to do:", operations)
    if operation != "Select an operation":
        st.session_state.operation_selected = operation
else:
    st.info("**Files uploaded. Remove them before changing operation.**")

if st.session_state.operation_selected:
    st.markdown(f"### Allowed files: {file_instructions.get(st.session_state.operation_selected, '')}")

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
if st.session_state.operation_selected == "Generate Empty PDF-maxx-100k":
    num_pages = st.number_input("Number of pages:", min_value=1, max_value=100000, value=1)
    file_name = st.text_input("Enter file name:", "empty_pdf")
    if st.button("Generate PDF"):
        pdf = FPDF()
        for i in range(num_pages):
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Page {i + 1}", ln=True, align="C")
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        st.download_button("Download Empty PDF", pdf_output, f"{file_name}.pdf", mime="application/pdf")

# Convert Any File to PDF
def convert_file_to_pdf(uploaded_file):
    if uploaded_file.type.startswith("image/"):
        image = Image.open(uploaded_file)
        pdf_bytes = io.BytesIO()
        image.convert("RGB").save(pdf_bytes, format="PDF")
        pdf_bytes.seek(0)
        return pdf_bytes
    elif uploaded_file.name.endswith(".txt"):
        content = uploaded_file.read().decode()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in content.split("\n"):
            pdf.cell(200, 10, txt=line, ln=True)
        pdf_bytes = io.BytesIO()
        pdf.output(pdf_bytes)
        pdf_bytes.seek(0)
        return pdf_bytes
    elif uploaded_file.name.endswith((".pdf", ".docx", ".pptx")):
        return uploaded_file
    return None

if st.session_state.operation_selected == "Convert Any File to PDF" and st.session_state.uploaded_files:
    file_name = st.text_input("Enter PDF name:", "converted_file")
    if st.button("Convert and Download"):
        for file in st.session_state.uploaded_files:
            converted_pdf = convert_file_to_pdf(file)
            if converted_pdf:
                st.download_button(f"Download {file_name}.pdf", converted_pdf, f"{file_name}.pdf", mime="application/pdf")

# Images to PDF
if st.session_state.operation_selected == "Images to PDF" and st.session_state.uploaded_files:
    file_name = st.text_input("PDF name:", "images_pdf")
    if st.button("Merge Images"):
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
    file_name = st.text_input("Extracted PDF name:", "extracted_pages")
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
    file_name = st.text_input("Merged PDF name:", "merged_pdf")
    if st.button("Merge and Download"):
        merger = PdfMerger()
        for pdf_file in st.session_state.uploaded_files:
            merger.append(pdf_file)
        merged_output = io.BytesIO()
        merger.write(merged_output)
        merged_output.seek(0)
        st.download_button("Download Merged PDF", merged_output, f"{file_name}.pdf", mime="application/pdf")

# Split PDF with new option A & B
if st.session_state.operation_selected == "Split PDF" and st.session_state.uploaded_files:
    split_option = st.radio("Select splitting option:", ["A) Split by range", "B) Split each page to PDF ZIP"])
    if split_option == "A) Split by range":
        range_size = st.number_input("Enter range size to split (example: 50 pages each file)", min_value=1, value=1)
        if st.button("Split by range and Download"):
            for file in st.session_state.uploaded_files:
                reader = PdfReader(file)
                total_pages = len(reader.pages)
                part = 1
                merger = PdfMerger()
                for start in range(0, total_pages, range_size):
                    writer = PdfWriter()
                    end = min(start + range_size, total_pages)
                    for page_num in range(start, end):
                        writer.add_page(reader.pages[page_num])
                    pdf_buffer = io.BytesIO()
                    writer.write(pdf_buffer)
                    pdf_buffer.seek(0)
                    st.download_button(f"Download Part {part}", pdf_buffer, f"split_part_{part}.pdf", mime="application/pdf")
                    part += 1
    else:
        if st.button("Split pages individually & Download ZIP"):
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
                st.download_button("Download ZIP of Individual Pages", zip_buffer, "split_pages.zip", mime="application/zip")

# Compress PDF
if st.session_state.operation_selected == "Compress PDF" and st.session_state.uploaded_files:
    file_name = st.text_input("Compressed PDF name:", "compressed_pdf")
    if st.button("Compress and Download"):
        for file in st.session_state.uploaded_files:
            doc = fitz.open(stream=file.read(), filetype="pdf")
            compressed = io.BytesIO()
            doc.save(compressed, garbage=4, deflate=True)
            compressed.seek(0)
            st.download_button("Download Compressed PDF", compressed, f"{file_name}.pdf", mime="application/pdf")

# Insert Page Numbers
if st.session_state.operation_selected == "Insert Page Numbers" and st.session_state.uploaded_files:
    file_name = st.text_input("PDF with numbers name:", "numbered_pdf")
    if st.button("Insert Numbers and Download"):
        for file in st.session_state.uploaded_files:
            doc = fitz.open(stream=file.read(), filetype="pdf")
            for page in doc:
                page.insert_text((50, 50), f"Page {page.number + 1}", fontsize=10)
            numbered_pdf = io.BytesIO()
            doc.save(numbered_pdf)
            numbered_pdf.seek(0)
            st.download_button("Download Numbered PDF", numbered_pdf, f"{file_name}.pdf", mime="application/pdf")

st.markdown("""<hr><small>Developed by  
**Pavan Sri Sai Mondem, Siva Satyamsetti, Uma Satyam Mounika Sapireddy,  
Bhuvaneswari Devi Seru, Chandu Meela, Trainees from techwing 🧡**</small>""", unsafe_allow_html=True)
