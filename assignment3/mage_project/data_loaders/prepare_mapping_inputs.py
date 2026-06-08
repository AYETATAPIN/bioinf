from pathlib import Path

from mage_ai.data_preparation.decorators import data_loader


@data_loader
def load_data(*args, **kwargs):
    assignment_dir = Path(__file__).resolve().parents[2]
    return {
        'assignment_dir': str(assignment_dir),
        'script': str(assignment_dir / 'scripts' / 'run_mapping_qc.sh'),
        'sra_run': 'SRR22784690',
        'threshold': 90.0,
    }
