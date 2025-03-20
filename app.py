import streamlit as st
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import fitz  # PyMuPDF
import os
import io
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
from docx import Document
from pptx import Presentation
from docx2pdf import convert as convert_docx
import base64
from datetime import datetime

st.set_page_config(page_title="All-in-One PDF Converter", layout="centered")

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

st.title("All-in-One PDF Converter")

# Hide error details from UI
st.markdown("""
<style>
.css-ffhzg2, .stException {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def remove_uploaded_files():
    st.session_state.uploaded_files = []

def save_uploaded_file(uploaded_file):
    bytes_data = uploaded_file.read()
    return io.BytesIO(bytes_data)

def download_zip(zip_buffer, filename):
    b64 = base64.b64encode(zip_buffer.getvalue()).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="{filename}">Download ZIP</a>'
    st.markdown(href, unsafe_allow_html=True)

operations = [
    "Generate Empty PDF",
    "Convert Any File to PDF (images each as separate PDFs)",
    "Images to PDF (multiple images to single PDF)",
    "Extract Pages from PDF",
    "Merge PDFs",
    "Split PDF",
    "Compress PDF",
    "Insert Page Numbers into PDF"
]

if not st.session_state.uploaded_files:
    operation = st.selectbox("Select Operation", operations)
else:
    st.info("Files uploaded. Remove them before changing operation.")

if st.session_state.uploaded_files:
    if st.button("Remove Uploaded Files"):
        remove_uploaded_files()
        st.experimental_rerun()

if not st.session_state.uploaded_files and 'operation' in locals():
    allowed_formats = {
        "Generate Empty PDF": "No files needed",
        "Convert Any File to PDF (images each as separate PDFs)": "Allowed: JPG, JPEG, PNG, TXT, DOCX, PPTX",
        "Images to PDF (multiple images to single PDF)": "Allowed: JPG, JPEG, PNG",
        "Extract Pages from PDF": "Allowed: PDF",
        "Merge PDFs": "Allowed: PDF",
        "Split PDF": "Allowed: PDF",
        "Compress PDF": "Allowed: PDF",
        "Insert Page Numbers into PDF": "Allowed: PDF"
    }
    st.write(f"**{allowed_formats.get(operation)}**")
    files = st.file_uploader("Upload Files", accept_multiple_files=True)
    if files:
        st.session_state.uploaded_files = files
        st.experimental_rerun()

if st.session_state.uploaded_files:
    uploaded_files = st.session_state.uploaded_files

    if operation == "Generate Empty PDF":
        file_name = st.text_input("PDF name:", "empty_pdf")
        total_pages = st.number_input("Number of pages", min_value=1, step=1, value=1)
        if st.button("Generate"):
            pdf_buffer = io.BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=A4)
            for page in range(total_pages):
                c.drawString(100, 800, f"Page {page + 1}")
                c.showPage()
            c.save()
            pdf_buffer.seek(0)
            st.download_button("Download Empty PDF", pdf_buffer, f"{file_name}.pdf", mime="application/pdf")

    elif operation == "Convert Any File to PDF (images each as separate PDFs)":
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for uploaded_file in uploaded_files:
                file_ext = uploaded_file.name.split('.')[-1].lower()
                if file_ext in ["jpg", "jpeg", "png"]:
                    image = Image.open(save_uploaded_file(uploaded_file))
                    pdf_io = io.BytesIO()
                    image.save(pdf_io, "PDF")
                    pdf_io.seek(0)
                    zf.writestr(f"{uploaded_file.name}.pdf", pdf_io.read())
                elif file_ext == "txt":
                    text = uploaded_file.getvalue().decode("utf-8")
                    pdf_io = io.BytesIO()
                    c = canvas.Canvas(pdf_io, pagesize=A4)
                    c.drawString(100, 800, text)
                    c.save()
                    pdf_io.seek(0)
                    zf.writestr(f"{uploaded_file.name}.pdf", pdf_io.read())
                elif file_ext == "docx":
                    with open("temp_docx.docx", "wb") as f:
                        f.write(uploaded_file.read())
                    convert_docx("temp_docx.docx")
                    with open("temp_docx.pdf", "rb") as f:
                        zf.writestr(f"{uploaded_file.name}.pdf", f.read())
                    os.remove("temp_docx.docx")
                    os.remove("temp_docx.pdf")
                elif file_ext == "pptx":
                    prs = Presentation(save_uploaded_file(uploaded_file))
                    pdf_io = io.BytesIO()
                    c = canvas.Canvas(pdf_io, pagesize=A4)
                    for slide in prs.slides:
                        for shape in slide.shapes:
                            if hasattr(shape, "text"):
                                c.drawString(100, 750, shape.text)
                        c.showPage()
                    c.save()
                    pdf_io.seek(0)
                    zf.writestr(f"{uploaded_file.name}.pdf", pdf_io.read())
        zip_buffer.seek(0)
        download_zip(zip_buffer, "converted_files.zip")

    elif operation == "Images to PDF (multiple images to single PDF)":
        file_name = st.text_input("PDF name:", "images_to_pdf")
        if st.button("Generate PDF"):
            images = [Image.open(save_uploaded_file(f)).convert("RGB") for f in uploaded_files]
            pdf_io = io.BytesIO()
            images[0].save(pdf_io, save_all=True, append_images=images[1:], format="PDF")
            pdf_io.seek(0)
            st.download_button("Download PDF", pdf_io, f"{file_name}.pdf", mime="application/pdf")

    elif operation == "Extract Pages from PDF":
        page_numbers = st.text_input("Enter pages to extract (e.g., 1,3,5-7):")
        file_name = st.text_input("Extracted PDF name:", "extracted_pages")
        if st.button("Extract"):
            pdf = PdfReader(save_uploaded_file(uploaded_files[0]))
            writer = PdfWriter()
            pages = []
            parts = page_numbers.replace(" ", "").split(",")
            for part in parts:
                if "-" in part:
                    start, end = part.split("-")
                    pages.extend(range(int(start) - 1, int(end)))
                else:
                    pages.append(int(part) - 1)
            for p in pages:
                writer.add_page(pdf.pages[p])
            pdf_output = io.BytesIO()
            writer.write(pdf_output)
            pdf_output.seek(0)
            st.download_button("Download Extracted PDF", pdf_output, f"{file_name}.pdf", mime="application/pdf")

    elif operation == "Merge PDFs":
        file_name = st.text_input("Merged PDF name:", "merged_pdf")
        if st.button("Merge"):
            merger = PdfMerger()
            for pdf in uploaded_files:
                merger.append(PdfReader(save_uploaded_file(pdf)))
            pdf_output = io.BytesIO()
            merger.write(pdf_output)
            pdf_output.seek(0)
            st.download_button("Download Merged PDF", pdf_output, f"{file_name}.pdf", mime="application/pdf")

    elif operation == "Split PDF":
        split_method = st.radio("Choose Split Method", ["Split by range", "Split each page into PDF"])
        if split_method == "Split by range":
            range_value = st.number_input("Enter page range to split (e.g., 50)", min_value=1, step=1)
            if st.button("Split by Range"):
                pdf = PdfReader(save_uploaded_file(uploaded_files[0]))
                num_pages = len(pdf.pages)
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for i in range(0, num_pages, range_value):
                        writer = PdfWriter()
                        for j in range(i, min(i + range_value, num_pages)):
                            writer.add_page(pdf.pages[j])
                        pdf_out = io.BytesIO()
                        writer.write(pdf_out)
                        pdf_out.seek(0)
                        zf.writestr(f"part_{i//range_value + 1}.pdf", pdf_out.read())
                zip_buffer.seek(0)
                download_zip(zip_buffer, "split_pdf_parts.zip")
        else:
            if st.button("Split each page"):
                pdf = PdfReader(save_uploaded_file(uploaded_files[0]))
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for i, page in enumerate(pdf.pages):
                        writer = PdfWriter()
                        writer.add_page(page)
                        pdf_out = io.BytesIO()
                        writer.write(pdf_out)
                        pdf_out.seek(0)
                        zf.writestr(f"page_{i + 1}.pdf", pdf_out.read())
                zip_buffer.seek(0)
                download_zip(zip_buffer, "split_pages.zip")

    elif operation == "Compress PDF":
        file_name = st.text_input("Compressed PDF name:", "compressed_pdf")
        if st.button("Compress"):
            pdf = fitz.open(stream=uploaded_files[0].read(), filetype="pdf")
            pdf_output = io.BytesIO()
            pdf.save(pdf_output, garbage=4, deflate=True)
            pdf_output.seek(0)
            st.download_button("Download Compressed PDF", pdf_output, f"{file_name}.pdf", mime="application/pdf")

    elif operation == "Insert Page Numbers into PDF":
        file_name = st.text_input("PDF name with page numbers:", "numbered_pdf")
        if st.button("Add Page Numbers"):
            pdf = fitz.open(stream=uploaded_files[0].read(), filetype="pdf")
            for page in pdf:
                page.insert_text((72, 820), f"Page {page.number + 1}", fontsize=12)
            pdf_output = io.BytesIO()
            pdf.save(pdf_output)
            pdf_output.seek(0)
            st.download_button("Download Numbered PDF", pdf_output, f"{file_name}.pdf", mime="application/pdf")

st.write("---")
st.markdown("<small>&copy; Pavan Sri Sai Mondem, Siva Satyamsetti, Uma Satyam Mounika Sapireddy, Bhuvaneswari Devi Seru, Chandu Meela</small>", unsafe_allow_html=True)
