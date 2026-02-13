"""
Google Sheets Integration Module
Automatically syncs leads to Google Sheets in real-time.
"""

import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
from google import auth 

# Scopes required for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
FIELDNAMES = [
    "First Name","Last Name","Title","Email","LinkedIn URL","Company",
    "Company Info","Qualification Grade","Why Good?","Pain_Point",
    "Icebreaker","Status","Recent updates","Keyword",
    "Employee Count","Annual Revenue","Company Size","Industry Tags",
    "Social Media","Contact Details","Logistics Signals","Brand Vibe",
    "Tech Stack","Product Profile","Customer Focus","Shipping Locations",
    "Timestamp"
]
class SheetsSync:
    def __init__(self, spreadsheet_id, credentials):
        """
        Initialize Google Sheets sync using a credentials object directly.
        """
        self.spreadsheet_id = spreadsheet_id
        self.service = None
        
        try:
            # We use the creds object directly now, not a path
            self.service = build('sheets', 'v4', credentials=credentials)
            logging.info(f"✅ Google Sheets API initialized for sheet: {spreadsheet_id}")
        except Exception as e:
            logging.error(f"Failed to initialize Google Sheets API: {e}")
            raise
    
    def init_sheet_headers(self, sheet_name='Sheet1'):
        try:
            headers = FIELDNAMES
            range_name = f"{sheet_name}!A1:AA1"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values or values[0] != headers:
                body = {'values': [headers]}
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{sheet_name}!A1",
                    valueInputOption='RAW',
                    body=body
                ).execute()
                logging.info(f"✅ Initialized headers in sheet: {sheet_name}")
        except HttpError as e:
            logging.error(f"Failed to initialize headers: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error initializing headers: {e}")
            raise
    
    def sync_lead(self, lead_data, sheet_name='Sheet1'):
        """
        Sync a single lead to Google Sheets.
        Appends as new row.
        
        Args:
            lead_data: Dictionary with lead information
            sheet_name: Name of the sheet tab
        
        Returns:
            Row number where lead was added, or None if failed
        """
        try:
            from datetime import datetime
            
            # Internal helper to ensure clean text formatting
            def clean_val(v):
                return "" if v is None else str(v).strip()

            lead_data = dict(lead_data)

            if not lead_data.get("Timestamp"):
                from datetime import datetime
                lead_data["Timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            row = [clean_val(lead_data.get(col)) for col in FIELDNAMES]
            
            # Append to sheet (rest of the logic remains the same)
            body = {'values': [row]}
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:AA",
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logging.info(f" Synced lead to Google Sheets: {lead_data.get('Company', 'Unknown')}")
            return result.get('updates', {}).get('updatedRange', '')
            
        except HttpError as e:
            if e.resp.status == 429:
                # Rate limit - retry with backoff
                logging.warning("Google Sheets rate limit hit, retrying in 2 seconds...")
                time.sleep(2)
                return self.sync_lead(lead_data, sheet_name)  # Retry once
            else:
                logging.error(f"Failed to sync lead to Sheets: {e}")
                return None
        except Exception as e:
            logging.error(f"Unexpected error syncing to Sheets: {e}")
            return None
    
    def batch_sync_leads(self, leads_list, sheet_name='Sheet1'):
        """
        Sync multiple leads at once (more efficient).
        
        Args:
            leads_list: List of lead dictionaries
            sheet_name: Name of the sheet tab
        
        Returns:
            Number of leads successfully synced
        """
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Prepare rows
            rows = []
            for lead_data in leads_list:
                if not lead_data.get("Timestamp"):
                    lead_data["Timestamp"] = timestamp
                rows.append([lead_data.get(col,"") for col in FIELDNAMES])
            
            # Batch append
            body = {'values': rows}
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:AA",
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logging.info(f"✅ Batch synced {len(rows)} leads to Google Sheets")
            return len(rows)
            
        except Exception as e:
            logging.error(f"Failed to batch sync leads: {e}")
            return 0


# Global sheets sync instance
_sheets_sync_instance = None

def get_sheets_sync():
    global _sheets_sync_instance
    if _sheets_sync_instance is None:
        from .config import GOOGLE_SHEET_ID, GOOGLE_APPLICATION_CREDENTIALS, ENABLE_SHEETS_SYNC
        
        if not ENABLE_SHEETS_SYNC:
            logging.info("Sheets sync is disabled in config.")
            return None
        
        try:
            # Check for local file, but DON'T exit if it's missing
            if GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
                creds = service_account.Credentials.from_service_account_file(
                    GOOGLE_APPLICATION_CREDENTIALS, scopes=SCOPES)
                logging.info("Using Local JSON Credentials")
            else:
                # This is what Cloud Run uses!
                creds, project = auth.default(scopes=SCOPES)
                logging.info("Using Cloud Run Default Identity")

            _sheets_sync_instance = SheetsSync(
                spreadsheet_id=GOOGLE_SHEET_ID,
                credentials=creds
            )
            _sheets_sync_instance.init_sheet_headers()
        except Exception as e:
            logging.error(f"Failed to initialize Sheets sync: {e}")
            return None
    
    return _sheets_sync_instance
    
def sync_lead_to_sheet(lead_data):
    """
    Convenience function to sync a lead to Google Sheets.
    Safe to call even if Sheets sync is disabled.
    
    Args:
        lead_data: Dictionary with lead information
    """
    sheets = get_sheets_sync()
    if sheets:
        return sheets.sync_lead(lead_data)
    return None

def sync_enriched_lead_to_sheet(lead_data):
    """
    Writes enrichment output to Enrichment tab
    """
    sheets = get_sheets_sync()
    if sheets:
        sheets.init_sheet_headers(sheet_name="Enrichment")
        return sheets.sync_lead(lead_data, sheet_name="Enrichment")
    return None

def get_enrichment_sheet_rows(sheet_name="Enrichment"):
    sheets = get_sheets_sync()
    if not sheets:
        return []

    try:
        result = sheets.service.spreadsheets().values().get(
            spreadsheetId=sheets.spreadsheet_id,
            range=f"{sheet_name}!A:AA"
        ).execute()

        values = result.get("values", [])
        if not values:
            return []

        headers = values[0]
        rows = []

        for r in values[1:]:
            rows.append(dict(zip(headers, r)))

        return rows

    except Exception as e:
        logging.error(f"Failed reading enrichment sheet rows: {e}")
        return []