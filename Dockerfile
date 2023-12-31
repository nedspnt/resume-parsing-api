FROM python:3.9.18-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN python -m spacy download en_core_web_lg

COPY . .

ENV FLASK_APP=api_service.py

RUN ["python", "utils/download_models.py"]

CMD ["flask", "run", "--host", "0.0.0.0"]
