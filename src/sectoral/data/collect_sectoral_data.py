"""Compatibility entry point for verified national and sectoral PNAD inputs.

No hand-entered employment/informality/hours shares are emitted as evidence.
Run with --allow-official-fallback if BigQuery authentication is unavailable.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'data_raw'))
from reprocess_verified_inputs import main
if __name__ == '__main__':
    main()
