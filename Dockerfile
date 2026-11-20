FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PUSTAHA_API_HOST=0.0.0.0 \
    PORT=7860 \
    PUSTAHA_DEVICE=cpu \
    TORCH_HOME=/tmp/torch \
    FVCORE_CACHE=/tmp/fvcore

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
      torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir \
      numpy==1.26.4 pillow opencv-python-headless pycocotools && \
    pip install --no-cache-dir --no-build-isolation \
      "git+https://github.com/facebookresearch/detectron2.git"

WORKDIR /app
COPY 01_model ./01_model
COPY 02_transliteration ./02_transliteration
COPY 03_web_app ./03_web_app

EXPOSE 7860

CMD ["python", "03_web_app/jalankan_api.py"]
