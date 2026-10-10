import urllib.request
import json
import uuid

boundary = uuid.uuid4().hex
with open('sample_contract.txt', 'r', encoding='utf-8') as f:
    contract_text = f.read()

body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="sample_contract.txt"\r\n'
    f'Content-Type: text/plain\r\n\r\n'
    f'{contract_text}\r\n'
    f'--{boundary}--\r\n'
).encode('utf-8')

req = urllib.request.Request(
    'http://localhost:8000/pipeline/process',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)

try:
    with urllib.request.urlopen(req, timeout=120) as response:
        result = json.loads(response.read().decode('utf-8'))
        print("PIPELINE TEST SUCCESSFUL:")
        print(f"Total clauses: {result['total_clauses']}")
        print(f"High risk count: {result['high_risk_count']}")
        print(f"Faithfulness flags: {result['faithfulness_flags']}")
        for idx, clause in enumerate(result['clauses'], 1):
            dev_str = f"{clause['deviation_score']:.2f}" if clause.get('deviation_score') is not None else "Uncomputed"
            print(f"\n[{idx}] Type: {clause['clause_type']} | Risk: {clause['risk_score']:.2f} | Deviation: {dev_str}")
            print(f"    Summary: {clause['summary'].get('meaning')}")
            print(f"    Obligor: {clause['summary'].get('obligor')}")
            print(f"    Rationale: {clause.get('risk_rationale')}")
except Exception as e:
    print("Error calling pipeline:", e)
