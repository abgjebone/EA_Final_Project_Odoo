# _*_ coding: utf-8 _*_
{
    'name': "hotel",
    'summary': "Hotel Management System",
    'description': "Hotel Guest Registration and Billing System",
    'author': "abgj",
    'website': "https://www.abgj.odoo.com",

    'category': 'Uncategorized',
    'version': '19.0.1.4.0',

    'depends': ['base', 'web'],

    'license': 'LGPL-3',

    # Always loaded data
    'data': [
            'views/mainmenu.xml',
            'models/views/guests.xml',
            'models/views/guestregistration.xml',
            'models/views/charges.xml',
            'models/views/rooms.xml',
            'models/views/roomtypes.xml',
            'security/ir.model.access.csv',
    ],

    'installable': True,
    'application': True,
}