mint
====

Small python script to check the balance of mint.com accounts.

Example:

```python
from mint import Session, get_balance

session = Session("mint.user@email.com", "mypassword123")
print get_balance(session)
```
