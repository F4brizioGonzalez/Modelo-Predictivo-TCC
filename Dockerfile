# 1. Imagen base
FROM python:3.13-slim

# 2. Instala uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Directorio de trabajo
WORKDIR /app

# 4. Copia archivos de dependencias
COPY pyproject.toml uv.lock ./

# 5. Instala dependencias desde uv.lock
RUN uv sync --frozen --no-install-project

RUN mkdir -p Data/Logs Data/Processed Data/Sql Reports/Performance Reports/ModelPredictive

# 6. Copia el resto del proyecto
COPY . .

# Crea la estructura de carpetas necesaria para los datos y logs
RUN mkdir -p Data/Logs Data/Processed Data/Sql

# Medidas de Seguridad para limitar los permisos del contenedor
RUN useradd -m appuser 
COPY --chown=appuser:appuser . .
USER appuser

# Puerto de StreamLite
EXPOSE 8501

# Comando por defecto ejecutado a través del entorno virtual de uv
CMD ["uv", "run", "Scripts/Pipeline.py"]