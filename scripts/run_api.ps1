param(
    [int]$Port = 8044
)

python -m uvicorn feintlex.app:app --reload --host 127.0.0.1 --port $Port
