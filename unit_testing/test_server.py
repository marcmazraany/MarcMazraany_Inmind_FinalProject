from server import web_search_ddg_try_get_sync

def run():
    print("Query: site:python.org PEP 8")
    res = web_search_ddg_try_get_sync("site:python.org PEP 8", max_results=5)
    print("RESULT:", res)

if __name__ == "__main__":
    run()