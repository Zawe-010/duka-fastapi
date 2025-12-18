# mpesa.py
import requests, base64
from requests.auth import HTTPBasicAuth
from datetime import datetime

# --- Sandbox Credentials ---
consumer_key = "tnWQLSS6IbyOlP7P91eEaQBe7WVD0Dn96DApWvjc8o3gUcJ0"
consumer_secret = "lC2bNrK0sna60sGn5eKNHEJQhyuLGbDtqZ4NdAv2GgvnDdZIXxTGvAA7mqGaPLAE"
short_code = "174379"
pass_key = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"

# --- API Endpoints ---
token_api = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
push_api = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
stk_push_query_api = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"
callback_url = "https://api.my-duka.co.ke/mpesa/callback"

# --- Get Access Token ---
def get_mpesa_access_token():
    try:
        res = requests.get(token_api, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        res.raise_for_status()
        token = res.json().get("access_token")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        print("✅ Access token retrieved:", token)
        return headers
    except Exception as e:
        print("❌ Error getting access token:", str(e))
        raise e

# --- Generate STK Push Password ---
def generate_password():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password_str = short_code + pass_key + timestamp
    return base64.b64encode(password_str.encode()).decode("utf-8")

# --- Send STK Push ---
def send_stk_push(amount: float, phone_number: str, sale_id: str):
    headers = get_mpesa_access_token()
    payload = {
        "BusinessShortCode": short_code,
        "Password": generate_password(),
        "Timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": short_code,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": str(sale_id),
        "TransactionDesc": "FastAPI Payment"
    }

    try:
        print("🔥 STK PUSH PAYLOAD 🔥", payload)
        response = requests.post(push_api, json=payload, headers=headers)
        print("🔥 STK PUSH RESPONSE 🔥", response.json())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("❌ ERROR SENDING STK PUSH ❌", str(e))
        return {"error": str(e)}

# --- Query STK Push Status (Optional) ---
def query_stk_push(checkout_request_id: str):
    headers = get_mpesa_access_token()
    payload = {
        "BusinessShortCode": short_code,
        "Password": generate_password(),
        "Timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
        "CheckoutRequestID": checkout_request_id
    }
    try:
        response = requests.post(stk_push_query_api, json=payload, headers=headers)
        print("STK QUERY PAYLOAD:", payload)
        print("STK QUERY RESPONSE:", response.json())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("❌ ERROR QUERYING STK PUSH ❌", str(e))
        return {"error": str(e)}
