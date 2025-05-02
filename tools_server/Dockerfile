FROM python:3.11-slim
WORKDIR /srv
COPY . /srv
RUN pip install --no-cache-dir "mcp[fastapi]" aiohttp pydantic==2.*
# playwright only needed for screenshot helpers
RUN pip install playwright && playwright install
CMD ["python", "-m", "tools_server.main"]
