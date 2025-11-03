set unstable

# List available recipes
default:
  @just --list

# Install all dependencies (Python + Node.js)
install:
  uv sync --frozen
  pnpm install

# Build the Python package
build: install
  uv build

# Run tests
test p: install
  cd "packages/{{p}}" && uv run --frozen pytest

# Format code
format: install
  uv run --frozen codespell -w
  uv run --frozen ruff format .
  pnpm exec biome format --write .
  pnpm exec markdownlint-cli2 --fix "**/*.md"
  uv run --frozen djlint docs/overrides --reformat

# Lint code
lint: install
  uv run --frozen codespell
  uv run --frozen yamllint --strict .
  uv run --frozen ruff check .
  uv run --frozen basedpyright
  pnpm exec biome check .
  pnpm exec markdownlint-cli2 "**/*.md"
  uv run --frozen djlint docs/overrides

# Lint GitHub Actions workflows
lint-actions: install
  actionlint

# Run pre-commit hooks
prek: install
  uv run --frozen prek

# Clean build artifacts
clean:
  rm -rf site/
  rm -rf dist/
  rm -rf build/
  find . -type d -name __pycache__ -exec rm -rf {} +
  find . -type d -name .pytest_cache -exec rm -rf {} +
  find . -type d -name .ruff_cache -exec rm -rf {} +
