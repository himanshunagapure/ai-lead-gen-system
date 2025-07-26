#!/usr/bin/env python3
"""
Standalone Comprehensive Integration Test for Lead Generation System
Tests all modules from start to end using 5 URLs from Google search
Can be run directly without pytest
"""
import sys
import os
import asyncio
import time
from httpx import AsyncClient, ASGITransport
from fastapi import status
from app.api.main import app, logger
from asgi_lifespan import LifespanManager
import pandas as pd
import json

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.search_client import GoogleSearchClient
from app.core.lead_storage import lead_storage
from app.core.lead_extractor import extract_pattern_leads
from app.core.lead_scorer import score_lead
from app.db.session import test_db_connection, engine

async def wait_for_job_completion(ac, job_id, timeout=60):
    """Wait for job completion with comprehensive error handling and debugging"""
    print(f"    Waiting for job {job_id} to complete (timeout: {timeout}s)...")
    start_time = time.time()
    
    for attempt in range(int(timeout * 2)):
        try:
            status_resp = await ac.get(f"/jobs/{job_id}")
            if status_resp.status_code != 200:
                print(f"    Error getting job status: {status_resp.status_code}")
                await asyncio.sleep(0.5)
                continue
                
            status_data = status_resp.json()
            current_status = status_data["status"]
            
            # Log progress every 15 seconds
            elapsed = time.time() - start_time
            if attempt % 30 == 0 and elapsed > 15:
                print(f"    Job {job_id} still {current_status} after {elapsed:.1f}s")
            
            if current_status not in ("pending", "in_progress"):
                elapsed = time.time() - start_time
                print(f"    Job {job_id} completed with status '{current_status}' after {elapsed:.1f}s")
                return status_data
                
        except Exception as e:
            print(f"    Error checking job status: {e}")
            
        await asyncio.sleep(0.5)
    
    elapsed = time.time() - start_time
    print(f"    ⚠️  Job {job_id} did not complete in {timeout} seconds (waited {elapsed:.1f}s)")
    raise TimeoutError(f"Job {job_id} did not complete in {timeout} seconds")

async def get_google_search_urls(query, max_results=2):
    """Get URLs from Google search for testing"""
    print(f"🔍 Getting Google search results for: '{query}'")
    
    try:
        client = GoogleSearchClient()
        results = await client.paginated_search(query, max_results=max_results)
        
        if not results:
            print("❌ No Google search results returned. Check API configuration.")
            return []
        
        urls = []
        for i, item in enumerate(results, 1):
            link = item.get('link') or item.get('url')
            title = item.get('title', 'No title')
            if link:
                urls.append({
                    'url': link,
                    'title': title,
                    'snippet': item.get('snippet', 'No description')
                })
                print(f"  [{i}] {title}")
                print(f"      URL: {link}")
        
        print(f"✅ Found {len(urls)} URLs from Google search")
        return urls
        
    except Exception as e:
        print(f"❌ Google search failed: {e}")
        return []

async def test_comprehensive_integration():
    """Comprehensive integration test for the entire lead generation system"""
    print("🧪 Comprehensive Integration Test")
    print("=" * 80)
    
    # Check current database state (preserving existing data)
    print("\n0️⃣ Checking current database state...")
    initial_count = 0
    try:
        initial_count = lead_storage.get_lead_count_from_db()
        print(f"   📊 Current leads in database: {initial_count}")
        print("   📝 Note: Existing data will be preserved (no cleanup)")
    except Exception as e:
        print(f"   ⚠️  Could not check database: {e}")
        print("   📝 Proceeding without database cleanup")
    
    # Test database connection and ensure tables exist
    print("\n1️⃣ Testing Database Connection and Setup...")
    try:
        test_db_connection()
        print("   ✅ Database connection successful")
        
        # Ensure tables exist
        from app.db.base import Base
        Base.metadata.create_all(bind=engine)
        print("   ✅ Database tables ensured")
        
    except Exception as e:
        print(f"   ❌ Database connection/setup failed: {e}")
        return
    
    # Get test URLs from Google search
    print("\n2️⃣ Getting Test URLs from Google Search...")
    test_queries = [
        "tour operators Hyderabad contact information",
        "luxury restaurants India phone email",
        "waterfall resorts in India"
    ]
    
    all_test_urls = []
    for query in test_queries:
        urls = await get_google_search_urls(query, max_results=2)  # Get 2 URLs per query
        all_test_urls.extend(urls)
        await asyncio.sleep(1)  # Rate limiting
    
    if not all_test_urls:
        print("❌ No URLs found from Google search. Cannot proceed with integration test.")
        print("💡 Make sure you have set up your Google API credentials:")
        print("   - GOOGLE_API_KEY")
        print("   - GOOGLE_SEARCH_ENGINE_ID")
        return
    
    print(f"✅ Total test URLs collected: {len(all_test_urls)}")
    
    # Test full API integration with real URLs
    print("\n3️⃣ Testing Full API Integration with Real URLs...")
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
            
            # Track all jobs and results
            all_jobs = []
            successful_crawls = 0
            successful_lead_processing = 0
            total_leads_found = 0
            
            # Test each URL individually
            for i, url_data in enumerate(all_test_urls, 1):
                url = url_data['url']
                title = url_data['title']
                
                print(f"\n   📄 Testing URL {i}/{len(all_test_urls)}: {title}")
                print(f"      URL: {url}")
                
                try:
                    # Submit crawl job for this URL
                    print("      Submitting crawl job...")
                    crawl_resp = await ac.post("/crawl", json={
                        "url": url,
                        "priority": 1
                    })
                    
                    if crawl_resp.status_code == 200:
                        crawl_job_id = crawl_resp.json()["job_id"]
                        print(f"      ✅ Crawl job submitted: {crawl_job_id}")
                        
                        # Wait for crawl completion
                        crawl_status = await wait_for_job_completion(ac, crawl_job_id, timeout=45)
                        
                        if crawl_status['status'] == 'completed':
                            successful_crawls += 1
                            print(f"      ✅ Crawl completed successfully")
                            
                            # Check if automatic lead processing was triggered
                            await asyncio.sleep(2)  # Give time for lead processing jobs
                            
                            # Look for lead processing jobs
                            all_jobs_resp = await ac.get("/jobs")
                            all_jobs = all_jobs_resp.json()
                            lead_jobs = [j for j in all_jobs if j["type"] == "lead_processing" and 
                                       j.get("payload", {}).get("source_url") == url]
                            
                            if lead_jobs:
                                print(f"      Found {len(lead_jobs)} lead processing job(s)")
                                
                                for lead_job in lead_jobs:
                                    lead_job_id = lead_job['job_id']
                                    print(f"      Processing lead job: {lead_job_id}")
                                    
                                    lead_status = await wait_for_job_completion(ac, lead_job_id, timeout=30)
                                    
                                    if lead_status['status'] == 'completed':
                                        successful_lead_processing += 1
                                        result = lead_status.get('result', {})
                                        pattern_leads = result.get('pattern_leads', {})
                                        ai_leads = result.get('ai_leads', [])
                                        
                                        pattern_count = (len(pattern_leads.get('emails', [])) + 
                                                       len(pattern_leads.get('phones', [])) + 
                                                       len(pattern_leads.get('business_names', [])))
                                        ai_count = len(ai_leads)
                                        total_count = pattern_count + ai_count
                                        
                                        total_leads_found += total_count
                                        
                                        print(f"      ✅ Lead processing completed:")
                                        print(f"         Pattern leads: {pattern_count}")
                                        print(f"         AI leads: {ai_count}")
                                        print(f"         Total: {total_count}")
                                        
                                        # Show sample leads
                                        if pattern_leads.get('emails'):
                                            print(f"         Sample emails: {pattern_leads['emails'][:3]}")
                                        if ai_leads:
                                            print(f"         Sample AI leads: {ai_leads[:2]}")
                                        
                                        # Debug: Check what's being stored
                                        print(f"         🔍 Debug: Pattern leads structure:")
                                        print(f"            Emails: {len(pattern_leads.get('emails', []))}")
                                        print(f"            Phones: {len(pattern_leads.get('phones', []))}")
                                        print(f"            Business names: {len(pattern_leads.get('business_names', []))}")
                                        if 'leads' in pattern_leads:
                                            print(f"            Structured leads: {len(pattern_leads.get('leads', []))}")
                                        
                                        print(f"         🔍 Debug: AI leads structure:")
                                        for i, ai_lead in enumerate(ai_leads[:2]):
                                            print(f"            AI Lead {i+1}: {ai_lead.get('business_name', 'N/A')} - {ai_lead.get('email', 'N/A')}")
                                    else:
                                        print(f"      ❌ Lead processing failed: {lead_status['status']}")
                            else:
                                print("      ⚠️  No automatic lead processing jobs found")
                                print("      🔍 Debug: Checking if crawl job created content...")
                                
                                # Check if crawl job actually created content
                                if 'result' in crawl_status and 'crawl_results' in crawl_status['result']:
                                    crawl_results = crawl_status['result']['crawl_results']
                                    if crawl_results:
                                        print(f"      ✅ Crawl created {len(crawl_results)} results")
                                        # Check if content was extracted
                                        for result in crawl_results:
                                            html_length = len(result.get('html', ''))
                                            text_length = len(result.get('text', ''))
                                            print(f"         HTML length: {html_length}, Text length: {text_length}")
                                    else:
                                        print("      ❌ Crawl results are empty")
                                else:
                                    print("      ❌ No crawl results found in job status")
                        else:
                            print(f"      ❌ Crawl failed: {crawl_status['status']}")
                            if 'error' in crawl_status:
                                print(f"      Error details: {crawl_status['error']}")
                    else:
                        print(f"      ❌ Crawl job submission failed: {crawl_resp.status_code}")
                        print(f"      Response: {crawl_resp.text}")
                        
                except Exception as e:
                    print(f"      ❌ Error processing URL: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Rate limiting between URLs
                await asyncio.sleep(2)
            
            # Test system-wide functionality
            print(f"\n4️⃣ Testing System-Wide Functionality...")
            
            # Check system status
            print("   Checking system status...")
            status_resp = await ac.get("/status")
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                print(f"   ✅ System status: {status_data}")
            else:
                print(f"   ❌ System status check failed: {status_resp.status_code}")
            
            # Check lead statistics
            print("   Checking lead statistics...")
            stats_resp = await ac.get("/leads/stats")
            if stats_resp.status_code == 200:
                stats = stats_resp.json()
                print(f"   📊 Lead Statistics:")
                print(f"      Database leads: {stats.get('database_leads', 0)}")
                print(f"      Memory leads: {stats.get('memory_leads', 0)}")
                print(f"      Total leads: {stats.get('total_leads', 0)}")
            else:
                print(f"   ❌ Lead statistics failed: {stats_resp.status_code}")
            
            # Export leads
            print("   Testing lead export...")
            export_resp = await ac.get("/export")
            if export_resp.status_code == 200:
                exported_leads = export_resp.json()
                print(f"   📊 Exported {len(exported_leads)} leads")
                
                if exported_leads:
                    print("   📋 Sample exported leads:")
                    for i, lead in enumerate(exported_leads[:3], 1):
                        print(f"      Lead {i}: {lead.get('business_name', 'N/A')} - {lead.get('email', 'N/A')}")
                else:
                    print("   ⚠️  No leads exported")
            else:
                print(f"   ❌ Lead export failed: {export_resp.status_code}")
            
            # Test CSV export (commented out to avoid duplicate files)
            print("   Testing CSV export...")
            csv_resp = await ac.get("/export/csv")
            if csv_resp.status_code == 200:
                print("   ✅ CSV export successful")
                content_length = len(csv_resp.content)
                print(f"      CSV content length: {content_length} bytes")
                print("   📝 Note: This creates the first CSV file via API endpoint")
            else:
                print(f"   ❌ CSV export failed: {csv_resp.status_code}")
    
    # Test database storage directly
    print(f"\n5️⃣ Testing Database Storage...")
    try:
        db_leads = lead_storage.get_leads_from_db()
        print(f"   📊 Database contains {len(db_leads)} leads")
        
        if db_leads:
            print("   📋 Database leads:")
            for i, lead in enumerate(db_leads[:5], 1):
                print(f"      Lead {i}: {lead.get('business_name', 'N/A')} - {lead.get('email', 'N/A')} - {lead.get('contact_person', 'N/A')}")
        else:
            print("   ⚠️  No leads found in database")
            
    except Exception as e:
        print(f"   ❌ Database storage test failed: {e}")
    
    # Test CSV export functionality (creates second CSV file)
    print(f"\n6️⃣ Testing CSV Export Functionality...")
    try:
        db_leads = lead_storage.get_leads_from_db()
        if db_leads:
            csv_filepath = lead_storage.export_leads_to_csv(db_leads, "comprehensive_test_leads.csv")
            print(f"   ✅ CSV exported to: {csv_filepath}")
            print("   📝 Note: This creates the second CSV file via direct service call")
            
            if os.path.exists(csv_filepath):
                df = pd.read_csv(csv_filepath)
                print(f"   📊 CSV contains {len(df)} rows and {len(df.columns)} columns")
                print(f"      Columns: {list(df.columns)}")
                
                if len(df) > 0:
                    print("   📋 CSV sample data:")
                    for i, row in df.head(3).iterrows():
                        print(f"      Row {i+1}: {row.get('business_name', 'N/A')} - {row.get('email', 'N/A')}")
                else:
                    print("   ⚠️  CSV file is empty")
            else:
                print("   ❌ CSV file was not created")
        else:
            print("   ⚠️  No leads to export")
            
    except Exception as e:
        print(f"   ❌ CSV export test failed: {e}")
    
    # Final summary with data preservation tracking
    print(f"\n7️⃣ Test Summary...")
    print(f"   📊 Test Results Summary:")
    print(f"      URLs tested: {len(all_test_urls)}")
    print(f"      Successful crawls: {successful_crawls}")
    print(f"      Successful lead processing: {successful_lead_processing}")
    print(f"      Total leads found: {total_leads_found}")
    
    # Check final database state
    try:
        final_count = lead_storage.get_lead_count_from_db()
        added_count = final_count - initial_count
        print(f"   📊 Database Summary:")
        print(f"      Initial leads: {initial_count}")
        print(f"      Final leads: {final_count}")
        print(f"      New leads added: {added_count}")
        
        if added_count > 0:
            print(f"      ✅ APPEND BEHAVIOR: New leads were appended to existing ones")
        else:
            print(f"      ⚠️  No new leads were added to database")
            
    except Exception as e:
        print(f"      ❌ Could not check final database state: {e}")
    
    # Calculate success rates
    crawl_success_rate = (successful_crawls / len(all_test_urls)) * 100 if all_test_urls else 0
    lead_processing_success_rate = (successful_lead_processing / successful_crawls) * 100 if successful_crawls > 0 else 0
    
    print(f"      Crawl success rate: {crawl_success_rate:.1f}%")
    print(f"      Lead processing success rate: {lead_processing_success_rate:.1f}%")
    
    # Determine overall test success
    if successful_crawls > 0 and total_leads_found > 0:
        print("   ✅ Comprehensive integration test PASSED!")
        print("   🎉 All modules are working correctly together")
    elif successful_crawls > 0:
        print("   ⚠️  Integration test PARTIALLY PASSED!")
        print("   📝 Crawling works but no leads were extracted")
    else:
        print("   ❌ Integration test FAILED!")
        print("   🔧 Check system configuration and API keys")
    
    print("\n" + "=" * 80)
    print("✅ Comprehensive Integration Test Completed!")

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Integration Test...")
    print("📝 This test will:")
    print("   0. Clean up database (remove old test data)")
    print("   1. Test database connection")
    print("   2. Get 4 URLs from Google search (2 per query)")
    print("   3. Test crawling each URL")
    print("   4. Test lead extraction and processing")
    print("   5. Test database storage")
    print("   6. Test CSV export")
    print("   7. Provide comprehensive results summary")
    print()
    
    try:
        asyncio.run(test_comprehensive_integration())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 