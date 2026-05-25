# 1. Imagen base
FROM python:3.13-slim

# 2. Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Directorio de trabajo
WORKDIR /app

# 4. Copiar archivos de dependencias
COPY pyproject.toml uv.lock ./

# 5. Instalar dependencias desde uv.lock
RUN uv sync --frozen --no-install-project


# 6. Copiar el resto del proyecto
COPY . .

# Crear la estructura de carpetas necesaria para los datos y logs
RUN mkdir -p Data/Logs Data/Processed Data/Sql

# Comando por defecto ejecutado a través del entorno virtual de uv
CMD ["uv", "run", "Scripts/Pipeline.py"]