import httpx
import os

def test_resume_upload():
    url = "http://127.0.0.1:8000/api/parse-resume"
    pdf_path = "valid.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        return

    files = {'file': (pdf_path, open(pdf_path, 'rb'), 'application/pdf')}
    
    try:
        print(f"Attempting to upload {pdf_path} to {url}...")
        response = httpx.post(url, files=files, timeout=35.0)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Success! Response JSON:")
            print(response.json())
        else:
            print("Failed. Details:")
            print(response.text)
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    test_resume_upload()
