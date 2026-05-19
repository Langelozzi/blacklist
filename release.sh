#!/bin/bash

# Release script: reads VERSION file, creates git tag, and pushes to GitHub

VERSION=$(cat VERSION)

echo "[+] Creating release for version v$VERSION..."

# Create annotated git tag
git tag -a "v$VERSION" -m "Release v$VERSION"

# Push tag to GitHub
git push origin "v$VERSION"

echo "[+] Release v$VERSION created and pushed to GitHub!"
