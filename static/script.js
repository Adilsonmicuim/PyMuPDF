const fileInput = document.getElementById("file-input");
const fileCountText = document.getElementById("file-count");

fileInput.addEventListener("change", () => {
    const count = fileInput.files.length;
    fileCountText.textContent = count === 0
        ? "Nenhum arquivo selecionado"
        : `${count} arquivo${count > 1 ? "s" : ""} selecionado${count > 1 ? "s" : ""}`;
});

document.getElementById("upload-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const statusDiv = document.getElementById("status");
    statusDiv.innerHTML = "⏳ Compactando...";

    const formData = new FormData();
    const files = fileInput.files;

    for (let file of files) {
        formData.append("files", file);
    }

    const response = await fetch("/upload/", {
        method: "POST",
        body: formData
    });

    if (!response.ok) {
        statusDiv.innerHTML = "❌ Erro ao compactar os PDFs.";
        return;
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get("content-disposition");
    const filename = contentDisposition
        ? contentDisposition.split("filename=")[1].replace(/["']/g, "")
        : "arquivo_compactado.pdf";

    const link = document.createElement("a");
    link.href = window.URL.createObjectURL(blob);
    link.download = filename;
    link.click();

    statusDiv.innerHTML = `✅ Download iniciado: ${filename}`;
});
