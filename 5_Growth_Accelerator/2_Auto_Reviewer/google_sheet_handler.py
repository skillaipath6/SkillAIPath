"""
Google Sheets Integration for PR Reviewer
Handles reading PR review requests from Google Sheets with optional GitHub tokens.
"""

import os
import json
import time
from typing import List, Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheetHandler:
    """
    Handles Google Sheets integration for PR review requests.
    
    Reads rows from a Google Sheet containing:
    - Column A: Timestamp
    - Column B: Email Address  
    - Column C: GitHub PR URL
    - Column D: GitHub Token (OPTIONAL)
    
    After successful processing, rows are deleted from the sheet.
    """
    
    def __init__(self):
        """Initialize Google Sheets API client using service account credentials."""
        # Get credentials from environment (injected by Databricks Apps)
        creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        
        if not creds_json:
            raise ValueError(
                "GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set. "
                "Please configure the secret in app.yaml."
            )
        
        try:
            # Parse JSON and create credentials
            creds_dict = json.loads(creds_json)
            self.credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
        except Exception as e:
            raise ValueError(f"Failed to create Google credentials: {e}")
        
        # Initialize Google Sheets API client
        try:
            self.service = build('sheets', 'v4', credentials=self.credentials)
        except Exception as e:
            raise ValueError(f"Failed to build Google Sheets service: {e}")
        
        # Get sheet ID from environment
        self.sheet_id = os.environ.get('GOOGLE_SHEET_ID')
        
        if not self.sheet_id:
            raise ValueError(
                "GOOGLE_SHEET_ID environment variable not set. "
                "Please configure it in app.yaml."
            )
        
        print(f"✅ Google Sheets handler initialized (Sheet ID: {self._mask_id(self.sheet_id)})")
    
    def _mask_id(self, sheet_id: str) -> str:
        """Mask sheet ID for logging (show first 8 chars only)."""
        if not sheet_id or len(sheet_id) < 8:
            return "[MASKED]"
        return f"{sheet_id[:8]}...[MASKED]"
    
    def _mask_token(self, token: Optional[str]) -> str:
        """Mask GitHub token for logging (show first 7 chars only)."""
        if not token or len(token) < 10:
            return "[NONE]"
        return f"{token[:7]}...[REDACTED]"
    
    def read_pending_reviews(self) -> List[Dict]:
        """
        Read all pending PR review requests from Google Sheet.
        
        Returns:
            List of dicts with keys: row_number, timestamp, email, pr_url, github_token
            
        Raises:
            HttpError: If Google Sheets API call fails
        """
        try:
            # Read all data rows (skip header row 1)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='Sheet1!A2:D'  # Columns A-D, starting from row 2
            ).execute()
            
            rows = result.get('values', [])
            
            if not rows:
                print("ℹ️ No pending review requests in Google Sheet")
                return []
            
            pending_reviews = []
            
            for i, row in enumerate(rows, start=2):  # Row 2 is first data row
                # Handle incomplete rows gracefully
                timestamp = row[0] if len(row) > 0 else ""
                email = row[1] if len(row) > 1 else ""
                pr_url = row[2] if len(row) > 2 else ""
                github_token = row[3] if len(row) > 3 else ""  # OPTIONAL
                
                # Strip whitespace
                pr_url = pr_url.strip() if pr_url else ""
                github_token = github_token.strip() if github_token else ""
                
                # Skip rows with empty PR URL
                if not pr_url:
                    print(f"⚠️ Row {i}: Skipping - no PR URL")
                    continue
                
                # GitHub token is OPTIONAL - empty is valid
                pending_reviews.append({
                    'row_number': i,
                    'timestamp': timestamp,
                    'email': email,
                    'pr_url': pr_url,
                    'github_token': github_token if github_token else None
                })
                
                # Log without exposing tokens
                token_status = "with token" if github_token else "no token"
                print(f"📋 Row {i}: {pr_url} ({token_status})")
            
            print(f"✅ Found {len(pending_reviews)} pending review(s)")
            return pending_reviews
            
        except HttpError as e:
            error_msg = str(e)
            # Don't expose credentials in error messages
            if 'credentials' in error_msg.lower():
                raise HttpError(
                    e.resp, 
                    b"Google Sheets API authentication failed. Check service account permissions."
                )
            raise
        except Exception as e:
            print(f"❌ Error reading Google Sheet: {e}")
            raise
    
    def delete_review_row(self, row_number: int) -> bool:
        """
        Delete a row from the sheet (GDPR compliance - immediate deletion after processing).
        
        Args:
            row_number: Row number to delete (1-indexed, matching Google Sheets UI)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Sheets API uses 0-indexed rows
            start_index = row_number - 1
            end_index = row_number
            
            request = {
                'deleteDimension': {
                    'range': {
                        'sheetId': 0,  # First sheet (Sheet1)
                        'dimension': 'ROWS',
                        'startIndex': start_index,
                        'endIndex': end_index
                    }
                }
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body={'requests': [request]}
            ).execute()
            
            print(f"✅ Deleted row {row_number} from Google Sheet (token removed)")
            return True
            
        except HttpError as e:
            print(f"❌ Google Sheets API error deleting row {row_number}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error deleting row {row_number}: {e}")
            return False
    
    def validate_pr_url(self, pr_url: str) -> bool:
        """
        Basic validation of PR URL format.
        
        Args:
            pr_url: GitHub PR URL to validate
            
        Returns:
            True if URL looks like a valid GitHub PR URL
        """
        if not pr_url:
            return False
        
        # Must contain github.com and /pull/
        return 'github.com' in pr_url and '/pull/' in pr_url


# Singleton instance (initialized once when module is imported)
_sheet_handler: Optional[GoogleSheetHandler] = None


def get_sheet_handler() -> GoogleSheetHandler:
    """
    Get or create the Google Sheets handler singleton.
    
    Returns:
        Initialized GoogleSheetHandler instance
        
    Raises:
        ValueError: If Google Sheets credentials are not configured
    """
    global _sheet_handler
    
    if _sheet_handler is None:
        _sheet_handler = GoogleSheetHandler()
    
    return _sheet_handler


def test_connection() -> bool:
    """
    Test Google Sheets connection and permissions.
    
    Returns:
        True if connection works, False otherwise
    """
    try:
        handler = get_sheet_handler()
        # Try to read (doesn't matter if empty)
        handler.read_pending_reviews()
        print("✅ Google Sheets connection test: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ Google Sheets connection test: FAILED - {e}")
        return False


if __name__ == "__main__":
    # Test connection when run directly
    print("Testing Google Sheets connection...\n")
    success = test_connection()
    exit(0 if success else 1)
