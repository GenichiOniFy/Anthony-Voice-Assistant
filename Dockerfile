FROM python:3

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY requirements1.txt .

RUN pip install --no-cache-dir -r requirements1.txt

COPY /server/ .

COPY master.zip /root/.cache/torch/hub/master.zip 

CMD ["python", "./server.py"]

