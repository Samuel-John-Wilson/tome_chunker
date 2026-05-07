



In main.py, after ToC parsing:
python# Step 2: Parse Table of Contents
toc_mapping = {}

if use_toc:
    print(f"\n{'='*70}")
    print("[Step 2/5] Parsing Table of Contents...")
    print('='*70)
    
    toc_mapping = parse_table_of_contents(pages)
    
    if toc_mapping:
        # Find which pages contain the ToC
        toc_pages = set()
        for page in pages[:15]:  # ToC usually in first 15 pages
            if 'TABLE OF CONTENTS' in page['text'].upper():
                toc_pages.add(page['page_num'])
        
        if toc_pages:
            print(f"   Found ToC on pages: {sorted(toc_pages)}")
            print(f"   Removing ToC pages from processing...")
            
            # Filter out ToC pages
            pages = [p for p in pages if p['page_num'] not in toc_pages]
            print(f"   {len(pages)} pages remaining for chunking")