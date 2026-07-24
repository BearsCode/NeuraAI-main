from backend.app.integrations.retail.base import RetailAdapter, RetailAdapterRegistry
from backend.app.integrations.retail.c1 import C1CommerceMLAdapter
from backend.app.integrations.retail.moysklad import MoyskladRestAdapter
from backend.app.integrations.retail.amocrm import AmoCRMAdapter
from backend.app.integrations.retail.bitrix24 import Bitrix24Adapter
from backend.app.integrations.retail.google_sheets import GoogleSheetsAdapter
from backend.app.integrations.retail.csv_adapter import CSVRetailAdapter

__all__ = [
    "RetailAdapter", "RetailAdapterRegistry",
    "C1CommerceMLAdapter", "MoyskladRestAdapter",
    "AmoCRMAdapter", "Bitrix24Adapter",
    "GoogleSheetsAdapter", "CSVRetailAdapter",
]
