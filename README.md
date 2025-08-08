Hunter.io minimal client

Usage example:

```python
from hunter_client import HunterClient

client = HunterClient(api_key="YOUR_API_KEY")

companies = client.discover(query="fintech in Germany", limit=2)
emails = client.domain_search(domain="example.com", limit=2)
guess = client.email_finder(domain="example.com", first_name="Jane", last_name="Doe")

print(companies)
print(emails)
print(guess)
```


