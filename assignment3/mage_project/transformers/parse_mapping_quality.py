from pathlib import Path

from mage_ai.data_preparation.decorators import transformer


@transformer
def transform(data, *args, **kwargs):
    result_path = Path(data['qc_result'])
    values = {}
    for line in result_path.read_text(encoding='utf-8').splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            values[key] = value

    return {
        **data,
        'mapped_percent': float(values['mapped_percent']),
        'status': values['status'],
    }
