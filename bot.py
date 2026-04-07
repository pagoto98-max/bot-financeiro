import pandas as pd
import pdfplumber
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")

def categorizar(desc):
    desc = desc.lower()

    if any(p in desc for p in ["posto", "uber", "99"]):
        return "🚗 Transporte"
    elif any(p in desc for p in ["ifood", "restaurante", "mercado"]):
        return "🍔 Alimentação"
    elif "farmacia" in desc:
        return "💊 Saúde"
    elif "clinica" in desc or "vet" in desc:
        return "🐾 Profissional"
    elif "pix" in desc:
        return "💸 Transferência"
    else:
        return "📦 Outros"

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    file_path = "extrato.pdf"
    await file.download_to_drive(file_path)

    texto = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            texto += page.extract_text() + "\n"

    linhas = texto.split("\n")
    dados = []

    for linha in linhas:
        if "R$" in linha:
            try:
                valor = float(linha.split("R$")[-1].replace(".", "").replace(",", "."))
                descricao = linha.split("R$")[0]
                categoria = categorizar(descricao)
                dados.append([descricao, valor, categoria])
            except:
                pass

    df = pd.DataFrame(dados, columns=["Descricao", "Valor", "Categoria"])
    resumo = df.groupby("Categoria")["Valor"].sum()

    resposta = "📊 Resumo dos gastos:\n\n"
    for cat, val in resumo.items():
        resposta += f"{cat}: R$ {val:.2f}\n"

    await update.message.reply_text(resposta)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

app.run_polling()
