{
    'name': 'TRCF Custom Brand - POS Logo',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Replace POS navbar logo with company logo',
    'description': """
        Simple module to replace the Odoo logo in POS navbar with company logo.
        The logo will be taken from Settings > Companies > Your Company > Logo.
    """,
    'author': 'TRCF',
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'trcf_custom_brand/static/src/js/pos_branding.js',
            'trcf_custom_brand/static/src/scss/pos_branding.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
