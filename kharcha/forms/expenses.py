# -*- coding: utf-8 -*-

# Expense forms
from decimal import Decimal
from flask import g
import wtforms
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from baseframe.forms import Form, RichTextField
from coaster.utils import simplify_text
from kharcha.models import Category, Budget, Expense

__all__ = ['BudgetForm', 'CategoryForm', 'ExpenseReportForm', 'ExpenseForm', 'WorkflowForm', 'ReviewForm']

CURRENCIES = [
    (u"INR", u"INR - India, Rupees"),
    (u"USD", u"USD - United States of America, Dollars"),
    (u"EUR", u"EUR - Euro Member Countries, Euro"),
    (u"GBP", u"GBP - United Kingdom, Pounds"),
    (u"",    u"----"),
    (u"AED", u"AED - United Arab Emirates, Dirhams"),
    (u"AFN", u"AFN - Afghanistan, Afghanis"),
    (u"ALL", u"ALL - Albania, Leke"),
    (u"AMD", u"AMD - Armenia, Drams"),
    (u"ANG", u"ANG - Netherlands Antilles, Guilders (also called Florins)"),
    (u"AOA", u"AOA - Angola, Kwanza"),
    (u"ARS", u"ARS - Argentina, Pesos"),
    (u"AUD", u"AUD - Australia, Dollars"),
    (u"AWG", u"AWG - Aruba, Guilders (also called Florins)"),
    (u"AZN", u"AZN - Azerbaijan, New Manats"),
    (u"BAM", u"BAM - Bosnia and Herzegovina, Convertible Marka"),
    (u"BBD", u"BBD - Barbados, Dollars"),
    (u"BDT", u"BDT - Bangladesh, Taka"),
    (u"BGN", u"BGN - Bulgaria, Leva"),
    (u"BHD", u"BHD - Bahrain, Dinars"),
    (u"BIF", u"BIF - Burundi, Francs"),
    (u"BMD", u"BMD - Bermuda, Dollars"),
    (u"BND", u"BND - Brunei Darussalam, Dollars"),
    (u"BOB", u"BOB - Bolivia, Bolivianos"),
    (u"BRL", u"BRL - Brazil, Brazil Real"),
    (u"BSD", u"BSD - Bahamas, Dollars"),
    (u"BTN", u"BTN - Bhutan, Ngultrum"),
    (u"BWP", u"BWP - Botswana, Pulas"),
    (u"BYR", u"BYR - Belarus, Rubles"),
    (u"BZD", u"BZD - Belize, Dollars"),
    (u"CAD", u"CAD - Canada, Dollars"),
    (u"CDF", u"CDF - Congo/Kinshasa, Congolese Francs"),
    (u"CHF", u"CHF - Switzerland, Francs"),
    (u"CLP", u"CLP - Chile, Pesos"),
    (u"CNY", u"CNY - China, Yuan Renminbi"),
    (u"COP", u"COP - Colombia, Pesos"),
    (u"CRC", u"CRC - Costa Rica, Colones"),
    (u"CUP", u"CUP - Cuba, Pesos"),
    (u"CVE", u"CVE - Cape Verde, Escudos"),
    (u"CYP", u"CYP - Cyprus, Pounds (expires 2008-Jan-31)"),
    (u"CZK", u"CZK - Czech Republic, Koruny"),
    (u"DJF", u"DJF - Djibouti, Francs"),
    (u"DKK", u"DKK - Denmark, Kroner"),
    (u"DOP", u"DOP - Dominican Republic, Pesos"),
    (u"DZD", u"DZD - Algeria, Algeria Dinars"),
    (u"EEK", u"EEK - Estonia, Krooni"),
    (u"EGP", u"EGP - Egypt, Pounds"),
    (u"ERN", u"ERN - Eritrea, Nakfa"),
    (u"ETB", u"ETB - Ethiopia, Birr"),
    (u"EUR", u"EUR - Euro Member Countries, Euro"),
    (u"FJD", u"FJD - Fiji, Dollars"),
    (u"FKP", u"FKP - Falkland Islands (Malvinas), Pounds"),
    (u"GBP", u"GBP - United Kingdom, Pounds"),
    (u"GEL", u"GEL - Georgia, Lari"),
    (u"GGP", u"GGP - Guernsey, Pounds"),
    (u"GHS", u"GHS - Ghana, Cedis"),
    (u"GIP", u"GIP - Gibraltar, Pounds"),
    (u"GMD", u"GMD - Gambia, Dalasi"),
    (u"GNF", u"GNF - Guinea, Francs"),
    (u"GTQ", u"GTQ - Guatemala, Quetzales"),
    (u"GYD", u"GYD - Guyana, Dollars"),
    (u"HKD", u"HKD - Hong Kong, Dollars"),
    (u"HNL", u"HNL - Honduras, Lempiras"),
    (u"HRK", u"HRK - Croatia, Kuna"),
    (u"HTG", u"HTG - Haiti, Gourdes"),
    (u"HUF", u"HUF - Hungary, Forint"),
    (u"IDR", u"IDR - Indonesia, Rupiahs"),
    (u"ILS", u"ILS - Israel, New Shekels"),
    (u"IMP", u"IMP - Isle of Man, Pounds"),
    (u"INR", u"INR - India, Rupees"),
    (u"IQD", u"IQD - Iraq, Dinars"),
    (u"IRR", u"IRR - Iran, Rials"),
    (u"ISK", u"ISK - Iceland, Kronur"),
    (u"JEP", u"JEP - Jersey, Pounds"),
    (u"JMD", u"JMD - Jamaica, Dollars"),
    (u"JOD", u"JOD - Jordan, Dinars"),
    (u"JPY", u"JPY - Japan, Yen"),
    (u"KES", u"KES - Kenya, Shillings"),
    (u"KGS", u"KGS - Kyrgyzstan, Soms"),
    (u"KHR", u"KHR - Cambodia, Riels"),
    (u"KMF", u"KMF - Comoros, Francs"),
    (u"KPW", u"KPW - Korea (North), Won"),
    (u"KRW", u"KRW - Korea (South), Won"),
    (u"KWD", u"KWD - Kuwait, Dinars"),
    (u"KYD", u"KYD - Cayman Islands, Dollars"),
    (u"KZT", u"KZT - Kazakhstan, Tenge"),
    (u"LAK", u"LAK - Laos, Kips"),
    (u"LBP", u"LBP - Lebanon, Pounds"),
    (u"LKR", u"LKR - Sri Lanka, Rupees"),
    (u"LRD", u"LRD - Liberia, Dollars"),
    (u"LSL", u"LSL - Lesotho, Maloti"),
    (u"LTL", u"LTL - Lithuania, Litai"),
    (u"LVL", u"LVL - Latvia, Lati"),
    (u"LYD", u"LYD - Libya, Dinars"),
    (u"MAD", u"MAD - Morocco, Dirhams"),
    (u"MDL", u"MDL - Moldova, Lei"),
    (u"MGA", u"MGA - Madagascar, Ariary"),
    (u"MKD", u"MKD - Macedonia, Denars"),
    (u"MMK", u"MMK - Myanmar (Burma), Kyats"),
    (u"MNT", u"MNT - Mongolia, Tugriks"),
    (u"MOP", u"MOP - Macau, Patacas"),
    (u"MRO", u"MRO - Mauritania, Ouguiyas"),
    (u"MTL", u"MTL - Malta, Liri (expires 2008-Jan-31)"),
    (u"MUR", u"MUR - Mauritius, Rupees"),
    (u"MVR", u"MVR - Maldives (Maldive Islands), Rufiyaa"),
    (u"MWK", u"MWK - Malawi, Kwachas"),
    (u"MXN", u"MXN - Mexico, Pesos"),
    (u"MYR", u"MYR - Malaysia, Ringgits"),
    (u"MZN", u"MZN - Mozambique, Meticais"),
    (u"NAD", u"NAD - Namibia, Dollars"),
    (u"NGN", u"NGN - Nigeria, Nairas"),
    (u"NIO", u"NIO - Nicaragua, Cordobas"),
    (u"NOK", u"NOK - Norway, Krone"),
    (u"NPR", u"NPR - Nepal, Nepal Rupees"),
    (u"NZD", u"NZD - New Zealand, Dollars"),
    (u"OMR", u"OMR - Oman, Rials"),
    (u"PAB", u"PAB - Panama, Balboa"),
    (u"PEN", u"PEN - Peru, Nuevos Soles"),
    (u"PGK", u"PGK - Papua New Guinea, Kina"),
    (u"PHP", u"PHP - Philippines, Pesos"),
    (u"PKR", u"PKR - Pakistan, Rupees"),
    (u"PLN", u"PLN - Poland, Zlotych"),
    (u"PYG", u"PYG - Paraguay, Guarani"),
    (u"QAR", u"QAR - Qatar, Rials"),
    (u"RON", u"RON - Romania, New Lei"),
    (u"RSD", u"RSD - Serbia, Dinars"),
    (u"RUB", u"RUB - Russia, Rubles"),
    (u"RWF", u"RWF - Rwanda, Rwanda Francs"),
    (u"SAR", u"SAR - Saudi Arabia, Riyals"),
    (u"SBD", u"SBD - Solomon Islands, Dollars"),
    (u"SCR", u"SCR - Seychelles, Rupees"),
    (u"SDG", u"SDG - Sudan, Pounds"),
    (u"SEK", u"SEK - Sweden, Kronor"),
    (u"SGD", u"SGD - Singapore, Dollars"),
    (u"SHP", u"SHP - Saint Helena, Pounds"),
    (u"SLL", u"SLL - Sierra Leone, Leones"),
    (u"SOS", u"SOS - Somalia, Shillings"),
    (u"SPL", u"SPL - Seborga, Luigini"),
    (u"SRD", u"SRD - Suriname, Dollars"),
    (u"STD", u"STD - São Tome and Principe, Dobras"),
    (u"SVC", u"SVC - El Salvador, Colones"),
    (u"SYP", u"SYP - Syria, Pounds"),
    (u"SZL", u"SZL - Swaziland, Emalangeni"),
    (u"THB", u"THB - Thailand, Baht"),
    (u"TJS", u"TJS - Tajikistan, Somoni"),
    (u"TMM", u"TMM - Turkmenistan, Manats"),
    (u"TND", u"TND - Tunisia, Dinars"),
    (u"TOP", u"TOP - Tonga, Pa'anga"),
    (u"TRY", u"TRY - Turkey, New Lira"),
    (u"TTD", u"TTD - Trinidad and Tobago, Dollars"),
    (u"TVD", u"TVD - Tuvalu, Tuvalu Dollars"),
    (u"TWD", u"TWD - Taiwan, New Dollars"),
    (u"TZS", u"TZS - Tanzania, Shillings"),
    (u"UAH", u"UAH - Ukraine, Hryvnia"),
    (u"UGX", u"UGX - Uganda, Shillings"),
    (u"USD", u"USD - United States of America, Dollars"),
    (u"UYU", u"UYU - Uruguay, Pesos"),
    (u"UZS", u"UZS - Uzbekistan, Sums"),
    (u"VEB", u"VEB - Venezuela, Bolivares (expires 2008-Jun-30)"),
    (u"VEF", u"VEF - Venezuela, Bolivares Fuertes"),
    (u"VND", u"VND - Viet Nam, Dong"),
    (u"VUV", u"VUV - Vanuatu, Vatu"),
    (u"WST", u"WST - Samoa, Tala"),
    (u"XAF", u"XAF - Communauté Financière Africaine BEAC, Francs"),
    (u"XCD", u"XCD - East Caribbean Dollars"),
    (u"XDR", u"XDR - International Monetary Fund (IMF) Special Drawing Rights"),
    (u"XOF", u"XOF - Communauté Financière Africaine BCEAO, Francs"),
    (u"XPF", u"XPF - Comptoirs Français du Pacifique Francs"),
    (u"YER", u"YER - Yemen, Rials"),
    (u"ZAR", u"ZAR - South Africa, Rand"),
    (u"ZMK", u"ZMK - Zambia, Kwacha"),
    (u"ZWD", u"ZWD - Zimbabwe, Zimbabwe Dollars"),
    ]

CURRENCY_SYMBOLS = {
    u'USD': u'$',
    u'CAD': u'$',
    u'AUD': u'$',
    u'SGD': u'$',
    u'INR': u'₨',
    u'EUR': u'€',
    u'GBP': u'£',
    u'PHP': u'₱',
    u'JPY': u'¥',
    u'THB': u'฿',
    u'KHR': u'៛',
    u'KRW': u'₩',
    }


class BudgetForm(Form):
    """
    Create or edit a budget.
    """
    title = wtforms.TextField(u"Budget title", validators=[wtforms.validators.Required()],
        description=u"The name of your project or other budget source")
    description = RichTextField(u"Description",
        description=u"Description of the budget")

    def validate_title(self, field):
        """
        If the title is already in use, refuse to add this one.
        """
        existing = set([simplify_text(b.title) for b in
            Budget.query.filter_by(workspace=g.workspace).all() if b != self.edit_obj])
        if simplify_text(field.data) in existing:
            raise wtforms.ValidationError("You have an existing budget with the same name")


class CategoryForm(Form):
    """
    Create or edit a category.
    """
    title = wtforms.TextField(u"Title", validators=[wtforms.validators.Required()],
        description=u"The name of the category")

    def validate_title(self, field):
        """
        If the title is already in use, refuse to add this one.
        """
        existing = set([simplify_text(c.title) for c in
            Category.query.filter_by(workspace=g.workspace).all() if c != self.edit_obj])
        if simplify_text(field.data) in existing:
            raise wtforms.ValidationError("You have an existing category with the same name")


def sorted_budgets():
    return Budget.query.filter_by(workspace=g.workspace).order_by('title')


def sorted_categories():
    return Category.query.filter_by(workspace=g.workspace).order_by('title')


class ExpenseReportForm(Form):
    """
    Create or edit an expense report.
    """
    title = wtforms.TextField(u"Title", validators=[wtforms.validators.Required()],
        description=u"What are these expenses for?")
    description = RichTextField(u"Description", validators=[wtforms.validators.Optional()],
        description=u"Notes on the expenses")
    currency = wtforms.SelectField(u"Currency", validators=[wtforms.validators.Required()],
        description=u"Currency for expenses in this report",
        choices=CURRENCIES)
    budget = QuerySelectField(u"Budget", validators=[wtforms.validators.Optional()],
        query_factory=sorted_budgets, get_label='title', allow_blank=True,
        description=u"The budget source for these expenses")


class ExpenseForm(Form):
    """
    Create or edit an expense line item.
    """
    id = wtforms.IntegerField(u"Id", validators=[wtforms.validators.Optional()])
    date = wtforms.DateField(u"Date", validators=[wtforms.validators.Required()])
    category = QuerySelectField(u"Category", validators=[wtforms.validators.Required()],
        query_factory=sorted_categories, get_label='title', allow_blank=True)
    description = wtforms.TextField(u"Description", validators=[wtforms.validators.Required()])
    amount = wtforms.DecimalField(u"Amount", validators=[wtforms.validators.Required(), wtforms.validators.NumberRange(min=0)])

    def validate_id(self, field):
        # Check if user is authorized to edit this expense.
        if field.data:
            expense = Expense.query.get(field.data)
            if not expense:
                raise wtforms.ValidationError("Unknown expense")
            if expense.report.user != g.user:
                raise wtforms.ValidationError("You are not authorized to edit this expense")

    def validate_amount(self, field):
        if field.data < Decimal('0.01'):
            raise wtforms.ValidationError("Amount should be non-zero")


class WorkflowForm(Form):
    """
    Blank form for CSRF in workflow submissions.
    """
    pass


class ReviewForm(Form):
    """
    Reviewer notes on expense reports.
    """
    notes = RichTextField(u"Notes", validators=[wtforms.validators.Required()])
