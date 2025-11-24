import gspread
import pandas as pd
import os
from config import Config
from logger import logger

def upload_excel_to_sheet(excel_path: str, tab_name: str = None) -> bool:
    """
    Uploads the content of an Excel file to a Google Sheet.
    
    Args:
        excel_path (str): Path to the Excel file.
        tab_name (str, optional): Name of the sheet tab to upload to. Defaults to Config.GOOGLE_SHEET_TAB.
    """
    try:
        logger.info('📊 Starting Google Sheets Upload...')

        if not os.path.exists(excel_path):
            logger.error(f'❌ Excel file not found: {excel_path}')
            return False

        if not Config.GOOGLE_SHEET_URL:
            logger.warning('⚠️ GOOGLE_SHEET_URL is not set. Skipping upload.')
            return False

        if not os.path.exists(Config.GOOGLE_CREDENTIALS_PATH):
            logger.warning(f'⚠️ Google Credentials file not found at: {Config.GOOGLE_CREDENTIALS_PATH}. Skipping upload.')
            return False

        # 1. Read Excel
        logger.debug(f'Reading Excel file: {excel_path}')
        df = None
        try:
            # Try reading as standard Excel (xlsx/xls)
            # engine='openpyxl' for xlsx, 'xlrd' for xls
            if excel_path.endswith('.xlsx'):
                df = pd.read_excel(excel_path, engine='openpyxl')
            else:
                # For .xls, try xlrd first
                try:
                    df = pd.read_excel(excel_path, engine='xlrd')
                except Exception:
                    # If xlrd fails, it might be an HTML file with .xls extension (common in ERPs)
                    logger.warning('⚠️ Failed to read as standard XLS. Trying as HTML...')
                    dfs = pd.read_html(excel_path)
                    if dfs:
                        df = dfs[0]  # Assume first table is the data
                    else:
                        raise ValueError('No tables found in HTML-based Excel file')

            if df is None:
                raise ValueError('DataFrame is empty after reading')

            # Convert all data to string to avoid JSON serialization issues with dates/NaNs
            df = df.astype(str)
            # Replace 'nan' strings with empty string
            df = df.replace('nan', '')
        except Exception as read_error:
            logger.error(f'❌ Failed to read Excel file: {str(read_error)}')
            return False

        # 2. Authenticate and Open Sheet
        logger.debug('Authenticating with Google...')
        try:
            gc = gspread.service_account(filename=Config.GOOGLE_CREDENTIALS_PATH)
            sh = gc.open_by_url(Config.GOOGLE_SHEET_URL)
            
            target_tab = tab_name if tab_name else Config.GOOGLE_SHEET_TAB
            logger.info(f'📑 Selecting Worksheet: {target_tab}')
            
            try:
                worksheet = sh.worksheet(target_tab)
            except gspread.WorksheetNotFound:
                logger.warning(f'⚠️ Worksheet "{target_tab}" not found. Creating it...')
                worksheet = sh.add_worksheet(title=target_tab, rows=1000, cols=26)
                
        except Exception as auth_error:
            logger.error(f'❌ Google Authentication/Sheet Open Failed: {str(auth_error)}')
            return False

        # 3. Update Sheet
        logger.info(f'📤 Uploading {len(df)} rows to Google Sheets...')
        
        # Clear existing content
        worksheet.clear()
        
        # Update with new data (headers + values)
        data = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.update(range_name='A1', values=data)
        
        logger.info('✅ Google Sheets Upload Completed Successfully!')
        return True

    except Exception as error:
        logger.error(f'❌ upload_excel_to_sheet failed: {str(error)}')
        return False
