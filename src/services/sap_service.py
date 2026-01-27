
import json
import requests
import datetime
from fastapi import HTTPException
from src.core.config import get_settings

class SapService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.SAP_SL_URL
        self.session_id = None
        self.route_id = None
        self.verify_ssl = self.settings.SAP_VERIFY_SSL

    def _get_headers(self):
        headers = {'Content-Type': 'application/json'}
        cookies = {}
        if self.session_id:
            cookies['B1SESSION'] = self.session_id
        if self.route_id:
            cookies['ROUTEID'] = self.route_id
        
        cookie_string = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        if cookie_string:
            headers['Cookie'] = cookie_string
            
        return headers

    def login(self):
        url = f"{self.base_url}/Login"
        payload = {
            "CompanyDB": self.settings.SAP_DB,
            "UserName": self.settings.SAP_USER,
            "Password": self.settings.SAP_PASSWORD
        }
        
        try:
            print(f"SAP LOGIN Attempt: {self.base_url} (DB: {self.settings.SAP_DB})")
            response = requests.post(url, json=payload, verify=self.verify_ssl, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            self.session_id = data.get('SessionId')
            
            # RouteID is often in cookies for Load Balancer affinity
            if 'ROUTEID' in response.cookies:
                self.route_id = response.cookies['ROUTEID']
                
            print("SAP LOGIN Success")
            return True
        except Exception as e:
            print(f"SAP LOGIN Error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"SAP Response: {e.response.text}")
            raise HTTPException(status_code=500, detail=f"SAP Login Failed: {str(e)}")

    def logout(self):
        if not self.session_id:
            return
            
        url = f"{self.base_url}/Logout"
        try:
            requests.post(url, headers=self._get_headers(), verify=self.verify_ssl)
            self.session_id = None
            self.route_id = None
        except:
            pass

    def create_order(self, order_payload):
        """
        Creates a Sales Order (Note) in SAP via Service Layer.
        Auto-logins if session is missing.
        """
        if not self.session_id:
            self.login()
            
        url = f"{self.base_url}/Orders"
        
        try:
            print("Creating SAP Order...")
            response = requests.post(url, json=order_payload, headers=self._get_headers(), verify=self.verify_ssl, timeout=30)
            
            # If session expired, retry once
            if response.status_code == 401:
                print("SAP Session expired. Re-logging...")
                self.login()
                response = requests.post(url, json=order_payload, headers=self._get_headers(), verify=self.verify_ssl, timeout=30)
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_detail = "SAP Error"
            try:
                error_json = e.response.json()
                error_detail = json.dumps(error_json)
                print(f"SAP API Error: {error_detail}")
            except:
                print(f"SAP Raw Error: {e.response.text}")
                error_detail = e.response.text
                
            raise HTTPException(status_code=400, detail=f"SAP Creation Failed: {error_detail}")
        except Exception as e:
            print(f"Unexpected SAP Error: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")

# Singleton instance to reuse session across requests (simple version)
# In production, consider request-scoped or better session management.
_sap_service_instance = None

def get_sap_service():
    global _sap_service_instance
    if _sap_service_instance is None:
        _sap_service_instance = SapService()
    return _sap_service_instance
