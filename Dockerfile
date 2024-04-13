FROM python:3.10-bullseye
WORKDIR /code
COPY src .
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python", "app.py"]