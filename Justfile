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
test: install
  uv run --frozen pytest

# Run performance benchmarks
benchmark: install
  uv run --frozen pytest tests/benchmarks/ --benchmark-only --benchmark-json=benchmark_results.json

# Save benchmark baseline
benchmark-save: install
  uv run --frozen pytest tests/benchmarks/ --benchmark-only --benchmark-save=baseline

# Compare benchmarks against latest saved run
benchmark-compare: install
  uv run --frozen pytest tests/benchmarks/ --benchmark-only --benchmark-compare

# Compare benchmarks against baseline and fail if regression > 15%
benchmark-compare-strict: install
  uv run --frozen pytest tests/benchmarks/ --benchmark-only --benchmark-compare --benchmark-compare-fail=mean:15%

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

# Lint documentation
lint-docs: install
  yamllint --strict mkdocs.yml
  pnpm exec markdownlint-cli2 "**/*.md"
  uv run --frozen djlint docs/.overrides
  pnpm exec biome check docs/

# Lint GitHub Actions workflows
lint-actions: install
  actionlint

vale:
  vale sync
  vale docs/

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

# Build the latest documentation
build-docs: clean
  ACLAF_DOCS_ENV=latest uv run mkdocs build
  uv pip freeze > requirements.txt

# Build the documentation for PR preview
[script]
build-docs-pr number: clean
  rm -f mkdocs.pr.yml
  cat << EOF >> mkdocs.pr.yml
  INHERIT: ./mkdocs.yml
  site_name: Aclaf Documentation (PR-{{number}})
  site_url: https://{{number}}-aclaf-docs-pr.tbhb.workers.dev/
  EOF
  uv run mkdocs build
  echo "User-Agent: *\nDisallow: /" > site/robots.txt
  uv pip freeze > requirements.txt

# Deploy latest documentation
deploy-docs: build-docs
  pnpm exec wrangler deploy --env latest

# Deploy documentation preview
deploy-docs-pr number: (build-docs-pr number)
  pnpm exec wrangler versions upload --env pr --preview-alias pr-{{number}}

# Develop the documentation site locally
dev-docs:
  uv run mkdocs serve --livereload
