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
        'reports/paperformats.xml',     
        'reports/pageheader.xml',
        'reports/billheader.xml',
        'reports/guestbill.xml',
        'reports/guestbill2.xml',
        'reports/hoteltransaction.xml',
        'reports/hoteltransaction3.xml',
        'reports/hoteltransactiondashboard.xml',
        'wizards/roombillrecord_edit.xml',        
        'wizards/roombillrecord_new.xml',
        'wizards/emailguestbill.xml',
        'security/ir.model.access.csv',
        'models/views/mainmenu.xml',
        'models/views/guestregistration.xml',
        'models/views/guests.xml',        
        'models/views/rooms.xml',        
        'models/views/roomtypes.xml',   
        'models/views/charges.xml', 
    ],

    'installable': True,
    'application': True,
}