# GitHub upload and application notes

## Run it first on your laptop

Extract the ZIP, open the `sahirfq` folder in PowerShell and follow the README's Windows commands. Run the tests. Open the local demo, complete the vague pump request, and inspect at least one excluded and one unknown-field supplier. This gives you a concrete demo you can explain in the interview.

The supported demo is local. Uploading code to GitHub does not automatically host the Python app. The form accepts a GitHub repository OR live demo link, so a public repository with a clear README is sufficient for the project-link field.

## Upload the source repository

Create a repository named **sahirfq** on GitHub. Suggested description:

> Evidence-first B2B sourcing: ML category routing, RFQ clarification, constrained supplier matching and grounded catalog Q&A.

Make it public if you want a recruiter to view it without an invitation. For the command-line route, create an empty repository without adding another README or license, then run from the project folder:

```powershell
git init
git add .
git commit -m "Build SahiRFQ sourcing prototype with evidence checks and evaluation"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sahirfq.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username. No repository has been created or pushed by this project package. The `.gitignore` excludes `.venv`, `.env` and generated Python cache files. Do not add an API key or private buyer documents. The package contains no placement email, application screenshot or JD PDF.

For GitHub's web upload route, upload the extracted project contents at the repository root, not the ZIP. Include the `.github` folder for CI. If GitHub asks to create an additional README, use the existing one from this package.

Suggested topics: `machine-learning`, `b2b`, `product-management`, `rag`, `information-retrieval`, `scikit-learn`.

## Form-ready project description

After uploading, replace the bracketed URL:

> SahiRFQ - an AI/ML prototype that turns incomplete English/Hinglish B2B enquiries into clear RFQs and evidence-backed supplier shortlists. It uses a trained logistic regression category router, word/character TF-IDF and LSA vector retrieval, clarification questions, and checks for specifications, MOQ, price units, budget scope and lead time. It includes cited catalog Q&A, optional OpenAI Structured Outputs RAG, quote completeness checks and a local web demo. Evaluated on 48 authored scenarios using fictional catalog data; the development regression suite passes all 48. GitHub: [paste your repository URL].

This text does not claim a live OpenAI run, real IndiaMART data or business uplift. If you enable and verify the provider yourself, you can say that the optional RAG path was tested live.

## Shorter version if the form has a limit

> SahiRFQ: AI/ML sourcing prototype for incomplete B2B enquiries. Trained category routing + hybrid vector retrieval + RFQ clarification + evidence-based supplier constraint checks. Includes cited catalog Q&A, optional OpenAI RAG, quote comparison and a local demo. 48 authored regression scenarios; fictional catalog data. GitHub: [URL].

## Resume bullet

Use after you have run and reviewed the implementation:

> Developed SahiRFQ with AI-assisted implementation: an ML-based B2B sourcing prototype with RFQ clarification, hybrid retrieval, supplier constraint checks and cited catalog Q&A; validated against 48 authored regression scenarios.

## Placement instructions in your uploaded email

The updated placement message dated 13 October states a deadline of **11:59 pm IST, 14 October 2026** and asks you to complete both the registration form and a second Google Form.

- Position: select **Other**, then enter **Management Intern - Assistant Product Manager**.
- PG college: select **Other**, then enter **Vinod Gupta School of Management, IIT Kharagpur**.
- PG percentage: the placement message explicitly instructs **100** for this registration. This is the form instruction, not a claim about your earned MBA marks.
- PG graduation year: **2028**.
- Resume filename: the message specifies **Full Name_VGSoM**; for you, **Mayank Nigam_VGSoM.pdf**.
- The original message says students already placed are not eligible to apply.

These details come from your supplied email, not a general recommendation about filling recruitment forms. Check both required forms are submitted before the stated deadline. The files do not establish whether the deadline has since changed.
