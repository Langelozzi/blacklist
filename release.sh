#!/bin/bash

# Release script: commits VERSION file, creates git tag, and pushes to GitHub

VERSION=$(cat VERSION)

echo "[+] Creating release for version v$VERSION..."

# Commit VERSION file changes
git add VERSION
git commit -m "Release v$VERSION"

# Push commits to GitHub
git push origin main

# Create annotated git tag
git tag -a "v$VERSION" -m "Release v$VERSION"

# Push tag to GitHub
git push origin "v$VERSION"

echo "[+] Release v$VERSION created and pushed to GitHub!"
