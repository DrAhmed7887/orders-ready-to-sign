# The problem, in plain words

## Meet Amparo
Amparo is 69. She has type 2 diabetes and high blood pressure, and she sees her family doctor every few months.
Her blood test says her kidneys filter well (eGFR 68), so her results are called "acceptable".

Ten months ago a **urine test** found albumin, a protein that should not be there (85 mg/g; normal is under 30).
That is often the first sign that diabetes and high blood pressure are damaging the kidneys.
In September a second result, 110 mg/g, came in a report from her private insurer and was typed into a note, where no filter looks.
Her record has no kidney diagnosis. She takes metformin for her sugar, but not the blood-pressure medicine that also protects the kidneys.

Nothing hurts. Nothing looks wrong. **The warning sign is hiding behind a normal blood test.**

*(Amparo is made up: she is patient 251 in our synthetic demo. The numbers below are real.)*

## How many people are like Amparo
From the US national health survey (NHANES, CDC), which tests a nationally representative sample of adults:

| | What we found | Source |
|---|---|---|
| **1 in 7** | adults with diabetes or high blood pressure have albumin in their urine **while their blood test looks normal** (143 per 1,000; 95 % CI 128–159) | NHANES 2021–2023, `eval/results/nhanes.md` |
| **About 10.6 million** | US adults in this situation (an undercount: a third of people had no lab result) | NHANES 2021–2023, `eval/results/nhanes_people.md` |
| **19 in 20** | of them have **never been told** they have a kidney problem (953 per 1,000; 904–977) | NHANES 2021–2023, `eval/results/nhanes_people.md` |
| **1 in 5** | of those who also have diabetes *and* high blood pressure **take no ACE inhibitor or ARB**, the medicine guidelines recommend for this (some may have a reason not to; 218 per 1,000; 151–304) | NHANES 2017–2020, `eval/results/nhanes_people.md` |

## Why it matters
- Albumin in the urine is not a lab curiosity. In 105,872 people from 14 population studies, a urine albumin-to-creatinine ratio of 10 mg/g or more predicted a higher risk of death independently of the kidney blood test ([Matsushita et al., Lancet 2010](https://doi.org/10.1016/S0140-6736(10)60674-5)).
- It is not only a US problem. In Spanish primary care, 54 % of kidney disease in 5,009 adults with type 2 diabetes was undiagnosed, "mainly in patients with isolated eGFR or uACR abnormalities" ([DIAMOND2, Prim Care Diabetes 2026](https://doi.org/10.1016/j.pcd.2026.02.007)).
- There is a clear next step. The international kidney guideline says: "We recommend that treatment with an ACEi or an ARB be initiated in patients with diabetes, hypertension, and albuminuria" ([KDIGO 2022, Recommendation 1.2.1](https://doi.org/10.1016/j.kint.2022.06.008)).
- But one urine test is not a diagnosis. In the CDC's own data, **about half** of high results were high again on a second sample 10 days later (52 %; 44–61 %). So the right first step is simple: **repeat the urine test**.

## Why it gets missed
The blood test is the number most people read as "the kidney result", and it looks fine.
The urine result sits elsewhere in the record, sometimes only in a note or a letter, and goes out of date quietly.
No one has time to check every chart, every morning. That is the whole problem: **attention, not knowledge.**

## What we built
Three steps. The computer does the checking; the doctor makes the decision.

1. **Every morning, it reads the doctor's list** of patients with diabetes or high blood pressure, with rules taken from kidney guidelines (KDIGO, Valencian primary-care protocol) and signed by the project's physician. A small open AI model also reads the notes for results typed there; the code checks every sentence it points to, and the rules decide.
2. **It prepares the next step** for each person it finds: the urine test order, one line for the notes, and a date to review the result. It says *why*, with the number and the date.
3. **The doctor signs with one click, or says no and why.** Nothing happens without the doctor.

It also stays quiet when it should: if the test is already ordered, or was repeated recently, the person is not listed again.

## What it changes
Run on the same national data, a filter that only looks at the blood test finds **48 %** of the people with a kidney warning sign at that visit.
The other **52 %** have a first result like Amparo's: every one of them gets a prepared urine-test order for the doctor to sign.
About half of those repeats will stay high on a second sample, and that is when the conversation, the diagnosis and the kidney-protecting medicine can start.

## Who could be harmed
- **Extra tests:** about half of the repeat orders will come back normal: a second urine sample, some worry, a small cost.
- **False reassurance:** someone not on the list is not "cleared"; the tool only sees what is in the record.
- **Wrong setting:** the numbers are from the US. The tool was designed for Spanish primary care, where we have no public data to test it.
Every order still needs the doctor's signature.
