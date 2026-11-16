FROM python:3.11-slim
WORKDIR /srv
# torch CPU (imagem bem menor que a versão com CUDA)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY ia-visao/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# baixa o CLIP no build para a subida do container ser rápida
RUN python -c "from transformers import CLIPModel, CLIPProcessor as P; m='openai/clip-vit-base-patch32'; CLIPModel.from_pretrained(m); P.from_pretrained(m)"
COPY ia-visao/app ./app
COPY prompts ./prompts
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
