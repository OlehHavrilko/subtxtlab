#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT_DIR="${1:-${OBSIDIAN_VAULT_DIR:-/root/vault/ObsidianVault}}"

README_SRC="$PROJECT_ROOT/README.md"
ENV_EXAMPLE_SRC="$PROJECT_ROOT/.env.example"
README_DST="$VAULT_DIR/CinemaClip-AI-README.md"
ENV_NOTE_DST="$VAULT_DIR/CinemaClip-AI-ENV.md"

if [[ ! -f "$README_SRC" ]]; then
  echo "README.md not found: $README_SRC" >&2
  exit 1
fi

if [[ ! -f "$ENV_EXAMPLE_SRC" ]]; then
  echo ".env.example not found: $ENV_EXAMPLE_SRC" >&2
  exit 1
fi

mkdir -p "$VAULT_DIR"
cp -f "$README_SRC" "$README_DST"

{
  echo "# CinemaClip AI — ENV шаблон"
  echo
  echo "Скопируй блок ниже в файл \`.env\` в корне проекта."
  echo
  echo "\`\`\`env"
  cat "$ENV_EXAMPLE_SRC"
  echo "\`\`\`"
  echo
  echo "## Где брать ключи"
  echo "- \`BOT_TOKEN\`: @BotFather в Telegram"
  echo "- \`GROQ_API_KEY\`: https://console.groq.com/keys"
  echo "- \`SUPABASE_URL\` и \`SUPABASE_KEY\`: Supabase -> Project Settings -> API"
} > "$ENV_NOTE_DST"

echo "Synced Obsidian notes:"
echo "- $README_DST"
echo "- $ENV_NOTE_DST"
