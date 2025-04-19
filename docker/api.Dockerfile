FROM python:3.7

ARG SSL_CERT
ARG SSL_KEY

ENV SSL_KEY=${SSL_KEY}
ENV SSL_CERT=${SSL_CERT}

WORKDIR /usr/src/app

RUN mkdir ssl

RUN echo "$SSL_CERT" > ./ssl/cert.crt
RUN echo "$SSL_KEY" > ./ssl/key.key

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-u", "src/app.py"]

