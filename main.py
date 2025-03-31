from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import fitz  # PyMuPDF
import os
import uuid
import zipfile

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def compress_pdf(input_path, output_path, quality=40):
    doc = fitz.open(input_path)
    for page in doc:
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            from PIL import Image
            from io import BytesIO

            img_pil = Image.open(BytesIO(image_bytes))
            buf = BytesIO()
            img_pil.save(buf, format="JPEG", quality=quality)

            # Substitui imagem diretamente no xref original
            page.replace_image(xref, stream=buf.getvalue())

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload/")
async def upload(files: list[UploadFile] = File(...)):
    compressed_files = []

    for uploaded_file in files:
        filename = uploaded_file.filename
        input_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{filename}")
        output_path = os.path.join(UPLOAD_FOLDER, filename)

        # Salva o arquivo original
        with open(input_path, "wb") as f:
            f.write(await uploaded_file.read())

        # Compacta mantendo o nome original
        compress_pdf(input_path, output_path)
        compressed_files.append(output_path)

    # Se for apenas 1 arquivo, devolve direto o PDF
    if len(compressed_files) == 1:
        return FileResponse(compressed_files[0], media_type="application/pdf",
                            filename=os.path.basename(compressed_files[0]))

    # Se for mais de 1, cria um ZIP
    zip_name = os.path.join(UPLOAD_FOLDER, f"compressed_{uuid.uuid4().hex[:8]}.zip")
    with zipfile.ZipFile(zip_name, "w") as zipf:
        for file in compressed_files:
            zipf.write(file, arcname=os.path.basename(file))

    return FileResponse(zip_name, media_type="application/zip", filename=os.path.basename(zip_name))
