from flask import Flask, render_template, request, send_file
import os
import pandas as pd
import random
import string
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')  # Alterado para caminho absoluto
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# gera pdf  
def read(caminho):
    df = pd.read_excel(caminho)
    df['login'] = df['Nome'].apply(lambda x: '_'.join(x.split()[:1] + x.split()[-1:]))  # criar login
    df['senha'] = df['Nome'].apply(lambda x: ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10)))  # gerar senha
    return df

def adicionar_texto(dados, inicio, fim, escritor_pdf, modelo_pdf):
    posicoes = [
        (69, 570), (280, 570), (491, 570), (702, 570),
        (69, 418), (280, 418), (491, 418), (702, 418),
        (69, 268), (280, 268), (491, 268), (702, 268),
        (69, 116), (280, 116), (491, 116), (702, 116)
    ]

    n = len(dados)

    pdf = BytesIO()
    canvas_obj = canvas.Canvas(pdf)
    canvas_obj.setPageSize((800, 600))

    pdfmetrics.registerFont(TTFont('IBMPlexSans-SemiBold', "static/IBMPlexSans-SemiBold.ttf"))
    canvas_obj.setFont("IBMPlexSans-SemiBold", 7.2) # fonte e tamanho
    canvas_obj.setFillColorRGB(0.0, 0.0, 0.0) # cor

    for _ in range(inicio, min(fim, n)):
        nome, login, senha = dados[_]
        x, y = posicoes[_ - inicio]

        canvas_obj.drawString(x, y, nome)
        canvas_obj.drawString(x+11, y-22, login)
        canvas_obj.drawString(x+11, y-34, senha)

    canvas_obj.save()
    pdf.seek(0)

    pagina_modelo = PdfReader(modelo_pdf).pages[0]
    pagina_sobreposicao = PdfReader(pdf).pages[0]
    pagina_modelo.merge_page(pagina_sobreposicao)
    escritor_pdf.add_page(pagina_modelo)

def gerar_pdf(planilha_path, template_path):
    dados = read(planilha_path)
    
    escritor_pdf = PdfWriter()
    n = len(dados)

    for i in range(0, n, 16):
        inicio = i
        fim = min(i + 16, n)
        adicionar_texto(dados.values.tolist(), inicio, fim, escritor_pdf, template_path)
    
    output_pdf = BytesIO()
    escritor_pdf.write(output_pdf)
    output_pdf.seek(0)

    return output_pdf

# flask
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():

    planilha = request.files['planilha']
    template = request.files['template']

    planilha_path = os.path.join(UPLOAD_FOLDER, planilha.filename)
    template_path = os.path.join(UPLOAD_FOLDER, template.filename)
    
    planilha.save(planilha_path)
    template.save(template_path)

    pdf_output = gerar_pdf(planilha_path, template_path)

    return send_file(pdf_output, as_attachment=True, download_name="logins_gerados.pdf", mimetype="application/pdf")

if __name__ == '__main__':
    
    app.run(debug=True)
