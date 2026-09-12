from app.parsers.base import BaseParser
from app.parsers.registry import register, get_parser, detect_parser, all_parsers

# Import all parser modules to trigger @register decorators
from app.parsers import sbi_bank
from app.parsers import sbi_cashback
from app.parsers import icici_amazon
from app.parsers import yes_bank
from app.parsers import au_zenith
from app.parsers import amex
from app.parsers import hdfc_swiggy
from app.parsers import hsbc
from app.parsers import idfc_first
from app.parsers import indusind
from app.parsers import generic
