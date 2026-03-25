#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "=== SEO Evolution Loop ==="
echo "Site: ${SITE_URL:-https://meetspot-irq2.onrender.com/}"
echo ""

# Sync latest GSC data
echo "Syncing GSC data..."
if ! python cli.py gsc sync --days 90; then
    echo "GSC sync failed, continuing with cached data."
fi

# Show status
python cli.py gsc status

# Run evolution
echo ""
echo "Starting evolution loop (mode: ${MODE:-continuous})..."
python cli.py evolve run \
    --site-url "${SITE_URL:-https://meetspot-irq2.onrender.com/}" \
    --max-steps "${MAX_STEPS:-15}" \
    --min-impressions "${MIN_IMPRESSIONS:-5}" \
    --mode "${MODE:-continuous}"
