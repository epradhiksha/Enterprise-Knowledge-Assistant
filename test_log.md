# Test Log

## 1. PDF Grounded Query

Question: What are the standard working hours?

Answer: Standard working hours are 9:30 a.m. to 6:00 p.m., Monday through Friday, with a one‑hour lunch break.

Sources:

Employee_Handbook.pdf — Page 1


Question: What should a practical risk record describe?

Answer: A practical risk record should describe the asset or process, the risk scenario, the consequences, the current safeguards, likelihood and impact estimates, the owner, the treatment plan, and the review date.

Sources:

NIST_Cybersecurity_Framework_2_0_Enterprise_Guide_4_Pages.pdf — Page 2

---

## 2. Text-File Grounded Query

Question: What are the IT help desk hours?

Answer: The IT Help Desk is available Monday to Friday, 9:00 a.m. to 6:00 p.m.

Sources:

IT_Security_Policy.txt

---

## 3. Web-Source Grounded Query

Question: What should the maximum password length be?

Answer: The maximum password length should be set to at least 64 characters.

Sources:

https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

---

## 4. Multi-Source Query

Question: How long is the probation period?

Answer: The probation period is six months.

Sources:

HR_Policies.pdf — Page 1
Employee_Handbook.pdf — Page 1

---

## 5. Information-Not-Available Query

Question: What is the company's parental leave policy?

Answer: I could not find sufficient information in the indexed knowledge base to answer this question.

Sources: None

---

## 6. Low-Relevance Query

Question: What is the travel reimbursement limit?

Answer: I could not find sufficient information in the indexed knowledge base to answer this question.

Sources: None

---

## 7. Ambiguous Query

Question: What is the policy?

Answer: Which policy are you referring to – the TechNova Solutions Leave Policy 2026, the OWASP Authentication considerations, or the NIST Cybersecurity Framework guidance?

Sources: None

---

## 8. Multi-Turn Follow-Up Conversation

Turn 1 question: What is the company's leave policy?

Answer: The indexed sources disagree about two aspects of the leave policy:

Annual paid leave entitlement
Leave_Policy_2026.pdf — Page 1 states that eligible full‑time employees receive 20 days of annual paid leave per calendar year, prorated for partial years of service.
Employee_Handbook.pdf — Page 1 states that employees receive 18 days of annual paid leave per calendar year after completing probation, with leave credited monthly on a prorated basis.

Probationary leave entitlement
Leave_Policy_2026.pdf — Page 1 says that employees in probation accrue annual leave on a prorated basis from their joining date, and use of accrued leave during probation requires manager and HR approval.
Employee_Handbook.pdf — Page 1 notes that during probation, employees should discuss leave eligibility with HR and that the handbook does not define a separate probation leave entitlement.

Please confirm with Human Resources which version of the leave policy is currently in effect.

Sources:

Leave_Policy_2026.pdf — Page 1
Employee_Handbook.pdf — Page 1


Turn 2 question: What about during probation?

Answer: The indexed sources disagree about probationary leave entitlement.

Employee_Handbook.pdf — Page 1 states that during probation employees should discuss leave eligibility with HR and that the handbook does not define a separate probation leave entitlement.
Leave_Policy_2026.pdf — Page 1 states that employees in probation accrue annual leave on a prorated basis from their joining date, and use of accrued leave during probation requires manager and HR approval.
Please confirm with Human Resources which version is currently in effect.

Sources:

Employee_Handbook.pdf — Page 1
Leave_Policy_2026.pdf — Page 1


Turn 3 question: How long does it last?

Answer: The standard probation period is six months.

Sources:

HR_Policies.pdf — Page 1
Employee_Handbook.pdf — Page 1

---

## 9. Conflicting-Source Scenario

Question: How many days of annual leave do employees get?

Answer: The indexed sources disagree about the number of annual leave days employees receive.

Employee_Handbook.pdf — Page 1 states that employees receive 18 days of annual paid leave per calendar year after completing probation.
Leave_Policy_2026.pdf — Page 1 states that eligible full-time employees receive 20 days of annual paid leave per calendar year, prorated for partial years of service.
Please confirm with Human Resources which version of the policy is currently applicable.

Sources:

Employee_Handbook.pdf — Page 1
Leave_Policy_2026.pdf — Page 1
