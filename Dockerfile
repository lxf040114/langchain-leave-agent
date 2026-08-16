FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8503

ENV STREAMLIT_SERVER_PORT=8503
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

CMD ["streamlit", "run", "app.py", \
     "--server.port=8503", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
