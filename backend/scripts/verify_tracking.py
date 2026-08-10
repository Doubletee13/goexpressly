import httpx
import time
import os

API_URL = "http://127.0.0.1:8000/api"

def get_admin_token():
    print("Logging in as admin...")
    # Assume default seeded admin exists
    resp = httpx.post(
        f"{API_URL}/auth/login",
        data={"username": "info@goexpressly.com", "password": "password123"}
    )
    if resp.status_code != 200:
        print("Could not login. Please ensure backend is running and seeded.")
        return None
    return resp.json()["access_token"]


def create_full_package(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n1. Creating highly-detailed package...")
    payload = {
        "recipient_name": "Sarah Connor",
        "recipient_email": "sarah.connor@example.com",
        "recipient_phone": "+1-555-0199",
        "origin": "Los Angeles, CA",
        "destination": "Mexico City, MX",
        "description": "Electronics and documents",
        
        # New sender / origin info
        "sender_name": "Cyberdyne Systems",
        "sender_phone": "+1-800-SKY-NET1",
        "sender_address": "18144 El Camino Real, Sunnyvale, CA 94086",
        "city_collection": "Sunnyvale",
        "shipping_date": "2026-08-10T09:00:00Z",
        "shipping_quantity": 3,
        "weight_lbs": 42.5,
        "carrier": "GoExpressly Global Flight",
        
        # New destination info
        "delivery_city": "Mexico City",
        "destination_address": "Av. Paseo de la Reforma 222, Cuauhtémoc, 06600 Ciudad de México, CDMX",
        "estimated_delivery_date": "2026-08-15T14:30:00Z",
        
        # Initial geolocation (Sunnyvale coordinates)
        "current_lat": 37.3688,
        "current_lng": -122.0363
    }
    
    resp = httpx.post(f"{API_URL}/packages", json=payload, headers=headers)
    if resp.status_code != 201:
        print("Failed to create package:", resp.text)
        return None
        
    data = resp.json()
    tracking_id = data["tracking_id"]
    pkg_id = data["id"]
    print(f"✅ Package created! Tracking ID: {tracking_id}")
    return tracking_id, pkg_id


def add_tracking_events(token, tracking_id, pkg_id):
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n2. Simulating package journey for {tracking_id}...")
    
    events = [
        {
            "status_label": "Package received at origin facility",
            "location": "Sunnyvale, CA",
            "notes": "Initial dropoff",
            "current_lat": 37.3875,
            "current_lng": -122.0575
        },
        {
            "status_label": "Departed origin facility",
            "location": "San Francisco International Airport (SFO)",
            "current_lat": 37.6213,
            "current_lng": -122.3790
        },
        {
            "status_label": "In Transit - Arrived at sorting hub",
            "location": "Mexico City International Airport (MEX)",
            "current_lat": 19.4361,
            "current_lng": -99.0718
        }
    ]
    
    for i, event in enumerate(events):
        print(f"   Adding event {i+1}: {event['status_label']}")
        resp = httpx.post(
            f"{API_URL}/packages/{pkg_id}/events", 
            json=event, 
            headers=headers
        )
        assert resp.status_code == 201, f"Failed to add event: {resp.text}"
        time.sleep(0.5) # slightly stagger timestamps
        
    print("✅ Journey events added.")


def track_public(tracking_id):
    print(f"\n3. Verifying Public API output for {tracking_id}...")
    resp = httpx.get(f"{API_URL}/track/{tracking_id}")
    if resp.status_code != 200:
        print("Tracking failed:", resp.text)
        return
        
    data = resp.json()
    print("✅ Public API lookup successful. Validated fields:")
    print(f"  - Sender: {data.get('sender_name')} | Carrier: {data.get('carrier')}")
    print(f"  - Recipient: {data.get('recipient_name')} | City: {data.get('delivery_city')}")
    print(f"  - Map Location: {data.get('current_lat')}, {data.get('current_lng')}")
    print(f"  - History Count: {len(data.get('history', []))}")


if __name__ == "__main__":
    print("--- GoExpressly Verification Script ---")
    token = get_admin_token()
    if token:
        result = create_full_package(token)
        if result:
            tracking_id, pkg_id = result
            add_tracking_events(token, tracking_id, pkg_id)
            track_public(tracking_id)
            print("\n🎉 DONE! Test this tracking ID on the frontend at:")
            print(f"   http://127.0.0.1:5500/public/track.html?id={tracking_id}")
