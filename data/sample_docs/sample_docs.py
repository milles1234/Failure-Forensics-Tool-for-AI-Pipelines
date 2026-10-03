# data/sample_docs.py

SAMPLE_DOCUMENTS = {
    "missing_dates_contract": {
        "description": "Contract with missing execution dates and vague terms (Triggers Extraction & Confidence Failures)",
        "text": """
        MUTUAL NON-DISCLOSURE AGREEMENT
        
        This Agreement is entered into by and between Alpha Corp and the undersigned party.
        
        1. Confidential Information: Both parties agree to keep all technical discussions confidential.
        2. Term: The obligations of this Agreement shall commence upon execution and continue for a period of two years.
        
        IN WITNESS WHEREOF, the parties have executed this Agreement.
        
        Party A: Alpha Corp
        Signature: __________________  Date: [BLANK]
        
        Party B: Beta LLC
        Signature: __________________  Date: [UNSPECIFIED]
        """
    },
    
    "multi_currency_invoice": {
        "description": "Invoice mixing multiple currencies without conversion rates (Triggers Entity & Summarization Propagation Error)",
        "text": """
        INVOICE #INV-2026-889
        Issuer: Global Logistics Ltd.
        Billed To: Acme Enterprises
        
        Line Items:
        - Server Infrastructure Hosting: $1,200.00 USD
        - On-site Support (Tokyo Branch): ¥150,000 JPY
        - EU Compliance Audit: €850.00 EUR
        
        Subtotal: $1,200.00 USD + ¥150,000 JPY + €850.00 EUR
        Tax: 10%
        Total Amount Due: Please remit payment in specified local currencies within 30 days.
        """
    },
    
    "ambiguous_category": {
        "description": "Hybrid document blurs line between Invoice and Correspondence (Triggers Misclassification)",
        "text": """
        Hey Sarah,
        
        Thanks for catching up over coffee yesterday! As discussed, here is a breakdown of the design work we completed for your project last month:
        
        - Logo redesign: $500
        - Homepage wireframes: $1,200
        
        Can you transfer the $1,700 to my PayPal when you get a chance? Let me know if you want to schedule another call next week to talk about Phase 2 marketing assets.
        
        Best,
        Mark
        """
    },
    
    "noisy_context_loss": {
        "description": "Disorganized document with key details hidden in irrelevant text (Triggers Context Loss / Prompt Failure)",
        "text": """
        Meeting Notes - March 12
        Attendees: Dave, Elena, Sam
        
        We started by discussing the catering for next week's office party. Dave wants tacos, Elena suggested sushi.
        Anyway, regarding the Vendor Agreement termination clause for Q3: Section 4.2 states that notice must be served 90 days prior to renewal, involving a penalty fee of $5,000 if cancelled after April 1st.
        Sam mentioned his dog is sick so he's WFH on Thursday.
        Action item: Check if the liability cap is capped at $50,000 or $500,000—the draft copy on page 14 says both in different paragraphs.
        """
    }
}