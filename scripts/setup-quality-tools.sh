#!/bin/bash
# Setup quality tools and pre-commit hooks

set -e

echo "🔧 Setting up quality tools and pre-commit hooks..."

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first."
    exit 1
fi

# Install dependencies including dev group
echo "📦 Installing dependencies..."
poetry install --with dev,test

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
poetry run pre-commit install

# Run pre-commit on all files to ensure everything passes
echo "🧪 Running pre-commit checks on all files..."
poetry run pre-commit run --all-files || {
    echo "⚠️  Some pre-commit checks failed. This is normal on first run."
    echo "Files have been auto-formatted. Please review changes and commit."
}

# Create git commit message template
echo "📝 Setting up commit message template..."
cat > .gitmessage << 'EOF'
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>
#
# Types: feat, fix, docs, style, refactor, perf, test, chore
# Scope: domain, application, infrastructure, presentation, api, tests
# Subject: imperative, lowercase, no period
# Body: explain what and why (not how)
# Footer: breaking changes, issues references
#
# Example:
# feat(domain): add client balance validation
#
# Implement validation logic for client balance to ensure credit limit
# is not exceeded during charge operations.
#
# Closes #123
EOF

git config commit.template .gitmessage 2>/dev/null || echo "⚠️  Could not set git commit template (not in a git repo?)"

echo "✅ Quality tools setup complete!"
echo ""
echo "📋 Available commands:"
echo "  poetry run lint       - Run linting checks"
echo "  poetry run format     - Format code with black"
echo "  poetry run typecheck  - Run type checking"
echo "  poetry run test       - Run tests"
echo "  poetry run quality    - Run all quality checks"
echo "  pre-commit run --all-files - Run all pre-commit hooks"
echo ""
echo "🎯 Next steps:"
echo "  1. Review and commit any changes made by formatters"
echo "  2. All commits will now run pre-commit hooks automatically"
echo "  3. Run 'poetry run quality' before pushing"
