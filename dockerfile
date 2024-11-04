FROM python:3.12

WORKDIR /code

COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src

CMD ["python", "-m", "src.main", "--host", "0.0.0.0", "--port", "80", "--reload"]