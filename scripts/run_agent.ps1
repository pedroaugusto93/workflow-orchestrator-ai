$ErrorActionPreference = "Stop"
if (-not (Test-Path ".venv\\Scripts\\python.exe")) {
  py -m venv .venv
}
& .venv\\Scripts\\python.exe -m pip install -e .
& .venv\\Scripts\\python.exe -m apps.agent.main
