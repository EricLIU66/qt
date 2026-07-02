$ErrorActionPreference = "Stop"

python -m unittest discover -s tests

if (Get-Command ruff -ErrorAction SilentlyContinue) {
  ruff check .
}

if (Get-Command mypy -ErrorAction SilentlyContinue) {
  mypy packages/qt_core services/api services/worker
}

if (Test-Path "apps/web/node_modules") {
  Push-Location apps/web
  npm run lint
  npm run build
  Pop-Location
}
