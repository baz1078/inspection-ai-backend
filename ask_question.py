import requests

BASE_URL = "http://localhost:5000"

# Use the Report ID from the upload
REPORT_ID = "52c211a6-def0-46d5-a4e5-529f49f56a24"  # Your ID from above

questions = [
    "Is the roof a big problem?",
    "How bad is the foundation issue?",
    "What's the main drain problem?",
]

def ask_question(report_id, question):
    print(f"\n{'='*60}")
    print(f"Q: {question}")
    print('='*60)
    
    response = requests.post(
        f"{BASE_URL}/api/ask/{report_id}",
        json={"question": question}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"A: {result['answer']}")
    else:
        print(f"ERROR: {response.status_code}")
        print(response.text)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Testing Q&A System")
    print("="*60)
    
    for question in questions:
        ask_question(REPORT_ID, question)
    
    print("\n" + "="*60)
    print("Done!")
    print("="*60)

