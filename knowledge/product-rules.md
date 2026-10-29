# RelayPay Product Rules

**Status:** Source of truth for how RelayPay works
**Version:** 0.1
**Scope:** Personal RelayPay accounts and person-to-person payments

These are product facts. They do not describe how support staff or an LLM
should behave.

## Terms

- **Transfer** — a payment sent from one RelayPay customer to another.
- **Pending transfer** — a transfer that has not yet completed, failed, or been
  cancelled.
- **Completed transfer** — a transfer that has successfully reached the
  recipient.
- **Failed transfer** — a transfer that did not complete successfully and was
  not cancelled by the sender.
- **Payment request** — a request asking another customer to pay. Creating or
  receiving a request does not move money.
- **Available balance** — funds the customer can immediately send or withdraw.

## Transfers

### PRODUCT-01 — Pending transfers expire after 24 hours

A transfer can remain pending for at most 24 hours. If it has not completed
within that window, it automatically becomes failed. The transfer amount
returns to the sender's available balance.

### PRODUCT-02 — Only pending transfers can be cancelled

A sender may cancel a transfer only while it is pending. Cancellation is
immediate, and the transfer amount returns to the sender's available balance.

### PRODUCT-03 — Completed transfers are final

Once a transfer is completed, it cannot be cancelled, reversed, recalled, or
refunded through the normal transfer flow. If the recipient agrees to return
the money, they must send a new transfer.

### PRODUCT-04 — Failed transfers return funds automatically

When a transfer fails, the transfer amount returns automatically to the
sender's available balance.

## Payment requests

### PRODUCT-05 — Payment requests expire after 7 days

A payment request expires 7 calendar days after it is created. An expired
request cannot be paid; the requester must create a new one. A request never
moves money automatically and never reserves funds.

## Fees

### PRODUCT-06 — Currency conversion costs 1%

For an amount X, the conversion fee is 1% of X. The remaining 99% is converted
into the target currency. The fee and final amount are shown before the
customer confirms. Transfers between customers in the same currency have no
RelayPay fee.
