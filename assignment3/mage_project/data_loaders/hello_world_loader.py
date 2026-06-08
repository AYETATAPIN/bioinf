from mage_ai.data_preparation.decorators import data_loader


@data_loader
def load_data(*args, **kwargs):
    return {
        'message': 'Hello world from Mage',
        'framework': 'Mage',
        'assignment': 3,
    }
