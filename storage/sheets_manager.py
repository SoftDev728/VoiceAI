import os
from typing import Optional, List, Dict, Any
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from models import AppointmentData, AppointmentsResponse
from config import Config

class GoogleSheetsManager:
    """Manages Google Sheets operations for appointment storage"""
    
    def __init__(self):
        self.client: Optional[gspread.Client] = None
        self.worksheet: Optional[gspread.Worksheet] = None
        self.connected: bool = False
        self._initialize_connection()
    
    def _initialize_connection(self) -> None:
        """Initialize Google Sheets connection with proper error handling"""
        try:
            # Get the directory where this script is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            cred_path = os.path.join(current_dir, "..", Config.CREDENTIALS_FILE)
            
            # Check if credentials file exists
            if not os.path.exists(cred_path):
                print(f"❌ Credentials file not found at: {cred_path}")
                return
            
            # Load credentials and authorize client
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                cred_path, Config.GOOGLE_SCOPES
            )
            self.client = gspread.authorize(credentials)
            
            try:
                # Open the spreadsheet by URL
                spreadsheet = self.client.open_by_url(Config.GOOGLE_SHEETS_URL)
                self.worksheet = spreadsheet.sheet1
                self.connected = True
                
                print(f"✅ Connected to Google Sheet: {spreadsheet.title}")
                print(f"🔗 Sheet URL: {Config.GOOGLE_SHEETS_URL}")
                
                # Initialize headers if needed
                self._initialize_headers()
                
            except gspread.SpreadsheetNotFound:
                print(f"❌ Could not access spreadsheet at URL: {Config.GOOGLE_SHEETS_URL}")
                print("🔧 Please make sure the sheet is shared with your service account email")
            except Exception as sheet_error:
                print(f"❌ Error accessing spreadsheet: {sheet_error}")
                print("🔧 Please check if the sheet is shared with your service account email")
                
        except FileNotFoundError:
            print(f"❌ Credentials file not found: {cred_path}")
        except Exception as e:
            print(f"❌ Error initializing Google Sheets: {e}")
            print("🔧 Please check your credentials and internet connection")
    
    def _initialize_headers(self) -> None:
        """Initialize spreadsheet headers if needed"""
        if not self.worksheet:
            return
            
        try:
            first_row = self.worksheet.row_values(1)
            expected_headers = Config.APPOINTMENT_HEADERS
            
            if not first_row:
                # Sheet is empty, add headers
                print("📝 Adding headers to empty sheet...")
                self.worksheet.append_row(expected_headers)
                print("✅ Headers added to spreadsheet")
            elif first_row != expected_headers:
                # Headers exist but different, update them
                print("📝 Updating headers...")
                self.worksheet.delete_rows(1, 1)  # Delete first row
                self.worksheet.insert_row(expected_headers, 1)  # Insert new headers
                print("✅ Headers updated in spreadsheet")
            else:
                print("✅ Headers already present and correct")
                
        except Exception as header_error:
            print(f"⚠️ Could not check/add headers: {header_error}")
            print("📝 Attempting to add headers anyway...")
            try:
                self.worksheet.append_row(expected_headers)
                print("✅ Headers added")
            except:
                print("❌ Could not add headers, but sheet connection successful")
    
    def save_appointment(self, appointment_data: AppointmentData) -> bool:
        """Save appointment data to Google Sheets"""
        if not self.worksheet:
            print("⚠️ Google Sheets not available - skipping save")
            return False
            
        try:
            row = appointment_data.to_row()
            self.worksheet.append_row(row)
            print(f"✅ Appointment {appointment_data.appointment_id} saved to Google Sheets")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save to Google Sheets: {e}")
            return False
    
    def get_all_appointments(self) -> AppointmentsResponse:
        """Retrieve all appointments from Google Sheets"""
        if not self.worksheet:
            return AppointmentsResponse(
                success=False,
                message="Google Sheets not available",
                appointments=[],
                total_appointments=0,
                source="Google Sheets"
            )
        
        try:
            # Get all records from the sheet (excluding header)
            records = self.worksheet.get_all_records()
            
            return AppointmentsResponse(
                success=True,
                appointments=records,
                total_appointments=len(records),
                source="Google Sheets",
                google_sheets_connected=True
            )
            
        except Exception as e:
            return AppointmentsResponse(
                success=False,
                message=f"Error reading from Google Sheets: {str(e)}",
                appointments=[],
                total_appointments=0,
                source="Google Sheets"
            )
    
    def is_connected(self) -> bool:
        """Check if Google Sheets is connected"""
        return self.connected

# Global instance
sheets_manager = GoogleSheetsManager()