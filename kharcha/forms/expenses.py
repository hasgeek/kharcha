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
    ("INR", "INR - India, Rupees"),
    ("USD", "USD - United States of America, Dollars"),
    ("EUR", "EUR - Euro Member Countries, Euro"),
    ("GBP", "GBP - United Kingdom, Pounds"),
    ("",    "----"),
    ("AED", "AED - United Arab Emirates, Dirhams"),
    ("AFN", "AFN - Afghanistan, Afghanis"),
    ("ALL", "ALL - Albania, Leke"),
    ("AMD", "AMD - Armenia, Drams"),
    ("ANG", "ANG - Netherlands Antilles, Guilders (also called Florins)"),
    ("AOA", "AOA - Angola, Kwanza"),
    ("ARS", "ARS - Argentina, Pesos"),
    ("AUD", "AUD - Australia, Dollars"),
    ("AWG", "AWG - Aruba, Guilders (also called Florins)"),
    ("AZN", "AZN - Azerbaijan, New Manats"),
    ("BAM", "BAM - Bosnia and Herzegovina, Convertible Marka"),
    ("BBD", "BBD - Barbados, Dollars"),
    ("BDT", "BDT - Bangladesh, Taka"),
    ("BGN", "BGN - Bulgaria, Leva"),
    ("BHD", "BHD - Bahrain, Dinars"),
    ("BIF", "BIF - Burundi, Francs"),
    ("BMD", "BMD - Bermuda, Dollars"),
    ("BND", "BND - Brunei Darussalam, Dollars"),
    ("BOB", "BOB - Bolivia, Bolivianos"),
    ("BRL", "BRL - Brazil, Brazil Real"),
    ("BSD", "BSD - Bahamas, Dollars"),
    ("BTN", "BTN - Bhutan, Ngultrum"),
    ("BWP", "BWP - Botswana, Pulas"),
    ("BYR", "BYR - Belarus, Rubles"),
    ("BZD", "BZD - Belize, Dollars"),
    ("CAD", "CAD - Canada, Dollars"),
    ("CDF", "CDF - Congo/Kinshasa, Congolese Francs"),
    ("CHF", "CHF - Switzerland, Francs"),
    ("CLP", "CLP - Chile, Pesos"),
    ("CNY", "CNY - China, Yuan Renminbi"),
    ("COP", "COP - Colombia, Pesos"),
    ("CRC", "CRC - Costa Rica, Colones"),
    ("CUP", "CUP - Cuba, Pesos"),
    ("CVE", "CVE - Cape Verde, Escudos"),
    ("CYP", "CYP - Cyprus, Pounds (expires 2008-Jan-31)"),
    ("CZK", "CZK - Czech Republic, Koruny"),
    ("DJF", "DJF - Djibouti, Francs"),
    ("DKK", "DKK - Denmark, Kroner"),
    ("DOP", "DOP - Dominican Republic, Pesos"),
    ("DZD", "DZD - Algeria, Algeria Dinars"),
    ("EEK", "EEK - Estonia, Krooni"),
    ("EGP", "EGP - Egypt, Pounds"),
    ("ERN", "ERN - Eritrea, Nakfa"),
    ("ETB", "ETB - Ethiopia, Birr"),
    ("EUR", "EUR - Euro Member Countries, Euro"),
    ("FJD", "FJD - Fiji, Dollars"),
    ("FKP", "FKP - Falkland Islands (Malvinas), Pounds"),
    ("GBP", "GBP - United Kingdom, Pounds"),
    ("GEL", "GEL - Georgia, Lari"),
    ("GGP", "GGP - Guernsey, Pounds"),
    ("GHS", "GHS - Ghana, Cedis"),
    ("GIP", "GIP - Gibraltar, Pounds"),
    ("GMD", "GMD - Gambia, Dalasi"),
    ("GNF", "GNF - Guinea, Francs"),
    ("GTQ", "GTQ - Guatemala, Quetzales"),
    ("GYD", "GYD - Guyana, Dollars"),
    ("HKD", "HKD - Hong Kong, Dollars"),
    ("HNL", "HNL - Honduras, Lempiras"),
    ("HRK", "HRK - Croatia, Kuna"),
    ("HTG", "HTG - Haiti, Gourdes"),
    ("HUF", "HUF - Hungary, Forint"),
    ("IDR", "IDR - Indonesia, Rupiahs"),
    ("ILS", "ILS - Israel, New Shekels"),
    ("IMP", "IMP - Isle of Man, Pounds"),
    ("INR", "INR - India, Rupees"),
    ("IQD", "IQD - Iraq, Dinars"),
    ("IRR", "IRR - Iran, Rials"),
    ("ISK", "ISK - Iceland, Kronur"),
    ("JEP", "JEP - Jersey, Pounds"),
    ("JMD", "JMD - Jamaica, Dollars"),
    ("JOD", "JOD - Jordan, Dinars"),
    ("JPY", "JPY - Japan, Yen"),
    ("KES", "KES - Kenya, Shillings"),
    ("KGS", "KGS - Kyrgyzstan, Soms"),
    ("KHR", "KHR - Cambodia, Riels"),
    ("KMF", "KMF - Comoros, Francs"),
    ("KPW", "KPW - Korea (North), Won"),
    ("KRW", "KRW - Korea (South), Won"),
    ("KWD", "KWD - Kuwait, Dinars"),
    ("KYD", "KYD - Cayman Islands, Dollars"),
    ("KZT", "KZT - Kazakhstan, Tenge"),
    ("LAK", "LAK - Laos, Kips"),
    ("LBP", "LBP - Lebanon, Pounds"),
    ("LKR", "LKR - Sri Lanka, Rupees"),
    ("LRD", "LRD - Liberia, Dollars"),
    ("LSL", "LSL - Lesotho, Maloti"),
    ("LTL", "LTL - Lithuania, Litai"),
    ("LVL", "LVL - Latvia, Lati"),
    ("LYD", "LYD - Libya, Dinars"),
    ("MAD", "MAD - Morocco, Dirhams"),
    ("MDL", "MDL - Moldova, Lei"),
    ("MGA", "MGA - Madagascar, Ariary"),
    ("MKD", "MKD - Macedonia, Denars"),
    ("MMK", "MMK - Myanmar (Burma), Kyats"),
    ("MNT", "MNT - Mongolia, Tugriks"),
    ("MOP", "MOP - Macau, Patacas"),
    ("MRO", "MRO - Mauritania, Ouguiyas"),
    ("MTL", "MTL - Malta, Liri (expires 2008-Jan-31)"),
    ("MUR", "MUR - Mauritius, Rupees"),
    ("MVR", "MVR - Maldives (Maldive Islands), Rufiyaa"),
    ("MWK", "MWK - Malawi, Kwachas"),
    ("MXN", "MXN - Mexico, Pesos"),
    ("MYR", "MYR - Malaysia, Ringgits"),
    ("MZN", "MZN - Mozambique, Meticais"),
    ("NAD", "NAD - Namibia, Dollars"),
    ("NGN", "NGN - Nigeria, Nairas"),
    ("NIO", "NIO - Nicaragua, Cordobas"),
    ("NOK", "NOK - Norway, Krone"),
    ("NPR", "NPR - Nepal, Nepal Rupees"),
    ("NZD", "NZD - New Zealand, Dollars"),
    ("OMR", "OMR - Oman, Rials"),
    ("PAB", "PAB - Panama, Balboa"),
    ("PEN", "PEN - Peru, Nuevos Soles"),
    ("PGK", "PGK - Papua New Guinea, Kina"),
    ("PHP", "PHP - Philippines, Pesos"),
    ("PKR", "PKR - Pakistan, Rupees"),
    ("PLN", "PLN - Poland, Zlotych"),
    ("PYG", "PYG - Paraguay, Guarani"),
    ("QAR", "QAR - Qatar, Rials"),
    ("RON", "RON - Romania, New Lei"),
    ("RSD", "RSD - Serbia, Dinars"),
    ("RUB", "RUB - Russia, Rubles"),
    ("RWF", "RWF - Rwanda, Rwanda Francs"),
    ("SAR", "SAR - Saudi Arabia, Riyals"),
    ("SBD", "SBD - Solomon Islands, Dollars"),
    ("SCR", "SCR - Seychelles, Rupees"),
    ("SDG", "SDG - Sudan, Pounds"),
    ("SEK", "SEK - Sweden, Kronor"),
    ("SGD", "SGD - Singapore, Dollars"),
    ("SHP", "SHP - Saint Helena, Pounds"),
    ("SLL", "SLL - Sierra Leone, Leones"),
    ("SOS", "SOS - Somalia, Shillings"),
    ("SPL", "SPL - Seborga, Luigini"),
    ("SRD", "SRD - Suriname, Dollars"),
    ("STD", "STD - São Tome and Principe, Dobras"),
    ("SVC", "SVC - El Salvador, Colones"),
    ("SYP", "SYP - Syria, Pounds"),
    ("SZL", "SZL - Swaziland, Emalangeni"),
    ("THB", "THB - Thailand, Baht"),
    ("TJS", "TJS - Tajikistan, Somoni"),
    ("TMM", "TMM - Turkmenistan, Manats"),
    ("TND", "TND - Tunisia, Dinars"),
    ("TOP", "TOP - Tonga, Pa'anga"),
    ("TRY", "TRY - Turkey, New Lira"),
    ("TTD", "TTD - Trinidad and Tobago, Dollars"),
    ("TVD", "TVD - Tuvalu, Tuvalu Dollars"),
    ("TWD", "TWD - Taiwan, New Dollars"),
    ("TZS", "TZS - Tanzania, Shillings"),
    ("UAH", "UAH - Ukraine, Hryvnia"),
    ("UGX", "UGX - Uganda, Shillings"),
    ("USD", "USD - United States of America, Dollars"),
    ("UYU", "UYU - Uruguay, Pesos"),
    ("UZS", "UZS - Uzbekistan, Sums"),
    ("VEB", "VEB - Venezuela, Bolivares (expires 2008-Jun-30)"),
    ("VEF", "VEF - Venezuela, Bolivares Fuertes"),
    ("VND", "VND - Viet Nam, Dong"),
    ("VUV", "VUV - Vanuatu, Vatu"),
    ("WST", "WST - Samoa, Tala"),
    ("XAF", "XAF - Communauté Financière Africaine BEAC, Francs"),
    ("XCD", "XCD - East Caribbean Dollars"),
    ("XDR", "XDR - International Monetary Fund (IMF) Special Drawing Rights"),
    ("XOF", "XOF - Communauté Financière Africaine BCEAO, Francs"),
    ("XPF", "XPF - Comptoirs Français du Pacifique Francs"),
    ("YER", "YER - Yemen, Rials"),
    ("ZAR", "ZAR - South Africa, Rand"),
    ("ZMK", "ZMK - Zambia, Kwacha"),
    ("ZWD", "ZWD - Zimbabwe, Zimbabwe Dollars"),
    ]

CURRENCY_SYMBOLS = {
    'USD': '$',
    'CAD': '$',
    'AUD': '$',
    'SGD': '$',
    'INR': '₨',
    'EUR': '€',
    'GBP': '£',
    'PHP': '₱',
    'JPY': '¥',
    'THB': '฿',
    'KHR': '៛',
    'KRW': '₩',
    }


class BudgetForm(Form):
    """
    Create or edit a budget.
    """
    title = wtforms.TextField("Budget title", validators=[wtforms.validators.Required()],
        description="The name of your project or other budget source")
    description = RichTextField("Description",
        description="Description of the budget")

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
    title = wtforms.TextField("Title", validators=[wtforms.validators.Required()],
        description="The name of the category")

    def validate_title(self, field):
        """
        If the title is already in use, refuse to add this one.
        """
        existing = set([simplify_text(c.title) for c in
            Category.query.filter_by(workspace=g.workspace).all() if c != self.edit_obj])
        if simplify_text(field.data) in existing:
            raise wtforms.ValidationError("You have an existing category with the same name")


def sorted_budgets():
    return Budget.query.filter_by(workspace=g.workspace).order_by(Budget.title)


def sorted_categories():
    return Category.query.filter_by(workspace=g.workspace).order_by(Category.title)


class ExpenseReportForm(Form):
    """
    Create or edit an expense report.
    """
    title = wtforms.TextField("Title", validators=[wtforms.validators.Required()],
        description="What are these expenses for?")
    description = RichTextField("Description", validators=[wtforms.validators.Optional()],
        description="Notes on the expenses")
    currency = wtforms.SelectField("Currency", validators=[wtforms.validators.Required()],
        description="Currency for expenses in this report",
        choices=CURRENCIES)
    budget = QuerySelectField("Budget", validators=[wtforms.validators.Optional()],
        query_factory=sorted_budgets, get_label='title', allow_blank=True,
        description="The budget source for these expenses")


class ExpenseForm(Form):
    """
    Create or edit an expense line item.
    """
    id = wtforms.IntegerField("Id", validators=[wtforms.validators.Optional()])
    date = wtforms.DateField("Date", validators=[wtforms.validators.Required()])
    category = QuerySelectField("Category", validators=[wtforms.validators.Required()],
        query_factory=sorted_categories, get_label='title', allow_blank=True)
    description = wtforms.TextField("Description", validators=[wtforms.validators.Required()])
    amount = wtforms.DecimalField("Amount", validators=[wtforms.validators.Required(), wtforms.validators.NumberRange(min=0)])

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
    notes = RichTextField("Notes", validators=[wtforms.validators.Required()])
