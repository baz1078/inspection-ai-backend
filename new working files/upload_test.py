import requests
from pathlib import Path

BASE_URL = "http://localhost:5000"

# CHANGE THIS to your PDF file path
PDF_PATH = "C:\\Users\\Baz\\Downloads\\Inspection Report - 340 Jessie Street.pdf"  # Change this!

def upload_pdf():
    print("\nUploading PDF...")
    print(f"File: {PDF_PATH}")
    
    if not Path(PDF_PATH).exists():
        print(f"ERROR: File not found at {PDF_PATH}")
        print("Edit the PDF_PATH in the script to the correct location")
        return
    
    try:
        with open(PDF_PATH, 'rb') as f:
            files = {'file': f}
            data = {
                'address': 'Test Property',
                'inspector_name': 'Baz',
                'report_type': 'home_inspection'
            }
            
            response = requests.post(
                f"{BASE_URL}/api/upload",
                files=files,
                data=data
            )
        
        if response.status_code == 201:
            result = response.json()
            print("\n✓ SUCCESS!")
            print(f"\nReport ID: {result['report_id']}")
            print(f"Share Token: {result['share_token']}")
            print(f"\nAI Summary:")
            print(result['summary'])
            
            # Save for next step
            with open('last_report_id.txt', 'w') as f:
                f.write(result['report_id'])
            print(f"\n[Report ID saved for next test]")
        else:
            print(f"ERROR: Upload failed - {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == '__main__':
    upload_pdf()